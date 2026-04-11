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

# --- CSS (Melhorado para os Cards de Cenário) ---
st.markdown("""
    <style>
    .metric-container {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #31333F;
        text-align: center;
    }
    .scenario-card {
        background-color: #f0f2f6;
        color: #1e3d33;
        padding: 15px;
        border-radius: 8px;
        border-top: 4px solid #00704A;
        margin-bottom: 10px;
        font-size: 0.9rem;
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
st.sidebar.header("📂 Configurações de Dados")
uploaded_file = st.sidebar.file_uploader("Upload do CSV", type=["csv"])
gemini_key = st.sidebar.text_input("Gemini API Key", type="password")

# --- FUNÇÃO DE CARREGAMENTO ---
@st.cache_data
def load_data(file):
    try:
        df = pd.read_csv(file, encoding='utf-8')
    except:
        file.seek(0)
        df = pd.read_csv(file, encoding='latin-1')
    df.columns = [c.strip() for c in df.columns]
    mapping = {'Latitude': 'lat', 'longitude': 'lon', 'Longitude': 'lon', 'latitude': 'lat',
               'City': 'Cidade', 'Country': 'País', 'State/Province': 'Estado'}
    return df.rename(columns=mapping)

if uploaded_file:
    df = load_data(uploaded_file)
    df = df.dropna(subset=['lat', 'lon'])

    # --- FILTROS GEOGRÁFICOS ---
    paises = sorted(df['País'].unique().astype(str))
    pais_sel = st.sidebar.selectbox("País", paises)
    df_filtrado = df[df['País'] == pais_sel]

    cidades = sorted(df_filtrado['Cidade'].dropna().unique().astype(str))
    cidade_sel = st.sidebar.selectbox("Cidade", ["Todas"] + cidades)
    if cidade_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado['Cidade'] == cidade_sel]

    # --- SEÇÃO: SIMULADOR DE CENÁRIOS (KPIs do Orientador) ---
    st.divider()
    st.subheader("🛠️ Simulador de Cenários de Expansão")
    st.info("Ajuste os indicadores abaixo para definir o perfil da nova unidade.")

    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

    with col_kpi1:
        densidade = st.slider("Densidade Populacional", 0, 50000, 15000, help="Habitantes por km²")
    with col_kpi2:
        renda_superior = st.checkbox("Renda > 30% da Média", value=True)
        renda_texto = "Superior a 30%" if renda_superior else "Média Nacional"
    with col_kpi3:
        publico_jovem = st.select_slider("Público Jovem", options=["Baixo", "Médio", "Alto"], value="Alto")
    with col_kpi4:
        fluxo_pedestres = st.selectbox("Fluxo de Pedestres", ["Zonas Residenciais", "Centros Comerciais", "Hubs de Transporte"])

    # --- EXIBIÇÃO DOS CARDS DO CENÁRIO ATUAL ---
    st.markdown("#### 📋 Resumo do Cenário Configurado")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="scenario-card"><b>Densidade:</b><br>{densidade} hab/km²</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="scenario-card"><b>Renda Familiar:</b><br>{renda_texto}</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="scenario-card"><b>Público Alvo:</b><br>Jovens ({publico_jovem})</div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="scenario-card"><b>Localização:</b><br>{fluxo_pedestres}</div>', unsafe_allow_html=True)

    # --- MAPA ---
    st.subheader("🗺️ Mapeamento de Unidades Atuais")
    center = [df_filtrado['lat'].mean(), df_filtrado['lon'].mean()]
    m = folium.Map(location=center, zoom_start=12 if cidade_sel != "Todas" else 4, tiles="cartodbpositron")
    cluster = MarkerCluster().add_to(m)
    for _, row in df_filtrado.iterrows():
        folium.Marker(location=[row['lat'], row['lon']], icon=folium.Icon(color='green', icon='coffee', prefix='fa')).add_to(cluster)
    st_folium(m, width="100%", height=400, returned_objects=[])

    # --- ÁREA DE INSIGHTS COM IA ---
    st.divider()
    st.subheader("🤖 IA Strategic Insights")
    
    if st.button("🚀 Gerar Análise de Expansão Baseada no Cenário"):
        if not gemini_key:
            st.warning("Por favor, insira a Gemini API Key na barra lateral.")
        else:
            nome_regiao = cidade_sel if cidade_sel != "Todas" else pais_sel
            
            with st.spinner("IA processando cenário..."):
                try:
                    genai.configure(api_key=gemini_key)
                    # Usando o modelo que apareceu na sua lista anterior
                    model = genai.GenerativeModel('gemini-flash-latest') 
                    
                    prompt = f"""
                    Como consultor estratégico da Starbucks, analise a expansão em {nome_regiao}.
                    Atualmente existem {len(df_filtrado)} lojas nesta região.
                    
                    Considere o seguinte CENÁRIO DE EXPANSÃO configurado pelo usuário:
                    1. Densidade Populacional Alvo: {densidade} hab/km².
                    2. Perfil de Renda: {renda_texto}.
                    3. Concentração de Público Jovem: {publico_jovem}.
                    4. Tipo de Fluxo: {fluxo_pedestres}.
                    
                    TAREFAS:
                    - Identifique 2 áreas geográficas em {nome_regiao} que deem match com esses critérios.
                    - Explique por que esses KPIs (Densidade e Renda) são cruciais para o sucesso dessa nova loja.
                    - Sugira o formato de loja (Drive-thru, Quiosque ou Flagship) baseado no fluxo de {fluxo_pedestres}.
                    """
                    
                    response = model.generate_content(prompt)
                    st.markdown(f'<div class="insight-box">{response.text}</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"Erro: {e}")

else:
    st.info("👋 Carregue o CSV para ativar o simulador.")