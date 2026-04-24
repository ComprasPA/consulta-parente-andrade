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

# 3. CSS PARA INTERFACE CLEAN E MARCA D'ÁGUA
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    
    .stApp { background-color: #f0f2f6; }

    /* Marca d'água no fundo */
    .stApp > div > div > div > div > section > div {
        background-image: url("data:image/png;base64,""" + str(base64_logo) + """");
        background-size: 350px;
        background-position: center 250px;
        background-repeat: no-repeat;
        background-attachment: fixed;
        opacity: 0.05;
        z-index: -1;
    }

    .block-container { padding-top: 1rem !important; }

    /* Forçar cabeçalhos da tabela em CAIXA ALTA via CSS */
    th {
        text-transform: uppercase !important;
    }

    /* Barra de Busca */
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 8px 15px !important;
        border-radius: 10px;
        border: 2px solid #478c3b;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* Botão de Download Amarelo PA */
    .stDownloadButton button {
        background-color: #f2a933 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        text-transform: uppercase;
    }

    .footer-text { text-align: center; color: #478c3b; font-size: 12px; margin-top: 40px; font-weight: bold; text-transform: uppercase; }
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
col_logo, col_busca = st.columns([1, 4])
with col_logo:
    try: st.image("logo", width=150)
    except: st.subheader("PARENTE ANDRADE")

with col_busca:
    busca = st.text_input("", placeholder="🔍 PESQUISAR (SC, PRODUTO, FORNECEDOR, CC...)", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO DE DADOS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/edit?usp=sharing"

def preparar_url_google(url):
    if "/edit" in url:
        return url.split("/edit")[0] + "/export?format=csv"
    return url

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        df_raw = pd.read_csv(url_csv, dtype=str).fillna('')
        
        # TRANSFORMAR TODOS OS DADOS EM CAIXA ALTA
        df_raw = df_raw.apply(lambda x: x.str.upper())
        
        # Formatação de Datas
        col_datas = ["DT ENVIO", "DT PGO (AVISTA)", "DT PREV DE ENTREGA", "DT ENTREGA ", "DATA EMISSAO", "DT LIBERACAO"]
        for col in col_datas:
            if col in df_raw.columns:
                temp = pd.to_datetime(df_raw[col], errors='coerce')
                df_raw[col] = temp.dt.strftime('%d/%m/%y').fillna(df_raw[col]).replace(['NAT', 'NAN'], '')
        
        return df_raw
    except Exception as e:
        st.error(f"ERRO AO CARREGAR A PLANILHA: {e}")
        return None

df = carregar_dados()

# 6. EXIBIÇÃO DOS DADOS
if df is not None:
    df_display = df.copy()
    
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca.upper(), case=False).any(), axis=1)
        df_display = df[mask]

    # Lista de colunas em CAIXA ALTA
    col_v = [
        "STATUS", 
        "DT ENVIO", 
        "CONDIÇÃO PGO", 
        "DT PGO (AVISTA)", 
        "DT PREV DE ENTREGA", 
        "DT ENTREGA ", 
        "N° DA SC", 
        "N° PC", 
        "FORNECEDOR", 
        "NOME FORNECEDOR", 
        "CC", 
        "PRODUTO", 
        "DESCRICAO", 
        "UM", 
        "QNT", 
        " PRC UNITARIO", 
        " VLR.TOTAL", 
        "DATA EMISSAO", 
        "DT LIBERACAO"
    ]
    
    cols = [c for c in col_v if c in df_display.columns]

    c_msg, c_down = st.columns([3, 1])
    with c_msg:
        if busca:
            st.success(f"✅ {len(df_display)} REGISTROS ENCONTRADOS.")
        else:
            st.info(f"💡 TOTAL DE {len(df_display)} REGISTROS CARREGADOS.")
    
    with c_down:
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_display[cols].to_excel(writer, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "CONSULTA_PA_SUPRIMENTOS.xlsx")

    st.dataframe(df_display[cols], use_container_width=True, hide_index=True)

st.markdown("<p class='footer-text'>PARENTE ANDRADE LTDA | SETOR DE SUPRIMENTOS</p>", unsafe_allow_html=True)
