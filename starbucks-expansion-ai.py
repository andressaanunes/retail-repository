import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import google.generativeai as genai
import re

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Starbucks Insights",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEMA DE ESTADO INICIAL ---
if 'lang' not in st.session_state: st.session_state.lang = 'PT' 
if 'theme' not in st.session_state: st.session_state.theme = 'Light' 
if 'ai_analysis' not in st.session_state: st.session_state.ai_analysis = None
if 'expansion_coords' not in st.session_state: st.session_state.expansion_coords = []
if 'suggested_format' not in st.session_state: st.session_state.suggested_format = "Core"

# Banco de Imagens de Arquitetura (URLs estáveis)
STORE_IMAGES = {
    "drive-thru": "https://images.unsplash.com/photo-1600093463592-8e36ae95ef56?q=80&w=1000&auto=format&fit=crop",
    "flagship": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?q=80&w=1000&auto=format&fit=crop",
    "quiosque": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?q=80&w=1000&auto=format&fit=crop",
    "core": "https://images.unsplash.com/photo-1501339817302-4448f9958e74?q=80&w=1000&auto=format&fit=crop"
}

def change_lang():
    mapping = {"Português": 'PT', "English": 'EN'}
    st.session_state.lang = mapping.get(st.session_state.lang_selector, 'PT')

t_dict = {
    'PT': {
        'title': "☕ Starbucks Insights", 'subtitle': "Simulador de Expansão - Análise de Vazios Comerciais via IA Geográfica",
        'config': "Configurações de Dados", 'upload': "Upload do CSV", 'pais': "País", 'estado': "Estado", 'cidade': "Cidade", 'todas': "Todas",
        'simulador_h': "Simulador de Cenários", 'simulador_info': "Ajuste os indicadores abaixo para definir o perfil da nova unidade",
        'densidade': "Densidade Populacional", 'renda': "Renda Superior", 'renda_sup': "Superior a 30%", 'renda_nac': "Média Nacional",
        'jovem': "Público Jovem", 'fluxo': "Fluxo de Pedestres", 'resumo': "Resumo do Cenário Configurado",
        'mapa_h': "Mapeamento de Unidades Atuais e Sugestões", 'ia_h': "IA Strategic Insights", 'botao_ia': "Gerar Análise de Expansão Baseada no Cenário",
        'aviso_csv': "Carregue o CSV para ativar o simulador.", 'aviso_key': "Por favor, insira a Gemini API Key na barra lateral.", 'tema': "Modo de Interface"
    },
    'EN': {
        'title': "☕ Starbucks Insights", 'subtitle': "Expansion Simulator - Commercial Void Analysis via Geographic AI",
        'config': "Data Settings", 'upload': "Upload CSV", 'pais': "Country", 'estado': "State", 'cidade': "City", 'todas': "All",
        'simulador_h': "Expansion Scenario Simulator", 'simulador_info': "Adjust the indicators below to define the profile of the new unit",
        'densidade': "Population Density", 'renda': "High Income", 'renda_sup': "Above 30%", 'renda_nac': "National Average",
        'jovem': "Young Audience", 'fluxo': "Pedestrian Flow", 'resumo': "Configured Scenario Summary",
        'mapa_h': "Current Units Mapping and Suggestions", 'ia_h': "AI Strategic Insights", 'botao_ia': "Generate Expansion Analysis Based on Scenario",
        'aviso_csv': "Upload CSV to activate the simulator.", 'aviso_key': "Please enter the Gemini API Key in the sidebar.", 'tema': "Interface Mode"
    }
}
t = t_dict.get(st.session_state.lang, t_dict['PT'])

# --- CORES ---
if st.session_state.theme == 'Dark':
    bg_app, bg_sidebar, bg_card, bg_widget = "#050505", "#0a0a0a", "#0d1310", "#111b17"
    border_card, text_main, text_sub = "#142b20", "#ffffff", "#888888"
    accent, bg_summary = "#00ff88", "rgba(0, 255, 136, 0.08)"
    map_tile, btn_text = "cartodbdark_matter", "#000000"
else:
    bg_app, bg_sidebar, bg_card, bg_widget = "#f8f9fa", "#ffffff", "#ffffff", "#ffffff"
    border_card, text_main, text_sub = "#dee2e6", "#1e3d33", "#495057"
    accent, bg_summary = "#00704A", "rgba(0, 112, 74, 0.08)"
    map_tile, btn_text = "cartodbpositron", "#ffffff"

