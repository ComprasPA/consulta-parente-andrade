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

# 2. FUNÇÃO PARA CONVERTER IMAGEM LOCAL PARA BASE64
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return None

base64_logo = get_base64_logo()

# 3. CSS PARA DASHBOARD SÓLIDO E MARCA D'ÁGUA
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Fundo da tela principal */
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

    /* Barra de Busca Superior */
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 8px 15px !important;
        border-radius: 12px;
        border: 2px solid #478c3b;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    /* --- ESTILO SÓLIDO DO DASHBOARD --- */
    div[data-testid="metric-container"] {
        background-color: #ffffff !important; /* Fundo branco sólido */
        padding: 15px !important;
        border-radius: 12px !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.12) !important; /* Sombra mais forte */
        border-left: 6px solid #478c3b !important; /* Borda lateral Verde PA */
        border-top: 1px solid #eeeeee !important;
    }
    
    [data-testid="stMetricValue"] { 
        font-size: 28px !important; 
        color: #478c3b !important; 
        font-weight: 800 !important;
    }
    
    [data-testid="stMetricLabel"] { 
        font-size: 13px !important; 
        font-weight: bold !important; 
        color: #333333 !important;
        text-transform: uppercase;
    }

    /* Botão de Download */
    .stDownloadButton button {
        background-color: #f2a933 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        width: 100%;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }

    /* Estilo da Tabela */
    .stDataFrame { 
        background-color: #ffffff; 
        border-radius: 15px; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    /* Alertas */
    div.stAlert > div {
        background-color: #478c3b !important;
        color: #ffffff !important;
        border-radius: 10px !important;
    }
    
    .footer-text { text-align: center; color: #478c3b; font-size: 13px; margin-top: 30px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
col_logo, col_busca = st.columns([1, 4])
with col_logo:
    try:
        st.image("logo", width=160)
    except:
        st.markdown("<h2 style='color:#478c3b; margin:0;'>PARENTE ANDRADE</h2>", unsafe_allow_html=True)

with col_busca:
    busca = st.text_input("", placeholder="🔍 Filtrar registros ou indicadores abaixo...", label_visibility="collapsed")

st.markdown("<div style='height: 5px; background-color: #f2a933; margin-bottom: 25px; border-radius: 5px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO DE DADOS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        df_raw = pd.read_csv(url_csv, dtype=str).fillna('')
        
        colunas_data = ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]
        for col in colunas_data:
            if col in df_raw.columns:
                temp_date = pd.to_datetime(df_raw[col], errors='coerce')
                df_raw[col] = temp_date.dt.strftime('%d/%m/%y').fillna(df_raw[col]).replace(['NaT', 'nan'], '')

        if 'Produto' in df_raw.columns:
            df_raw['Produto'] = df_raw['Produto'].apply(lambda x: str(x).strip().zfill(10) if (x != '' and str(x).lower() != 'nan') else '')
        
        return df_raw
    except Exception as e:
        st.error(f"⚠️ Erro base: {e}")
        return None

df = carregar_dados()

# 6. DASHBOARD SÓLIDO E TABELA
if df is not None:
    # FILTRO PARA A TABELA (Dashboard continua mostrando total geral)
    df_display = df.copy()
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df[mask]

    # DASHBOARD COM CORES SÓLIDAS
    st.markdown("### 📊 RESUMO DE OPERAÇÕES")
    c1, c2, c3, c4, c5 = st.columns(5)
    
    # Contagem dinâmica baseada nos termos da sua planilha
    c1.metric("PEND. RECEBIMENTO", len(df[df['STATUS'].str.contains('PENDENTE', case=False, na=False)]))
    c2.metric("PAGOS", len(df[df['STATUS'].str.contains('PAGO', case=False, na=False)]))
    c3.metric("ENV. FORNECEDOR", len(df[df['STATUS'].str.contains('ENVIADO FORNECEDOR', case=False, na=False)]))
    c4.metric("RECEBIDOS", len(df[df['STATUS'].str.contains('RECEBIDO', case=False, na=False)]))
    c5.metric("ENV. FINANCEIRO", len(df[df['STATUS'].str.contains('FINANCEIRO', case=False, na=False)]))

    st.markdown("<br>", unsafe_allow_html=True)

    # EXIBIÇÃO DA TABELA
    colunas_visiveis = [
        "STATUS", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", 
        "DT entrega ", "CONDIÇÃO PGO", "N° da SC", "N° PC", "Fornecedor", 
        "Nome Fornecedor", "CC", "Produto", "Descricao", "UM", "QNT", 
        " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao"
    ]
    colunas_existentes = [col for col in colunas_visiveis if col in df_display.columns]

    c_msg, c_down = st.columns([3, 1])
    with c_msg:
        st.success(f"📋 LISTAGEM: {len(df_display)} REGISTROS ENCONTRADOS")
    with c_down:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_display[colunas_existentes].to_excel(writer, index=False)
        st.download_button("📥 BAIXAR PLANILHA", output.getvalue(), "Consulta_Suprimentos_PA.xlsx")

    st.dataframe(df_display[colunas_existentes], use_container_width=True, hide_index=True)

else:
    st.error("❌ Erro ao carregar base de dados.")

st.markdown(f"<p class='footer-text'>PARENTE ANDRADE LTDA<br><span style='color: #f2a933;'>SETOR DE SUPRIMENTOS</span></p>", unsafe_allow_html=True)
