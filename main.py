import streamlit as st
import pandas as pd
import base64
import re
from datetime import datetime, timedelta
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
    except: 
        return None

base64_logo = get_base64_logo()

# 3. CSS MODERNIZADO
st.markdown(f"""
    <style>
    /* Ocultar elementos padrão */
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    
    .block-container {{ padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }}
    .stApp {{ background-color: #f8fafc; font-family: 'Inter', sans-serif; }}
    
    .header-modern {{
        background: #ffffff; padding: 16px 24px; border-radius: 12px;
        display: flex; align-items: center; justify-content: space-between;
        margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }}
    
    .portal-title {{ color: #1e293b !important; font-size: 38px !important; font-weight: 800 !important; margin: 0 auto !important; }}
    
    /* GAVETA: Alinhamento à direita e remoção de bordas */
    div[data-testid="stExpander"] {{ background: transparent !important; border: none !important; box-shadow: none !important; }}
    div[data-testid="stExpander"] summary {{
        display: flex !important; justify-content: flex-end !important;
        border: none !important; outline: none !important;
    }}
    div[data-testid="stExpander"] summary p {{
        color: #1e293b !important; font-weight: 700 !important; font-size: 16px !important;
    }}
    div[data-testid="stExpander"] summary:hover p {{ color: #478c3b !important; }}

    .status-card {{ background: #ffffff; color: #1e293b; padding: 16px 24px; border-radius: 8px; border-left: 5px solid #478c3b; margin: 16px 0; }}
    .custom-info-blue {{ background-color: #1e40af !important; color: #ffffff !important; padding: 16px 24px; border-radius: 8px; margin: 16px 0; }}
    .custom-error-red {{ background-color: #fee2e2 !important; color: #991b1b !important; padding: 16px 24px; border-radius: 8px; margin: 16px 0; }}
    .custom-welcome-salutation {{ background-color: #ffffff; color: #1e293b; padding: 32px 24px; border-radius: 12px; text-align: center; margin-top: 20px; }}
    
    .system-signature {{ position: fixed; bottom: 8px; left: 12px; font-size: 10px !important; color: #94a3b8 !important; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CARREGAMENTO E BUSCA (Lógica mantida igual)
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

# Header
st.markdown('<div class="header-modern">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.5, 6.5, 2.0])
with c1:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:120px; display:block; margin:auto 0;">', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="center-title-container"><p class="portal-title">Portal Gestão de Compras</p></div>', unsafe_allow_html=True)
with c3:
    busca = st.text_input("", placeholder="🔍 Rastrear SC, PC ou CC...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. GAVETA COM TÍTULO "Filtros Avançados" ALINHADO À DIREITA
with st.expander("Filtros Avançados", expanded=False):
    f_col1, f_col2, f_col3 = st.columns([3.5, 3.5, 3.0])
    with f_col1:
        col_status = next((c for c in df_pc.columns if "STATUS" in c.upper()), None) if not df_pc.empty else None
        lista = ["Todos"] + sorted([str(x).strip() for x in df_pc[col_status].unique() if str(x).strip()]) if col_status else ["Todos"]
        filtro_status = st.selectbox("Filtrar por Status:", options=lista)
    with f_col2:
        data_hoje = datetime.now().date()
        filtro_data = st.date_input("Período de Emissão:", value=(data_hoje - timedelta(days=30), data_hoje))
    with f_col3:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar"): st.cache_data.clear(); st.rerun()

# 6. ASSINATURA E RODAPÉ
st.markdown('<div class="system-signature">System created by SS</div>', unsafe_allow_html=True)
