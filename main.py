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
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 8px 15px !important;
        border-radius: 10px;
        border: 2px solid #478c3b;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .stDownloadButton button {
        background-color: #f2a933 !important;
        color: white !important;
        font-weight: bold !important;
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

# 5. CARREGAMENTO E LÓGICA DE VÍNCULO (PROCV)
URL_BASE = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP"

@st.cache_data(ttl=300)
def carregar_e_vincular_dados():
    try:
        # Carregar aba principal: Protheus SC (2)
        url_protheus = f"{URL_BASE}/gviz/tq?tqx=out:csv&sheet=Protheus+SC+(2)"
        df_protheus = pd.read_csv(url_protheus, dtype=str).fillna('')

        # Carregar aba de referência: SCM
        url_scm = f"{URL_BASE}/gviz/tq?tqx=out:csv&sheet=SCM"
        df_scm = pd.read_csv(url_scm, dtype=str).fillna('')

        # 1. Ajuste do Código do Produto (10 dígitos)
        if 'Produto' in df_protheus.columns:
            df_protheus['Produto'] = df_protheus['Produto'].astype(str).str.zfill(10)

        # 2. Lógica PROCV (Merge): Vincula 'N° da SC SCM' usando 'Cod SC. SCM' como chave
        if 'Cod SC. SCM' in df_protheus.columns and 'N° da SC SCM' in df_scm.columns:
            df_scm_ref = df_scm[['N° da SC SCM']].drop_duplicates()
            df_protheus = df_protheus.merge(
                df_scm_ref, 
                left_on='Cod SC. SCM', 
                right_on='N° da SC SCM', 
                how='left'
            )

        # Formatação de Datas
        col_datas = ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]
        for col in col_datas:
            if col in df_protheus.columns:
                temp = pd.to_datetime(df_protheus[col], errors='coerce')
                df_protheus[col] = temp.dt.strftime('%d/%m/%y').fillna(df_protheus[col]).replace(['NaT', 'nan'], '')
        
        return df_protheus
    except Exception as e:
        st.error(f"Erro ao processar vínculo de planilhas: {e}")
        return None

df = carregar_e_vincular_dados()

# 6. EXIBIÇÃO
if df is not None:
    df_display = df.copy()
    
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df[mask]

    # LISTA COMPLETA DE COLUNAS PARA EXIBIÇÃO
    col_v = [
        "STATUS", 
        "N° da SC SCM", 
        "N° da SC", 
        "N° PC", 
        "CC", 
        "Nome Fornecedor", 
        "Produto", 
        "Descricao", 
        "UM", 
        "QNT", 
        " Prc Unitario", 
        " Vlr.Total", 
        "Data Emissao", 
        "Dt Liberacao",
        "DT Envio", 
        "CONDIÇÃO PGO", 
        "DT Pgo (AVISTA)", 
        "DT Prev de Entrega", 
        "DT entrega "
    ]
    
    # Filtra apenas as colunas que realmente existem no DataFrame para evitar erro
    cols_existentes = [c for c in col_v if c in df_display.columns]

    c_msg, c_down = st.columns([3, 1])
    with c_msg:
        st.info(f"💡 {len(df_display)} registros encontrados. Utilize a barra de rolagem para ver todas as colunas.")
    
    with c_down:
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_display[cols_existentes].to_excel(writer, index=False, sheet_name='Consulta')
            worksheet = writer.sheets['Consulta']
            for i, col in enumerate(cols_existentes):
                column_len = max(df_display[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)
        st.download_button("📥 BAIXAR EXCEL COMPLETO", out.getvalue(), "Consulta_PA_Suprimentos.xlsx")

    # Força a exibição de todas as colunas identificadas
    st.dataframe(df_display[cols_existentes], use_container_width=True, hide_index=True)

st.markdown("<p class='footer-text'>PARENTE ANDRADE LTDA | Setor de Suprimentos</p>", unsafe_allow_html=True)
