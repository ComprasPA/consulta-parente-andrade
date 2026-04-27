import streamlit as st
import pandas as pd
import base64
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Portal Gestão de Compras | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. FUNÇÃO LOGO
@st.cache_data(ttl=86400)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

base64_logo = get_base64_logo()

# 3. CSS (DESIGN)
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    
    .header-wrapper {{
        border: 2px solid #478c3b; border-radius: 10px; padding: 15px 25px;
        background-color: #ffffff; display: flex; align-items: center;
        justify-content: space-between; margin-top: 10px; margin-bottom: 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}
    .portal-title {{ 
        color: #000000 !important; font-size: 35px !important; font-weight: bold !important; 
        text-align: center !important; margin: 0 !important; line-height: 1.1;
    }}
    /* Estilização dos inputs e selectbox */
    div[data-testid="stVerticalBlock"] > div:has(input), div[data-testid="stVerticalBlock"] > div:has(select) {{
        background-color: #ffffff; border-radius: 8px; border: 2px solid #478c3b !important;
    }}
    .stDownloadButton button {{ background-color: #f2a933 !important; color: white !important; font-weight: bold !important; }}
    .status-box {{ background-color: #478c3b; color: white; padding: 12px 20px; border-radius: 10px; font-weight: bold; font-size: 18px; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO COM LISTA SUSPENSA
st.markdown('<div class="header-wrapper">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 4, 3])
with c1:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:120px;">', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="portal-title">Portal Gestão de Compras Parente Andrade</p>', unsafe_allow_html=True)
with c3:
    col_tipo, col_termo = st.columns([1, 1.5])
    with col_tipo:
        tipo_busca = st.selectbox("", ["Geral", "Número SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "STATUS"], label_visibility="collapsed")
    with col_termo:
        busca = st.text_input("", placeholder="🔍 Digite aqui...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 0px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# 5. TRATAMENTO DE DADOS
def tratar_dados(df):
    for col in df.columns:
        if any(x in col.upper() for x in ["NUMERO", "N°", "SC", "PC", "PEDIDO", "COTACAO", "CC", "PRODUTO"]):
            df[col] = df[col].astype(str).str.split('.').str[0].str.strip().replace('nan', '')
    return df

@st.cache_data(ttl=600)
def carregar_bases():
    URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        df_pc = tratar_dados(pd.read_excel(excel, sheet_name=0, dtype=str).fillna(''))
        aba_sc = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.DataFrame()
        if aba_sc:
            df_sc = tratar_dados(pd.read_excel(excel, sheet_name=aba_sc, dtype=str).fillna(''))
        return df_pc, df_sc
    except: return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_bases()

COLUNAS_PADRAO = ["STATUS", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "DT Prev de Entrega"]

# 6. LÓGICA DE FILTRO POR CATEGORIA
if busca:
    termo = busca.lower().strip()
    
    def aplicar_filtro(df, t, tipo):
        if tipo == "Geral":
            return df[df.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
        
        # Mapeia o nome amigável da lista para o nome real da coluna na planilha
        mapa_colunas = {
            "Número SC": "N° da SC",
            "Num. Cotacao": "Num. Cotacao",
            "N° PC": "N° PC",
            "CC": "CC",
            "Nome Fornecedor": "Nome Fornecedor",
            "Produto": "Produto",
            "Descricao": "Descricao",
            "STATUS": "STATUS"
        }
        col_real = mapa_colunas.get(tipo)
        if col_real in df.columns:
            return df[df[col_real].astype(str).str.lower().str.contains(t, na=False)]
        return pd.DataFrame()

    df_res = aplicar_filtro(df_pc, termo, tipo_busca)
    
    if df_res.empty and not df_sc.empty:
        df_res = aplicar_filtro(df_sc, termo, tipo_busca)
        df_res = df_res.rename(columns={"Numero da SC": "N° da SC", "Numero Pedido": "N° PC"})

    if not df_res.empty:
        for col in COLUNAS_PADRAO:
            if col not in df_res.columns: df_res[col] = ""
        st.markdown(f'<div class="status-box">🟢 {len(df_res)} registros encontrados em "{tipo_busca}"</div>', unsafe_allow_html=True)
        st.dataframe(df_res[COLUNAS_PADRAO], use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum resultado para '{busca}' na categoria '{tipo_busca}'")
else:
    st.info("💡 Selecione a categoria e digite o termo para buscar.")
http://googleusercontent.com/action_card_content/26