# --- CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_app} !important; color: {text_main} !important; }}
    [data-testid="stSidebar"] {{ background-color: {bg_sidebar} !important; border-right: 1px solid {border_card}; }}
    
    /* CONTAINER SIMULADOR - VERDE FLUORESCENTE */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        background-color: rgba(0, 255, 136, 0.1) !important;
        border: 1px solid #00ff88 !important;
        border-left: 8px solid #00ff88 !important;
        border-radius: 12px !important;
        padding: 25px !important;
    }}

    /* WIDGETS LIGHT MODE */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, [data-testid="stFileUploader"] section {{
        background-color: {bg_widget} !important;
        color: {text_main} !important;
        border: 1px solid {border_card} !important;
    }}
    [data-testid="stFileUploader"] button, .stTextInput input {{
        background-color: #ffffff !important; color: #1e3d33 !important; border: 1px solid #dee2e6 !important;
    }}

    /* BOTAO PRINCIPAL */
    .stButton > button {{
        background-color: {accent} !important; color: {btn_text} !important;
        font-weight: 600 !important; width: 100%; border: none !important;
    }}

    /* CARDS */
    .kpi-card-top {{ background-color: {bg_card} !important; border: 1px solid {border_card} !important; border-radius: 12px !important; padding: 25px !important; margin-bottom: 15px !important; }}
    .summary-card {{ background-color: {bg_summary} !important; border: 1px solid {accent} !important; border-left: 5px solid {accent} !important; border-radius: 12px !important; padding: 15px; display: flex; align-items: center; gap: 15px; }}
    
    /* IMAGEM DESIGN */
    .store-design-img {{ width: 100%; border-radius: 12px; border: 4px solid {accent}; margin-bottom: 10px; }}
    .insight-card {{ background-color: {bg_card}; border-left: 4px solid {accent}; padding: 20px; border-radius: 8px; margin-bottom: 15px; border: 1px solid {border_card}; }}

    h1, h2, h3, b, strong {{ color: {text_main} !important; }}
    p, label, span, small {{ color: {text_sub} !important; }}
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
    gemini_key = st.text_input("Gemini API Key", type="password")

# --- CONTEÚDO ---
st.title(t['title'])
st.markdown(f"<p>{t['subtitle']}</p>", unsafe_allow_html=True)

if uploaded_file:
    try: df = pd.read_csv(uploaded_file, encoding='utf-8')
    except: 
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='latin-1')
    
    df.columns = [c.strip() for c in df.columns]
    mapping = {'Latitude': 'lat', 'longitude': 'lon', 'Longitude': 'lon', 'latitude': 'lat', 'City': 'Cidade', 'Country': 'País', 'State/Province': 'Estado'}
    df = df.rename(columns=mapping).dropna(subset=['lat', 'lon'])

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
    with col3: st.markdown(f'<div class="kpi-card-top">Estados<br><h3>{len(estados)}</h3></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="kpi-card-top">Cidades<br><h3>{len(cidades)}</h3></div>', unsafe_allow_html=True)

    # SIMULADOR
    st.markdown(f"<br><h3>{t['simulador_h']}</h3>", unsafe_allow_html=True)
    with st.container(border=True):
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1: dens = st.slider(t['densidade'], 0, 50000, 15000)
        with sc2: renda_sup = st.toggle(t['renda'], value=True)
        with sc3: p_jovem = st.selectbox(t['jovem'], ["Baixo", "Médio", "Alto"], index=2)
        with sc4: fluxo = st.selectbox(t['fluxo'], ["Zonas Residenciais", "Centros Comerciais", "Hubs"], index=1)
    
    txt_renda = t['renda_sup'] if renda_sup else t['renda_nac']

    # CARDS RESUMO
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
        if not gemini_key: st.warning(t['aviso_key'])
        else:
            with st.spinner("IA processando cenário estratégico..."):
                try:
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel('gemini-flash-latest')
                    prompt = f"""
                    Como consultor estratégico da Starbucks, analise a expansão em {cidade_sel}.
                    Atualmente existem {len(df_f)} lojas.
                    CENÁRIO: Densidade {dens}, Renda {txt_renda}, Público {p_jovem}, Fluxo {fluxo}.
                    TAREFAS:
                    - Identifique 2 áreas reais que deem match.
                    - Explique por que esses KPIs são cruciais.
                    - Sugira UM formato entre: Drive-thru, Flagship, Quiosque ou Core.
                    - No final, inclua obrigatoriamente: FORMATO: [Nome] e COORDENADAS: [LAT, LON, NOME]; [LAT, LON, NOME]
                    """
                    response = model.generate_content(prompt)
                    st.session_state.ai_analysis = response.text
                    
                    # Extração de Coordenadas
                    match_c = re.findall(r"\[([-+]?\d*\.\d+|\d+),\s*([-+]?\d*\.\d+|\d+),\s*([^\]]+)\]", response.text)
                    st.session_state.expansion_coords = [{'lat': float(m[0]), 'lon': float(m[1]), 'name': m[2]} for m in match_c]
                    
                    # Extração de Formato (Melhorada com Regex para hífen e Case Insensitive)
                    match_f = re.search(r"FORMATO:\s*([\w-]+)", response.text, re.IGNORECASE)
                    if match_f:
                        fmt_key = match_f.group(1).lower()
                        st.session_state.suggested_format = fmt_key if fmt_key in STORE_IMAGES else "core"
                    else:
                        st.session_state.suggested_format = "core"
                    
                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

    if st.session_state.ai_analysis:
        st.markdown(f"### {t['ia_h']}")
        col_txt, col_img = st.columns([2, 1])
        with col_txt:
            for section in re.split(r'\n(?=\d\.)', st.session_state.ai_analysis):
                if section.strip(): st.markdown(f'<div class="insight-card">{section}</div>', unsafe_allow_html=True)
        with col_img:
            # Exibição da Imagem
            fmt = st.session_state.suggested_format
            st.markdown(f"**Design Sugerido: {fmt.title()}**")
            st.markdown(f'<img src="{STORE_IMAGES[fmt]}" class="store-design-img">', unsafe_allow_html=True)
            st.caption("Referência de arquitetura para o formato sugerido.")
else:
    st.info(t['aviso_csv'])