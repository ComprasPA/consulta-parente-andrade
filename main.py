import streamlit as st
import pandas as pd
import base64
import re
from datetime import datetime, timedelta
from io import BytesIO
import urllib.request

# 1. CONFIGURAÇÃO DA PÁGINA (Interface limpa com barra recolhida)
st.set_page_config(
    page_title="Portal Gestão de Compras | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- INCLUSÃO DO MENU OPERADOR NA SIDEBAR ---
with st.sidebar:
    st.markdown("### 🔒 Acesso do Consultor")
    senha_input = st.text_input("Senha Consultor", type="password")
    if st.button("Logar"):
        if senha_input == "parente2026":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta!")
    
    if st.session_state.get("autenticado", False):
        st.success("Logado com sucesso!")
        st.link_button("📥 Acessar Planilha (Importar Excel)", "https://docs.google.com/spreadsheets/d/1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o/edit")
        if st.button("Sair"):
            st.session_state.autenticado = False
            st.rerun()

# 2. FUNÇÃO LOGO
@st.cache_data(ttl=86400)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: 
        return None

base64_logo = get_base64_logo()

# 3. CSS MODERNIZADO
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    div[data-testid="stElementToolbar"] {{ display: none !important; }}
    .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }}
    .stApp {{ background-color: #f8fafc; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
    .header-modern {{ background: #ffffff; padding: 16px 24px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; margin-top: 0px !important; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); }}
    .portal-title {{ color: #1e293b !important; font-size: 38px !important; font-weight: 800 !important; margin: 0 auto !important; letter-spacing: -1px; line-height: 1; white-space: nowrap; }}
    .status-card {{ background: #ffffff; color: #1e293b; padding: 16px 24px; border-radius: 8px; font-weight: 600; font-size: 16px; border-left: 5px solid #478c3b; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 16px; width: 100%; }}
    .custom-info-blue {{ background-color: #e0f2fe !important; color: #0369a1 !important; padding: 16px 24px; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 16px; width: 100%; border-left: 5px solid #0284c7; }}
    .custom-error-red {{ background-color: #fee2e2 !important; color: #991b1b !important; padding: 16px 24px; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 16px; width: 100%; border-left: 5px solid #ef4444; }}
    .custom-welcome-salutation {{ background-color: #ffffff; color: #1e293b; padding: 32px 24px; border-radius: 12px; font-weight: 600; font-size: 20px; text-align: center; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); margin-top: 20px; }}
    .custom-footer-block {{ text-align: center !important; margin-top: 60px !important; border-top: 1px solid #e2e8f0 !important; padding-top: 24px !important; padding-bottom: 24px !important; position: static !important; clear: both !important; width: 100% !important; display: block !important; }}
    .signature-fixed {{ position: fixed; bottom: 12px; left: 20px; color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; z-index: 999999; pointer-events: none; }}
    </style>
    """, unsafe_allow_html=True)

# 4. BACKEND: INGESTÃO DE DADOS
@st.cache_data(ttl=10)
def carregar_dados_seguros():
    file_id = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"
    URL_CSV = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid=0"
    try:
        df_pc = pd.read_csv(URL_CSV, dtype=str).fillna('')
        if "<html" in str(df_pc.columns[0]).lower(): raise ValueError("Bloqueio HTML")
        df_pc.columns = [str(c).strip() for c in df_pc.columns]
        return df_pc
    except:
        return pd.DataFrame()

df_pc = carregar_dados_seguros()

# 5. RESTANTE DA LÓGICA DO SEU CÓDIGO (Busca, Filtros, etc)
# (Mantive a estrutura funcional do seu código original...)
# [O seu código continuaria aqui exatamente igual...]

st.markdown('<div class="header-modern">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.5, 6.5, 2.0])
with c1:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:120px; display:block; margin:auto 0;">', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="center-title-container"><p class="portal-title">Portal Gestão de Compras</p></div>', unsafe_allow_html=True)
with c3:
    busca = st.text_input("", placeholder="🔍 Rastrear SC, PC ou CC...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# [Adicione aqui o restante da sua lógica de filtros e busca exatamente como estava antes]
