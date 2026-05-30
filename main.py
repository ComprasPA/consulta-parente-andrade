import streamlit as st
import pandas as pd
import base64
import re
from datetime import datetime, timedelta
from io import BytesIO
import urllib.request

st.set_page_config(
    page_title="Portal Gestão de Compras | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

with st.sidebar:
    st.markdown("### 🔒 Acesso Restrito")
    senha_input = st.text_input("Senha Consultor", type="password")
    if st.button("Logar"):
        if senha_input == "parente2026":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    
    if st.session_state.get("autenticado", False):
        st.success("Logado com sucesso!")
        st.link_button("📥 Acessar Planilha", "https://docs.google.com/spreadsheets/d/1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o/edit")
        if st.button("Sair"):
            st.session_state.autenticado = False
            st.rerun()

@st.cache_data(ttl=86400)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: 
        return None

base64_logo = get_base64_logo()

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    div[data-testid="stElementToolbar"] { display: none !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    .header-modern { background: #ffffff; padding: 16px 24px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .portal-title { color: #1e293b !important; font-size: 38px !important; font-weight: 800 !important; margin: 0 auto !important; letter-spacing: -1px; white-space: nowrap; }
    .status-card { background: #ffffff; color: #1e293b; padding: 16px 24px; border-radius: 8px; font-weight: 600; border-left: 5px solid #478c3b; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 16px; }
    .custom-error-red { background-color: #fee2e2 !important; color: #991b1b !important; padding: 16px 24px; border-radius: 8px; border-left: 5px solid #ef4444; margin-bottom: 16px; }
    .custom-footer-block { text-align: center !important; margin-top: 60px !important; border-top: 1px solid #e2e8f0 !important; padding: 24px !important; }
    .signature-fixed { position: fixed; bottom: 12px; left: 20px; color: #94a3b8; font-size: 11px; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=10)
def carregar_dados_seguros():
    file_id = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"
    URL_CSV = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid=0"
    try:
        df_pc = pd.read_csv(URL_CSV, dtype=str).fillna('')
        if "<html" in str(df_pc.columns[0]).lower(): raise ValueError("Bloqueio HTML")
        df_pc.columns = [str(c).strip() for c in df_pc.columns]
        return df_pc
    except: return pd.DataFrame()

df_pc = carregar_dados_seguros()

st.markdown('<div class="header-modern">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.5, 6.5, 2.0])
with c1:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:120px;">', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="center-title-container"><p class="portal-title">Portal Gestão de Compras</p></div>', unsafe_allow_html=True)
with c3:
    busca = st.text_input("", placeholder="🔍 Rastrear SC, PC ou CC...")
st.markdown('</div>', unsafe_allow_html=True)
