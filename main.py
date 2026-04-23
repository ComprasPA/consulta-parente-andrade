import streamlit as st
import pandas as pd
import base64
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. FUNÇÃO LOGO BASE64 PARA MARCA D'ÁGUA
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return None

base64_logo = get_base64_logo()

# 3. CSS PARA DASHBOARD DE CC E MARCA D'ÁGUA
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    .stApp { background-color: #f0f2f6; }

    /* Marca d'água */
    .stApp > div > div > div > div > section > div {
        background-image: url("data:image/png;base64,""" + str(base64_logo) + """");
        background-size: 350px;
        background-position: center 250px;
        background-repeat: no-repeat;
        background-attachment: fixed;
        opacity: 0.05;
        z-index: -1;
    }

    .block-container { padding-top: 1.5rem !important; }

    /* Estilo dos Cards do Dashboard */
    div[data-testid="metric-container"] {
        background-color: #ffffff !important;
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        border-left: 6px solid #f2a933 !important; /* Laranja PA para CC */
    }
    
    [data-testid="stMetricValue"] { 
        font-size: 24px !important; 
        color: #478c3b !important; 
        font-weight: bold !important;
    }
    
    [data-testid="stMetricLabel"] { 
        font-size: 11px !important; 
        font-weight: 800 !important; 
        color: #333333 !important;
    }

    .stDownloadButton button {
        background-color: #f2a933 !important;
        color: white !important;
        font-weight: bold !important;
    }
    
    .footer-text { text-align: center; color: #478c3b; font-size: 13px; margin-top: 30px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
col_logo, col_busca = st.columns([1, 4])
with col_logo:
    try: st.image("logo", width=160)
    except: st.markdown("<h2 style='color:#478c3b;'>PA</h2>", unsafe_allow_html=True)

with col_busca:
    busca = st.text_input("", placeholder="🔍 Filtrar por CC, Produto ou Fornecedor...", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO DE DADOS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        df_raw = pd.read_csv(url_csv, dtype=str).fillna('')
        
        # Tratamento de Datas
        col_datas = ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]
        for col in col_datas:
            if col in df_raw.columns:
                temp = pd.to_datetime(df_raw[col], errors='coerce')
                df_raw[col] = temp.dt.strftime('%d/%m/%y').fillna(df_raw[col]).replace(['NaT', 'nan'], '')
        
        return df_raw
    except Exception as e:
        st.error(f"Erro base: {e}")
        return None

df = carregar_dados()

# 6. DASHBOARD DE CENTROS DE CUSTO
if df is not None and 'CC' in df.columns:
    
    # Contagem de Itens por CC
    df_cc = df[df['CC'] != ''].groupby('CC').size().reset_index(name='Qtd')
    df_cc = df_cc.sort_values(by='Qtd', ascending=False)

    st.markdown("### 📊 DASHBOARD POR CENTRO DE CUSTO")
    
    # Exibe os 4 Centros de Custo com maior volume em Cards
    top_cc = df_cc.head(4)
    cols_metrics = st.columns(len(top_cc) + 1)
    
    for i, row in enumerate(top_cc.itertuples()):
        cols_metrics[i].metric(label=f"CC: {row.CC}", value=row.Qtd)
    
    cols_metrics[-1].metric(label="TOTAL DE ITENS", value=len(df))

    st.markdown("<br>", unsafe_allow_html=True)

    # Divisão em duas colunas: Tabela de Resumo CC e Informações Gerais
    col_tab_cc, col_filtros = st.columns([1, 2])
    
    with col_tab_cc:
        st.markdown("**Resumo Consolidado (CC)**")
        st.dataframe(df_cc, hide_index=True, use_container_width=True)

    with col_filtros:
        st.markdown("**Ações Rápidas**")
        df_display = df.copy()
        if busca:
            mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
            df_display = df[mask]
        
        st.info(f"Filtro ativo: {len(df_display)} registros encontrados.")
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_display.to_excel(writer, index=False)
        st.download_button("📥 BAIXAR BASE FILTRADA (EXCEL)", out.getvalue(), "Suprimentos_PA.xlsx")

    st.markdown("---")

    # TABELA PRINCIPAL
    col_v = ["STATUS", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "CONDIÇÃO PGO", "N° da SC", "N° PC", "Fornecedor", "Nome Fornecedor", "CC", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao"]
    cols = [c for c in col_v if c in df_display.columns]
    
    st.dataframe(df_display[cols], use_container_width=True, hide_index=True)

else:
    st.error("Coluna 'CC' não encontrada ou erro no carregamento.")

st.markdown("<p class='footer-text'>PARENTE ANDRADE LTDA | Suprimentos</p>", unsafe_allow_html=True)
