import streamlit as st
import pandas as pd
import base64
import re
from datetime import datetime, timedelta
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA (Interface limpa com barra recolhida)
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
    except: 
        return None

base64_logo = get_base64_logo()

# 3. CSS MODERNIZADO (Alinhamento do título da gaveta à direita)
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }}
    .stApp {{ background-color: #f8fafc; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
    .header-modern {{ background: #ffffff; padding: 16px 24px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; margin-top: 0px !important; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    div[data-testid="column"] {{ display: flex; align-items: center; justify-content: center; }}
    .center-title-container {{ width: 100%; text-align: center; display: flex; justify-content: center; align-items: center; }}
    .portal-title {{ color: #1e293b !important; font-size: 38px !important; font-weight: 800 !important; margin: 0 auto !important; letter-spacing: -1px; }}
    
    /* GAVETA: Alinhamento à direita e remoção de bordas */
    div[data-testid="stExpander"] summary {{ display: flex !important; justify-content: flex-end !important; text-align: right !important; border: none !important; }}
    div[data-testid="stExpander"] {{ background: transparent !important; border: none !important; box-shadow: none !important; }}
    div[data-testid="stExpander"] summary p {{ color: #1e293b !important; font-weight: 700 !important; font-size: 16px !important; margin: 0 !important; }}
    div[data-testid="stExpander"] summary:hover p {{ color: #478c3b !important; }}
    
    .status-card {{ background: #ffffff; padding: 16px 24px; border-radius: 8px; border-left: 5px solid #478c3b; margin-bottom: 16px; }}
    .custom-error-red {{ background-color: #fee2e2 !important; color: #991b1b !important; padding: 16px 24px; border-radius: 8px; margin-bottom: 16px; }}
    .custom-welcome-salutation {{ background-color: #ffffff; padding: 32px 24px; border-radius: 12px; text-align: center; border: 1px solid #e2e8f0; }}
    .system-signature {{ position: fixed; bottom: 8px; left: 12px; font-size: 10px !important; color: #94a3b8 !important; }}
    </style>
    """, unsafe_allow_html=True)

# BACKEND
@st.cache_data(ttl=60)
def carregar_dados_seguros():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]
        return df_pc
    except: return pd.DataFrame()

df_pc = carregar_dados_seguros()

# CABEÇALHO
st.markdown('<div class="header-modern">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.5, 6.5, 2.0])
with c1:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:120px;">', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="center-title-container"><p class="portal-title">Portal Gestão de Compras</p></div>', unsafe_allow_html=True)
with c3:
    busca = st.text_input("", placeholder="🔍 Rastrear SC, PC ou CC...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# GAVETA DE FILTROS
with st.expander("Filtros Avançados", expanded=False):
    f_col1, f_col2, f_col3, f_col4 = st.columns([2.5, 2.5, 2.5, 2.5])
    col_status = next((c for c in df_pc.columns if "STATUS" in c.upper()), None)
    
    with f_col1:
        lista = ["Todos"] + sorted([str(x).strip() for x in df_pc[col_status].unique() if str(x).strip()]) if col_status else ["Todos"]
        filtro_status = st.selectbox("Status:", options=lista)
    with f_col2:
        # value=None deixa o filtro de data em branco inicialmente
        filtro_data = st.date_input("Período de Emissão:", value=None, format="DD/MM/YYYY")
    with f_col3:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar"): st.rerun()
    with f_col4:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("❌ Limpar Filtros"):
            st.cache_data.clear()
            st.rerun()

# MOTOR DE BUSCA (Ajustado para considerar data apenas se preenchida)
if busca:
    df_final = df_pc[df_pc.apply(lambda row: row.astype(str).str.contains(busca.strip(), case=False).any(), axis=1)]
    
    if filtro_status != "Todos":
        df_final = df_final[df_final[col_status] == filtro_status]
        
    if filtro_data and isinstance(filtro_data, tuple) and len(filtro_data) == 2:
        col_emissao = next((c for c in df_pc.columns if "EMISSAO" in c.upper()), None)
        if col_emissao:
            df_final[col_emissao] = pd.to_datetime(df_final[col_emissao], errors='coerce')
            df_final = df_final[(df_final[col_emissao].dt.date >= filtro_data[0]) & (df_final[col_emissao].dt.date <= filtro_data[1])]

    if not df_final.empty:
        st.markdown(f'<div class="status-card">🔍 {len(df_final)} registros localizados.</div>', unsafe_allow_html=True)
        st.dataframe(df_final, use_container_width=True)
    else:
        st.markdown('<div class="custom-error-red">⚠️ Nenhum registro encontrado.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="custom-welcome-salutation">👋 Bem-vindo ao Portal de Gestão de Compras.</div>', unsafe_allow_html=True)

st.markdown('<div class="system-signature">System created by SS</div>', unsafe_allow_html=True)
