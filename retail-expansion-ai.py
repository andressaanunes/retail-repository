import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from supabase import create_client, Client
import google.generativeai as genai
import datetime
import re
import os
import random

from fallback import STORE_IMAGES_FALLBACK as _STORE_IMAGES_FALLBACK

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Retail Insights",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONFIGURAÇÃO SUPABASE ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- SISTEMA DE ESTADO INICIAL ---
if 'lang' not in st.session_state: st.session_state.lang = 'PT' 
if 'theme' not in st.session_state: st.session_state.theme = 'Light' 
if 'ai_analysis' not in st.session_state: st.session_state.ai_analysis = None
if 'expansion_coords' not in st.session_state: st.session_state.expansion_coords = []
if 'suggested_format' not in st.session_state: st.session_state.suggested_format = "core"
if 'selected_image' not in st.session_state: st.session_state.selected_image = None
if 'show_survey' not in st.session_state: st.session_state.show_survey = False

@st.cache_data(show_spinner=False)
def baixar_imagem_base64(url: str) -> str | None:
    """Baixa a imagem no servidor e converte para base64, evitando bloqueios do cliente."""
    try:
        import requests, base64, re
        
        # Se for um link de compartilhamento do Gemini, primeiro extraímos a imagem real dele
        if "gemini.google.com/share" in url:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                match = re.search(r'(https://lh3\.googleusercontent\.com/[A-Za-z0-9\-_/]+)', r.text)
                if match:
                    url = match.group(1)
                else:
                    return None
            else:
                return None
                
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return base64.b64encode(r.content).decode('utf-8')
    except Exception:
        pass
    return None
@st.cache_data(ttl=3600, show_spinner=False)
def carregar_imagens_supabase() -> dict | None:
    """Busca a tabela public.store_images no Supabase e monta o dict {categoria: [urls]}.
    Retorna None em caso de falha para que o chamador use o fallback hardcoded."""
    try:
        data = []
        limit = 1000
        offset = 0
        while True:
            res = (
                supabase.table("store_images")
                .select("imagem,categoria")
                .range(offset, offset + limit - 1)
                .execute()
            )
            if not res.data:
                break
            data.extend(res.data)
            if len(res.data) < limit:
                break
            offset += limit

        if not data:
            return None

        agrupado: dict[str, list[str]] = {}
        for row in data:
            cat = row.get("categoria")
            url_img = row.get("imagem")
            if cat and url_img:
                agrupado.setdefault(cat, []).append(url_img)

        if not agrupado:
            return None

        # Garantir que todas as categorias do fallback existem no resultado
        for cat in _STORE_IMAGES_FALLBACK:
            agrupado.setdefault(cat, list(_STORE_IMAGES_FALLBACK[cat]))

        return agrupado
    except Exception:
        return None


STORE_IMAGES = carregar_imagens_supabase() or _STORE_IMAGES_FALLBACK

@st.cache_data(ttl=3600, show_spinner=False)
def carregar_dados_supabase() -> pd.DataFrame | None:
    """Busca os dados de lojas no Supabase de forma paginada para evitar o limite de 1000 registros."""
    try:
        data = []
        limit = 1000
        offset = 0
        while True:
            res = supabase.table("lojas").select("*").range(offset, offset + limit - 1).execute()
            if not res.data:
                break
            data.extend(res.data)
            if len(res.data) < limit:
                break
            offset += limit
        if data:
            return pd.DataFrame(data)
    except Exception:
        pass
    return None

# --- FUNÇÃO DE CACHE DA IA ---
@st.cache_data(show_spinner=False)
def obter_analise_ia(api_key, cidade, num_lojas, densidade, renda, publico, fluxo):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.1-flash-lite')
    prompt = f"Consultor estratégico: analise expansão na cidade de {cidade}. Lojas atuais: {num_lojas}. Cenário de geolocalização: Densidade {densidade}, Renda {renda}, Público {publico}, Fluxo {fluxo}. ATENÇÃO: Baseie sua análise ESTRITAMENTE na cidade de {cidade}. Não mencione São Paulo ou Rio de Janeiro a menos que seja a cidade solicitada. Identifique 2 áreas reais para expansão em {cidade}. Sugira o formato ideal escolhendo estritamente entre: drive-thru, flagship, quiosque ou core. Finalize obrigatoriamente no formato exato: FORMATO: [formato_escolhido] e COORDENADAS: [LAT, LON, NOME]; [LAT, LON, NOME]"
    response = model.generate_content(prompt)
    return response.text

