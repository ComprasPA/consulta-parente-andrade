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

# 3. CSS PARA MARCA D'ÁGUA E ESTILO PA
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

    /* Estilo da Tabela de Centro de Custo (Destaque) */
    .cc-container {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        border-left: 6px solid #f2a933;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
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
    busca = st.text_input("", placeholder="🔍 Digite para filtrar os dados...", label_visibility="collapsed")

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
        
        # Tratamento de Datas para DD/MM/AA
        col_datas = ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]
        for col in col_datas:
            if col in df_raw.columns:
                temp = pd.to_datetime(df_raw[col], errors='coerce')
                df_raw[col] = temp.dt.strftime('%d/%m/%y').fillna(df_raw[col]).replace(['NaT', 'nan'], '')
        
        return df_raw
    except Exception as e:
        st.error(f"Erro ao carregar base: {e}")
        return None

df = carregar_dados()

# 6. CONTAGEM POR CENTRO DE CUSTO E LISTAGEM
if df is not None:
    
    # --- SEÇÃO DE CONTAGEM POR CENTRO DE CUSTO ---
    st.markdown("### 🏢 Itens por Centro de Custo")
    
    if 'CC' in df.columns:
        # Criar contagem agrupada por CC
        df_cc = df['CC'].value_counts().reset_index()
        df_cc.columns = ['Centro de Custo', 'Quantidade de Itens']
        df_cc = df_cc[df_cc['Centro de Custo'] != ''] # Remove vazios se houver
        
        # Exibir em uma tabela compacta e elegante
        st.dataframe(df_cc, hide_index=True, use_container_width=True)
    else:
        st.warning("Coluna 'CC' não encontrada na planilha.")

    st.markdown("---")

    # --- FILTRO E LISTAGEM GERAL ---
    df_display = df.copy()
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df[mask]

    col_v = ["STATUS", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "CONDIÇÃO PGO", "N° da SC", "N° PC", "Fornecedor", "Nome Fornecedor", "CC", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao"]
    cols = [c for c in col_v if c in df_display.columns]

    c_msg, c_down = st.columns([3, 1])
    with c_msg: 
        st.success(f"📋 Registros encontrados: {len(df_display)}")
    with c_down:
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_display[cols].to_excel(writer, index=False)
        st.download_button("📥 Baixar Planilha Excel", out.getvalue(), "Consulta_Suprimentos_PA.xlsx")

    st.dataframe(df_display[cols], use_container_width=True, hide_index=True)

st.markdown("<p class='footer-text'>PARENTE ANDRADE LTDA | Gestão de Suprimentos</p>", unsafe_allow_html=True)
