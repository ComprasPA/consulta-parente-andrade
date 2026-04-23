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

# 2. FUNÇÃO LOGO BASE64
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return None

base64_logo = get_base64_logo()

# 3. CSS APRIMORADO
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
        border-left: 6px solid #478c3b !important;
    }
    
    [data-testid="stMetricValue"] { 
        font-size: 26px !important; 
        color: #478c3b !important; 
        font-weight: bold !important;
    }
    
    [data-testid="stMetricLabel"] { 
        font-size: 11px !important; 
        font-weight: 800 !important; 
        color: #555555 !important;
        text-transform: uppercase;
    }

    .stDownloadButton button {
        background-color: #f2a933 !important;
        color: white !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
col_logo, col_busca = st.columns([1, 4])
with col_logo:
    try: st.image("logo", width=160)
    except: st.markdown("<h2 style='color:#478c3b;'>PA</h2>", unsafe_allow_html=True)

with col_busca:
    busca = st.text_input("", placeholder="🔍 Pesquisar na base de dados...", label_visibility="collapsed")

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
        st.error(f"Erro: {e}")
        return None

df = carregar_dados()

# 6. DASHBOARD CORRIGIDO
if df is not None:
    # Função auxiliar para contar status ignorando acentos e espaços
    def contar_status(termo):
        return len(df[df['STATUS'].str.contains(termo, case=False, na=False)])

    st.markdown("### 📊 RESUMO DE PEDIDOS")
    
    # Primeira linha de indicadores
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("EM APROVAÇÃO", contar_status("APROVAÇÃO"))
    m2.metric("APROVADO", contar_status("APROVADO"))
    m3.metric("ENV. FORNECEDOR", contar_status("FORNECEDOR"))
    m4.metric("PEND. RECEBIMENTO", contar_status("PENDENTE"))

    # Segunda linha de indicadores
    m5, m6, m7, m8 = st.columns(4)
    m5.metric("RECEBIDO", contar_status("RECEBIDO"))
    m6.metric("ENV. FINANCEIRO", contar_status("FINANCEIRO"))
    m7.metric("PAGO", contar_status("PAGO"))
    m8.metric("TOTAL GERAL", len(df))

    st.markdown("<br>", unsafe_allow_html=True)

    # FILTRO E TABELA
    df_display = df.copy()
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df[mask]

    col_v = ["STATUS", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "CONDIÇÃO PGO", "N° da SC", "N° PC", "Fornecedor", "Nome Fornecedor", "CC", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao"]
    cols = [c for c in col_v if c in df_display.columns]

    c_msg, c_down = st.columns([3, 1])
    with c_msg: st.success(f"📋 LISTAGEM: {len(df_display)} REGISTROS")
    with c_down:
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_display[cols].to_excel(writer, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Consulta_PA.xlsx")

    st.dataframe(df_display[cols], use_container_width=True, hide_index=True)

st.markdown("<p class='footer-text'>PARENTE ANDRADE LTDA | Suprimentos</p>", unsafe_allow_html=True)