def change_lang():
    mapping = {"Português": 'PT', "English": 'EN'}
    st.session_state.lang = mapping.get(st.session_state.lang_selector, 'PT')

t_dict = {
    'PT': {
        'title': "☕ Retail Insights", 'subtitle': "Simulador de Expansão - Análise de Vazios Comerciais via IA Geográfica",
        'config': "Configurações de Dados", 'upload': "Upload do CSV", 'pais': "País", 'estado': "Estado", 'cidade': "Cidade", 'todas': "Todas",
        'simulador_h': "Simulador de Cenários", 'densidade': "Densidade Populacional", 'renda': "Renda Superior", 'renda_sup': "Superior a 30%", 'renda_nac': "Média Nacional",
        'jovem': "Público Jovem", 'fluxo': "Fluxo de Pedestres", 'resumo': "Resumo do Cenário Configurado",
        'mapa_h': "Mapeamento de Unidades Atuais e Sugestões", 'ia_h': "IA Strategic Insights", 'botao_ia': "Gerar Análise de Expansão",
        'aviso_csv': "Carregue o CSV para ativar o simulador.", 'tema': "Modo de Interface",
        'likert_opts': ["Péssimo", "Ruim", "Médio", "Bom", "Excelente"]
    },
    'EN': {
        'title': "☕ Retail Insights", 'subtitle': "Expansion Simulator - Geographic AI",
        'config': "Data Settings", 'upload': "Upload CSV", 'pais': "Country", 'estado': "State", 'cidade': "City", 'todas': "All",
        'simulador_h': "Scenario Simulator", 'densidade': "Pop. Density", 'renda': "High Income", 'renda_sup': "Above 30%", 'renda_nac': "National Average",
        'jovem': "Young Audience", 'fluxo': "Pedestrian Flow", 'resumo': "Scenario Summary",
        'mapa_h': "Current Mapping and Suggestions", 'ia_h': "AI Strategic Insights", 'botao_ia': "Generate Analysis", 'tema': "Interface Mode",
        'likert_opts': ["Worst", "Poor", "Average", "Good", "Excellent"]
    }
}
t = t_dict.get(st.session_state.lang, t_dict['PT'])

# --- CORES E CSS ---
if st.session_state.theme == 'Dark':
    bg_app, bg_sidebar, bg_card, bg_widget = "#050505", "#0a0a0a", "#0d1310", "#111b17"
    border_card, text_main, text_sub = "#142b20", "#ffffff", "#888888"
    accent, bg_summary = "#00ff88", "rgba(0, 255, 136, 0.08)"
    map_tile, btn_text = "cartodbdark_matter", "#ffffff"
else:
    bg_app, bg_sidebar, bg_card, bg_widget = "#f8f9fa", "#ffffff", "#ffffff", "#f0f2f6"
    border_card, text_main, text_sub = "#dee2e6", "#1e3d33", "#495057"
    accent, bg_summary = "#00704A", "rgba(0, 112, 74, 0.05)"
    map_tile, btn_text = "cartodbpositron", "#ffffff"

