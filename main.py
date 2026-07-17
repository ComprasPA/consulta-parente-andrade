import streamlit as st
import pandas as pd
import base64
import re
from datetime import datetime, timedelta
from io import BytesIO
import urllib.request

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
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    div[data-testid="stElementToolbar"] { display: none !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }
    .stApp { background-color: #f8fafc; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    .header-modern { background: #ffffff; padding: 16px 24px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; margin-top: 0px !important; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); }
    .portal-title { color: #1e293b !important; font-size: 38px !important; font-weight: 800 !important; margin: 0 auto !important; letter-spacing: -1px; white-space: nowrap; }
    div[data-testid="stVerticalBlock"] > div:has(input), div[data-testid="stVerticalBlock"] > div:has(select), div[data-testid="stVerticalBlock"] > div:has(button) { background-color: #ffffff; padding: 2px 6px !important; border-radius: 8px; border: 1px solid #e2e8f0 !important; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02); }
    .status-card { background: #ffffff; color: #1e293b; padding: 16px 24px; border-radius: 8px; font-weight: 600; font-size: 16px; border-left: 5px solid #478c3b; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 16px; }
    .custom-error-red { background-color: #fee2e2 !important; color: #991b1b !important; padding: 16px; border-radius: 8px; border-left: 5px solid #ef4444; }
    .custom-footer-block { text-align: center !important; margin-top: 60px !important; border-top: 1px solid #e2e8f0 !important; padding-top: 24px !important; }
    .signature-fixed { position: fixed; bottom: 12px; left: 20px; color: #94a3b8; font-size: 11px; font-weight: 700; pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

# 4. CARREGAMENTO COM ESTADO
def carregar_dados_seguros():
    file_id = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"
    URL_CSV = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(URL_CSV, dtype=str).fillna('')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

if 'dados_globais' not in st.session_state:
    st.session_state.dados_globais = carregar_dados_seguros()

df_pc = st.session_state.dados_globais

# 5. CABEÇALHO
st.markdown('<div class="header-modern">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.5, 6.5, 2.0])
with c1:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:120px;">', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="center-title-container"><p class="portal-title">Portal Gestão de Compras</p></div>', unsafe_allow_html=True)
with c3:
    busca = st.text_input("", placeholder="🔍 Rastrear SC, PC, Fornecedor ou Item...")
st.markdown('</div>', unsafe_allow_html=True)

# 6. FILTROS COM BOTÃO DE ATUALIZAÇÃO INTEGRADO
if "filtro_status_val" not in st.session_state: st.session_state.filtro_status_val = "Todos"
with st.expander("Filtros Avançados ▼"):
    with st.form("form_filtros"):
        cols = st.columns([3, 2, 2, 2, 2])
        col_status = next((c for c in df_pc.columns if "STATUS" in c.upper()), None)
        lista_status = ["Todos"] + sorted([str(x).strip() for x in df_pc[col_status].unique() if x]) if col_status else ["Todos"]
        
        with cols[0]: st.session_state.filtro_status_val = st.selectbox("Status Operacional:", lista_status)
        with cols[1]: btn_pesquisar = st.form_submit_button("🔍 Pesquisar")
        with cols[2]: 
            if st.form_submit_button("❌ Limpar"): st.rerun()
        with cols[4]:
            if st.form_submit_button("🔄 Atualizar Banco"):
                st.session_state.dados_globais = carregar_dados_seguros()
                st.rerun()

# 7. MOTOR DE BUSCA (Ajustado para procurar em tudo)
if busca:
    termo = busca.lower()
    # Busca em todas as colunas
    df_final = df_pc[df_pc.apply(lambda row: row.astype(str).str.lower().str.contains(termo).any(), axis=1)].copy()
    
    if st.session_state.filtro_status_val != "Todos":
        df_final = df_final[df_final[col_status] == st.session_state.filtro_status_val]
        
    if not df_final.empty:
        st.markdown(f'<div class="status-card">🔍 Resultados encontrados: {len(df_final)}</div>', unsafe_allow_html=True)
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.markdown('<div class="custom-error-red">⚠️ Nenhum registro encontrado.</div>', unsafe_allow_html=True)

# 8. RODAPÉ
st.markdown("<div class='custom-footer-block'>Parente Andrade | Coordenação de Suprimentos</div>", unsafe_allow_html=True)
st.markdown('<div class="signature-fixed">Created by SS.</div>', unsafe_allow_html=True)
