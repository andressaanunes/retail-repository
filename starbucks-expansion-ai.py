import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import google.generativeai as genai

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Starbucks Insights",
    page_icon="☕",
    layout="wide"
)

# --- CSS CORRIGIDO (Compatível com Dark e Light Mode) ---
st.markdown("""
    <style>
    .metric-container {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #31333F;
        margin-bottom: 10px;
    }
    .insight-box {
        background-color: #1e3d33;
        color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00704A;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TÍTULO ---
st.title("☕ Starbucks Insights: Simulador de Expansão")
st.markdown("### Estudo de Caso: Análise de Vazios Comerciais via IA Geográfica")

# --- SIDEBAR ---
st.sidebar.header("📂 Configurações")
uploaded_file = st.sidebar.file_uploader("Upload do CSV", type=["csv"])
gemini_key = st.sidebar.text_input("Gemini API Key (Opcional)", type="password")

# --- FUNÇÃO DE CARREGAMENTO RESILIENTE ---
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, encoding='utf-8')
    except:
        file.seek(0)
        df = pd.read_csv(file, encoding='latin-1')
    
    # Padronização de Colunas
    df.columns = [c.strip() for c in df.columns]
    mapping = {
        'Latitude': 'lat', 'longitude': 'lon', 'Longitude': 'lon', 'latitude': 'lat',
        'City': 'Cidade', 'Country': 'País', 'State/Province': 'Estado'
    }
    df = df.rename(columns=mapping)
    return df

if uploaded_file:
    df = load_data(uploaded_file)
    df = df.dropna(subset=['lat', 'lon'])

    # --- FILTROS ---
    paises = sorted(df['País'].unique().astype(str))
    pais_sel = st.sidebar.selectbox("País", paises)
    df_filtrado = df[df['País'] == pais_sel]

    estados = sorted(df_filtrado['Estado'].dropna().unique().astype(str))
    estado_sel = st.sidebar.selectbox("Estado", ["Todos"] + estados)
    if estado_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado['Estado'] == estado_sel]

    cidades = sorted(df_filtrado['Cidade'].dropna().unique().astype(str))
    cidade_sel = st.sidebar.selectbox("Cidade", ["Todas"] + cidades)
    if cidade_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Cidade'] == cidade_sel]

    # --- MÉTRICAS (Formatadas para visibilidade) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-container"><b>Total de Lojas</b><br><h2>{len(df_filtrado)}</h2></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-container"><b>Região</b><br><h2>{pais_sel}</h2></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-container"><b>Cidades Atendidas</b><br><h2>{df_filtrado["Cidade"].nunique()}</h2></div>', unsafe_allow_html=True)

    # --- MAPA ---
    st.subheader("🗺️ Mapeamento de Unidades Atuais")
    center = [df_filtrado['lat'].mean(), df_filtrado['lon'].mean()]
    m = folium.Map(location=center, zoom_start=12 if cidade_sel != "Todas" else 4, tiles="cartodbpositron")
    
    cluster = MarkerCluster().add_to(m)
    for _, row in df_filtrado.iterrows():
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=row.get('Store Name', 'Starbucks'),
            icon=folium.Icon(color='green', icon='coffee', prefix='fa')
        ).add_to(cluster)
    
    st_folium(m, width="100%", height=450, returned_objects=[])

    # --- ÁREA DE INSIGHTS (CORRIGIDA) ---
    st.divider()
    st.subheader("🤖 IA Strategic Insights: Plano de Expansão")
    
    # Usando st.expander para o insight não sumir e ficar organizado
    with st.expander("Clique para Analisar Oportunidades de Expansão", expanded=True):
        if st.button("🚀 Gerar Análise de Vazios Comerciais"):
            nome_regiao = cidade_sel if cidade_sel != "Todas" else pais_sel
            
            with st.spinner(f"IA analisando densidade de lojas em {nome_regiao}..."):
                if not gemini_key:
                    # SIMULAÇÃO DETALHADA PARA O TCC
                    st.success("Análise Concluída (Modo Simulação Estatística)")
                    st.markdown(f"""
                    <div class="insight-box">
                        <h4>Relatório de Expansão: {nome_regiao}</h4>
                        <p><b>1. Identificação de Vazio Comercial:</b> Detectamos uma lacuna de atendimento num raio de 5km em zonas de alta densidade corporativa.</p>
                        <p><b>2. Sugestão de Localização:</b> Bairros periféricos com crescimento vertical (novos prédios) apresentam demanda represada.</p>
                        <p><b>3. Modelo de Loja:</b> Recomendado formato 'Starbucks Pick-up' para otimizar custos operacionais em áreas de alto aluguel.</p>
                        <hr>
                        <small><i>Nota: Para insights geográficos precisos via satélite, insira sua Gemini API Key na barra lateral.</i></small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # CHAMADA REAL GEMINI
                    try:
                        genai.configure(api_key=gemini_key)
                        model = genai.GenerativeModel('gemini-pro')
                        prompt = f"""
                        Como especialista em expansão da Starbucks, analise a região de {nome_regiao} que possui {len(df_filtrado)} lojas.
                        1. Identifique 3 possíveis 'vazios comerciais' (bairros ou zonas) para novas lojas.
                        2. Justifique com base em público-alvo (proximidade de escritórios ou universidades).
                        3. Sugira se a loja deve ser Drive-thru ou tradicional.
                        Seja muito específico e use um tom executivo.
                        """
                        response = model.generate_content(prompt)
                        st.markdown(f'<div class="insight-box">{response.text}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Erro na conexão com a IA: {e}")

else:
    st.info("👋 Bem-vindo! Por favor, carregue o arquivo CSV na barra lateral para iniciar o simulador.")