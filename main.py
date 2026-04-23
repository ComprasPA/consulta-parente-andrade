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

# 2. FUNÇÃO PARA CONVERTER IMAGEM LOCAL PARA BASE64 (PARA O CSS)
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return None

base64_logo = get_base64_logo()

# 3. CSS PARA MARCA D'ÁGUA E CORES DA IDENTIDADE PA
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}

    .stApp { background-color: #f0f2f6; }

    .stApp > div > div > div > div > section > div {
        background-image: url("data:image/png;base64,""" + str(base64_logo) + """");
        background-size: 350px;
        background-position: center 250px;
        background-repeat: no-repeat;
        background-attachment: fixed;
        opacity: 0.06;
        z-index: -1;
    }

    .block-container { padding-top: 1.5rem !important; }

    /* Barra de Busca */
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 8px 15px !important;
        border-radius: 12px;
        border: 2px solid #478c3b;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Cards do Dashboard */
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #478c3b; }
    [data-testid="stMetricLabel"] { font-size: 14px !important; font-weight: bold; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 5px solid #f2a933;
    }

    .stDownloadButton button {
        background-color: #f2a933 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        width: 100%;
    }

    .stDataFrame { background-color: #ffffff; border-radius: 15px; }

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
    busca = st.text_input("", placeholder="🔍 Filtrar pedidos ou dashboard...", label_visibility="collapsed")

st.markdown("<div style='height: 5px; background-color: #f2a933; margin-bottom: 20px; border-radius: 5px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO DE DADOS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        df_raw = pd.read_csv(url_csv, dtype=str).fillna('')
        
        # Padronização de datas
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

# 6. DASHBOARD E TABELA
if df is not None:
    # FILTRO GLOBAL (Caso o usuário busque algo)
    df_display = df.copy()
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df[mask]

    # CRIANDO OS CARDS DO DASHBOARD (Baseado na coluna STATUS)
    st.markdown("### 📊 Resumo de Operações")
    c1, c2, c3, c4, c5 = st.columns(5)
    
    # Contagem de Status (Ajuste os nomes entre aspas se estiverem diferentes na sua planilha)
    c1.metric("Pend. Recebimento", len(df[df['STATUS'].str.contains('PENDENTE', case=False, na=False)]))
    c2.metric("Pagos", len(df[df['STATUS'].str.contains('PAGO', case=False, na=False)]))
    c3.metric("Enviado Fornecedor", len(df[df['STATUS'].str.contains('ENVIADO FORNECEDOR', case=False, na=False)]))
    c4.metric("Recebidos", len(df[df['STATUS'].str.contains('RECEBIDO', case=False, na=False)]))
    c5.metric("Env. Financeiro", len(df[df['STATUS'].str.contains('FINANCEIRO', case=False, na=False)]))

    st.markdown("---")

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
        st.success(f"📋 Exibindo {len(df_display)} registros")
    with c_down:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_display[colunas_existentes].to_excel(writer, index=False)
        st.download_button("📥 Baixar Planilha", output.getvalue(), "Consulta_PA.xlsx")

    st.dataframe(df_display[colunas_existentes], use_container_width=True, hide_index=True)

else:
    st.error("❌ Erro ao carregar base.")

st.markdown(f"<p class='footer-text'>PARENTE ANDRADE LTDA<br><span style='color: #f2a933;'>Suprimentos</span></p>", unsafe_allow_html=True)
