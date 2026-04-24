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
    }

    .footer-text { text-align: center; color: #478c3b; font-size: 12px; margin-top: 40px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
col_logo, col_busca = st.columns([1, 4])
with col_logo:
    try: st.image("logo", width=150)
    except: st.subheader("PARENTE ANDRADE")

with col_busca:
    busca = st.text_input("", placeholder="🔍 O que você deseja consultar? (SC, Produto, Fornecedor, CC...)", label_visibility="collapsed")

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
        
        # AJUSTE: COMPLETAR CÓDIGO DO PRODUTO COM ZEROS (10 DÍGITOS)
        if 'Produto' in df_raw.columns:
            df_raw['Produto'] = df_raw['Produto'].astype(str).str.zfill(10)
        
        # Formatação de Datas para o padrão brasileiro DD/MM/AA
        col_datas = ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]
        for col in col_datas:
            if col in df_raw.columns:
                temp = pd.to_datetime(df_raw[col], errors='coerce')
                df_raw[col] = temp.dt.strftime('%d/%m/%y').fillna(df_raw[col]).replace(['NaT', 'nan'], '')
        
        return df_raw
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")
        return None

df = carregar_dados()

# 6. EXIBIÇÃO DOS DADOS
if df is not None:
    df_display = df.copy()
    
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df[mask]

    # ORDEM DEFINIDA PELO USUÁRIO
    col_v = [
        "STATUS", "N° da SC", "N° PC", "CC", "Nome Fornecedor", "Produto", 
        "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", 
        "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", 
        "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "
    ]
    
    cols = [c for c in col_v if c in df_display.columns]

    c_msg, c_down = st.columns([3, 1])
    with c_msg:
        if busca:
            st.success(f"✅ {len(df_display)} registros encontrados.")
        else:
            st.info(f"💡 Total de {len(df_display)} registros carregados.")
    
    with c_down:
        # Lógica para gerar Excel com Auto-Ajuste de Colunas
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_display[cols].to_excel(writer, index=False, sheet_name='Consulta')
            workbook = writer.book
            worksheet = writer.sheets['Consulta']
            
            for i, col in enumerate(cols):
                column_len = df_display[col].astype(str).str.len().max()
                column_len = max(column_len, len(col)) + 2
                worksheet.set_column(i, i, column_len)
                
        st.download_button("📥 BAIXAR EXCEL AJUSTADO", out.getvalue(), "Consulta_PA_Suprimentos.xlsx")

    st.dataframe(df_display[cols], use_container_width=True, hide_index=True)

st.markdown("<p class='footer-text'>PARENTE ANDRADE LTDA | Setor de Suprimentos</p>", unsafe_allow_html=True)