# --- CSS PERSONALIZADO (VERSÃO FINAL COM LETRAS BRANCAS NOS BOTÕES) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_app} !important; color: {text_main} !important; }}
    [data-testid="stSidebar"] {{ background-color: {bg_sidebar} !important; border-right: 1px solid {border_card}; }}
    
    /* CORREÇÃO DOS BOTÕES - FORÇANDO BRANCO EM TUDO */
    div.stButton > button {{
        background-color: {accent} !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        width: 100%;
        border-radius: 8px;
    }}

    /* Garante que textos internos (tags p ou span) também fiquem brancos */
    div.stButton > button p, div.stButton > button span, div.stButton > button div {{
        color: #FFFFFF !important;
    }}

    /* Mantém as letras brancas ao passar o mouse ou clicar */
    div.stButton > button:hover, div.stButton > button:active, div.stButton > button:focus {{
        color: #FFFFFF !important;
        background-color: {accent} !important;
        opacity: 0.92;
    }}

    /* Correção da Toolbar e Toolbar Header */
    header[data-testid="stHeader"] {{
        background-color: {bg_app} !important;
        color: {text_main} !important;
    }}

    /* Correção do File Uploader e botão 'Browse files' */
    [data-testid="stFileUploader"] section {{
        background-color: {bg_widget} !important;
        border: 1px dashed {border_card} !important;
        color: {text_main} !important;
    }}
    [data-testid="stFileUploader"] button {{
        background-color: {bg_app} !important;
        color: {text_main} !important;
        border: 1px solid {border_card} !important;
    }}

    /* Correção campos de seleção e inputs */
    div[data-baseweb="select"] > div, 
    div[data-baseweb="input"] > div, 
    div[data-baseweb="base-input"] {{
        background-color: {bg_widget} !important;
        color: {text_main} !important;
        border: 1px solid {border_card} !important;
    }}

    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: {bg_summary} !important;
        border: 1px solid {accent} !important;
        border-left: 8px solid {accent} !important;
        border-radius: 12px !important;
        padding: 25px !important;
    }}

    .kpi-card-top {{ background-color: {bg_card} !important; border: 1px solid {border_card} !important; border-radius: 12px !important; padding: 20px !important; height: 120px; display: flex; flex-direction: column; justify-content: center; }}
    .summary-card {{ background-color: {bg_summary} !important; border: 1px solid {accent} !important; border-left: 5px solid {accent} !important; border-radius: 12px !important; padding: 15px; height: 100px; display: flex; align-items: center; gap: 15px; }}
    .insight-card {{ background-color: {bg_card}; border-left: 4px solid {accent}; padding: 20px; border-radius: 8px; margin-bottom: 15px; border: 1px solid {border_card}; }}

    h1, h2, h3, b, strong, label {{ color: {text_main} !important; }}
    p, span, small {{ color: {text_sub} !important; }}
    [data-testid="stFileUploader"] p, [data-testid="stFileUploader"] small {{ color: {text_main} !important; }}
    </style>
    """, unsafe_allow_html=True)
# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### {t['title']}")
    theme_sel = st.selectbox(t['tema'], ["Dark", "Light"], index=0 if st.session_state.theme == 'Dark' else 1)
    if theme_sel != st.session_state.theme:
        st.session_state.theme = theme_sel
        st.rerun()
    st.session_state.lang_selector = st.selectbox("Language", ["Português", "English"], on_change=change_lang)
    st.markdown("---")
    uploaded_file = st.file_uploader(t['upload'], type=["csv"])
    
    # Feedback visual sobre qual arquivo está carregado
    default_csv_path = os.path.join(os.path.dirname(__file__), "starbucks", "Starbucks Store Locations.csv")
    df = None
    
    if uploaded_file:
        st.success(f"✅ Usando arquivo carregado: **{uploaded_file.name}**")
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except Exception:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='latin-1')
    else:
        df_db = carregar_dados_supabase()
        if df_db is not None and not df_db.empty:
            df = df_db
            st.success("☁️ Carregado com sucesso do banco de dados **Supabase**!")
        elif os.path.exists(default_csv_path):
            st.info("📂 Usando fallback local: **Starbucks Store Locations.csv**")
            try:
                df = pd.read_csv(default_csv_path, encoding='utf-8')
            except Exception:
                df = pd.read_csv(default_csv_path, encoding='latin-1')
        else:
            st.warning("⚠️ Nenhuma fonte de dados encontrada. Faça o upload de um CSV.")

# --- LÓGICA DE DADOS ---
if df is not None:
    df.columns = [str(c).strip().lower() for c in df.columns]
    mapping = {
        'latitude': 'lat', 
        'longitude': 'lon', 
        'city': 'Cidade', 
        'country': 'País', 
        'state/province': 'Estado',
        'state_province': 'Estado'
    }
    df = df.rename(columns=mapping)
    
    required_cols = ['lat', 'lon', 'Cidade', 'País', 'Estado']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        st.error(f"⚠️ O arquivo carregado não possui algumas colunas obrigatórias.")
        st.warning(f"**Colunas ausentes:** {', '.join(missing_cols)}")
        st.stop()
        
    df = df.dropna(subset=['lat', 'lon'])

    with st.sidebar:
        pais_sel = st.selectbox(t['pais'], sorted(df['País'].unique()))
        df_f = df[df['País'] == pais_sel]
        estados = sorted(df_f['Estado'].dropna().unique())
        estado_sel = st.selectbox(t['estado'], [t['todas']] + estados)
        if estado_sel != t['todas']: df_f = df_f[df_f['Estado'] == estado_sel]
        cidades = sorted(df_f['Cidade'].dropna().unique())
        cidade_sel = st.selectbox(t['cidade'], [t['todas']] + cidades)
        if cidade_sel != t['todas']: df_f = df_f[df_f['Cidade'] == cidade_sel]

    # KPIs TOPO
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(f'<div class="kpi-card-top">Lojas<br><h3>{len(df_f)}</h3></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="kpi-card-top">País<br><h3>{pais_sel}</h3></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="kpi-card-top">Estado<br><h3>{estado_sel}</h3></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="kpi-card-top">Cidades<br><h3>{len(cidades)}</h3></div>', unsafe_allow_html=True)

    # SIMULADOR
    st.markdown(f"<br><h3>{t['simulador_h']}</h3>", unsafe_allow_html=True)
    with st.container(border=True):
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1: dens = st.slider(t['densidade'], 0, 50000, 15000)
        with sc2: renda_sup = st.toggle(t['renda'], value=True)
        with sc3: p_jovem = st.selectbox(t['jovem'], ["Baixo", "Médio", "Alto"], index=2)
        with sc4: fluxo = st.selectbox(t['fluxo'], ["Zonas Residenciais", "Centros Comerciais", "Hubs"], index=1)
    
    txt_renda = "Superior a 30%" if renda_sup else "Média Nacional"

    st.markdown("<br>", unsafe_allow_html=True)
    i1, i2, i3, i4 = st.columns(4)
    with i1: st.markdown(f'<div class="summary-card">👥 DENSIDADE<br><b>{dens} hab/km²</b></div>', unsafe_allow_html=True)
    with i2: st.markdown(f'<div class="summary-card">💰 RENDA<br><b>{txt_renda}</b></div>', unsafe_allow_html=True)
    with i3: st.markdown(f'<div class="summary-card">👤 PÚBLICO<br><b>{p_jovem}</b></div>', unsafe_allow_html=True)
    with i4: st.markdown(f'<div class="summary-card">👣 FLUXO<br><b>{fluxo}</b></div>', unsafe_allow_html=True)

    # MAPA
    st.markdown(f"<br><h3>🗺️ {t['mapa_h']}</h3>", unsafe_allow_html=True)
    m = folium.Map(location=[df_f['lat'].mean(), df_f['lon'].mean()], zoom_start=12, tiles=map_tile)
    cluster = MarkerCluster().add_to(m)
    for _, r in df_f.iterrows():
        folium.Marker([r['lat'], r['lon']], icon=folium.Icon(color='green', icon='coffee', prefix='fa')).add_to(cluster)
    
    if st.session_state.expansion_coords:
        for pt in st.session_state.expansion_coords:
            folium.Circle(location=[pt['lat'], pt['lon']], radius=800, color='#00ff88', fill=True, fill_opacity=0.4, popup=pt['name']).add_to(m)
    st_folium(m, width="100%", height=500, returned_objects=[])

    # IA ACTION
    st.divider()
    if st.button(t['botao_ia']):
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key: st.error("Configure a GEMINI_API_KEY nos Secrets.")
        else:
            with st.spinner("IA processando estratégia..."):
                try:
                    # Determinar a localização exata para a IA não alucinar com "Todas"
                    if cidade_sel != t['todas']:
                        local_ia = f"{cidade_sel}, {estado_sel}, {pais_sel}"
                    elif estado_sel != t['todas']:
                        local_ia = f"estado de {estado_sel}, {pais_sel}"
                    else:
                        local_ia = f"{pais_sel}"
                        
                    res_ia = obter_analise_ia(api_key, local_ia, len(df_f), dens, txt_renda, p_jovem, fluxo)
                    st.session_state.ai_analysis = res_ia
                    match_c = re.findall(r"\[([-+]?\d*\.\d+|\d+),\s*([-+]?\d*\.\d+|\d+),\s*([^\]]+)\]", res_ia)
                    st.session_state.expansion_coords = [{'lat': float(m[0]), 'lon': float(m[1]), 'name': m[2]} for m in match_c]
                    match_f = re.search(r"FORMATO:\s*([\w-]+)", res_ia, re.IGNORECASE)
                    fmt_detectado = match_f.group(1).lower() if match_f and match_f.group(1).lower() in STORE_IMAGES else "core"
                    st.session_state.suggested_format = fmt_detectado
                    st.session_state.selected_image = random.choice(STORE_IMAGES[fmt_detectado])
                    st.rerun()
                except Exception as e: st.error(f"Erro IA: {e}")

    # EXIBIÇÃO RESULTADO IA
    if st.session_state.ai_analysis:
        st.markdown(f"### {t['ia_h']}")
        col_txt, col_img = st.columns([2, 1])
        with col_txt:
            clean_ia = re.sub(r"FORMATO:.*|COORDENADAS:.*", "", st.session_state.ai_analysis, flags=re.S).strip()
            st.markdown(f'<div class="insight-card">{clean_ia}</div>', unsafe_allow_html=True)
        with col_img:
            fmt = st.session_state.suggested_format
            st.markdown(f"**🏗️ Design Sugerido: {fmt.title()}**")
            if 'selected_image' not in st.session_state or not st.session_state.selected_image:
                st.session_state.selected_image = random.choice(STORE_IMAGES.get(fmt, STORE_IMAGES["core"]))
            url_img = st.session_state.selected_image
            b64 = baixar_imagem_base64(url_img)
            if b64:
                st.markdown(f'<img src="data:image/jpeg;base64,{b64}" style="width:100%;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.2);"/>', unsafe_allow_html=True)
            else:
                st.image(url_img, use_container_width=True)
    
    # --- FORMULÁRIO DE AVALIAÇÃO (MOVIMENTADO PARA FORA DO IF AI_ANALYSIS) ---
    st.divider()
    c_fb1, c_fb2, c_fb3 = st.columns([1, 1, 1])
    with c_fb2:
        if st.button("📊 Avaliar Experiência da Interface", use_container_width=True):
            st.session_state.show_survey = not st.session_state.show_survey
            st.rerun()

    if st.session_state.show_survey:
        with st.container(border=True):
            st.markdown(f"### Sua opinião é fundamental!")
            ci1, ci2 = st.columns(2)
            nome = ci1.text_input("Nome completo", key="n_srv")
            contato = ci1.text_input("Contato", key="c_srv")
            email = ci2.text_input("E-mail", key="e_srv")
            profissao = ci2.text_input("Profissão", key="p_srv")
            
            res_likert = {}
            questions = ["A interface é intuitiva?", "O design visual ajudou?", "A IA foi relevante?", "O mapa ajudou?"]
            for i, q in enumerate(questions):
                res_likert[f"Q{i+1}"] = st.select_slider(q, options=t['likert_opts'], value=t['likert_opts'][2], key=f"lk_{i}")

            if st.button("Enviar Avaliação Final", use_container_width=True):
                if nome and email and contato:
                    try:
                        contato_num = int(re.sub(r'\D', '', contato))
                        dados = {"nome": nome, "email": email, "contato": contato_num, "profissao": profissao, 
                                 "q1": res_likert["Q1"], "q2": res_likert["Q2"], "q3": res_likert["Q3"], "q4": res_likert["Q4"]}
                        supabase.table("respostas").insert(dados).execute()
                        st.success(f"✅ Obrigado, {nome}!")
                        st.balloons()
                        st.session_state.show_survey = False
                        st.rerun()
                    except Exception as e: st.error(f"Erro Banco: {e}")
                else: st.warning("Preencha Nome, E-mail e Contato.")
else:
    st.info(t['aviso_csv'])