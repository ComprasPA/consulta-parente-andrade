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

# 3. CSS
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
    try: st.image("logo", width=150)
    except: st.subheader("PARENTE ANDRADE")

with col_busca:
    busca = st.text_input("", placeholder="🔍 Pesquisar em todas as colunas...", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO E VÍNCULO (PROCV)
URL_BASE = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP"

@st.cache_data(ttl=300)
def carregar_dados_completos():
    try:
        # Carregar Protheus SC (2)
        url_protheus = f"{URL_BASE}/gviz/tq?tqx=out:csv&sheet=Protheus+SC+(2)"
        df_p = pd.read_csv(url_protheus, dtype=str)
        
        # Limpar nomes das colunas (remover espaços invisíveis no início/fim)
        df_p.columns = df_p.columns.str.strip()
        df_p = df_p.fillna('')

        # Carregar SCM
        url_scm = f"{URL_BASE}/gviz/tq?tqx=out:csv&sheet=SCM"
        df_s = pd.read_csv(url_scm, dtype=str)
        df_s.columns = df_s.columns.str.strip()
        df_s = df_s.fillna('')

        # Vínculo SCM (PROCV)
        if 'Cod SC. SCM' in df_p.columns and 'N° da SC SCM' in df_s.columns:
            df_s_ref = df_s[['N° da SC SCM']].drop_duplicates()
            df_p = df_p.merge(df_s_ref, left_on='Cod SC. SCM', right_on='N° da SC SCM', how='left')

        # Formatação de Datas (tentando encontrar colunas mesmo com nomes variados)
        for col in df_p.columns:
            if "DT" in col or "Data" in col or "Dt" in col:
                temp = pd.to_datetime(df_p[col], errors='coerce')
                df_p[col] = temp.dt.strftime('%d/%m/%y').fillna(df_p[col]).replace(['NaT', 'nan'], '')

        if 'Produto' in df_p.columns:
            df_p['Produto'] = df_p['Produto'].astype(str).str.zfill(10)
        
        return df_p
    except Exception as e:
        st.error(f"Erro técnico: {e}")
        return None

df = carregar_dados_completos()

if df is not None:
    # FILTRAGEM
    df_display = df.copy()
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df[mask]

    # DEFINIÇÃO DE ORDEM PRIORITÁRIA (Ajustado conforme seu pedido)
    ordem_desejada = [
        "STATUS", "N° da SC SCM", "N° da SC", "N° PC", "CC", "Nome Fornecedor", 
        "Produto", "Descricao", "UM", "QNT", "Prc Unitario", "Vlr.Total", 
        "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", 
        "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega"
    ]
    
    # Criar lista final de colunas: 
    # 1. Primeiro as da ordem que ele encontrar
    # 2. Depois qualquer outra que sobrar na planilha e não estiver na lista
    cols_finais = [c for c in ordem_desejada if c in df_display.columns]
    cols_restantes = [c for c in df_display.columns if c not in cols_finais]
    cols_totais = cols_finais + cols_restantes

    c_msg, c_down = st.columns([3, 1])
    with c_msg:
        st.info(f"📋 {len(df_display)} registros encontrados. Arraste a tabela para o lado para ver todas as colunas.")
    
    with c_down:
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_display[cols_totais].to_excel(writer, index=False, sheet_name='Dados')
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Suprimentos_PA.xlsx")

    # EXIBIÇÃO FORÇADA DE TODAS AS COLUNAS
    st.dataframe(df_display[cols_totais], use_container_width=True, hide_index=True)

st.markdown("<p style='text-align:center; font-weight:bold; color:#478c3b;'>PARENTE ANDRADE LTDA</p>", unsafe_allow_html=True)
