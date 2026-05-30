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
    #MainMenu, footer, header {visibility: hidden;}
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    .header-modern { background: #ffffff; padding: 16px 24px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .portal-title { color: #1e293b !important; font-size: 32px !important; font-weight: 800 !important; margin: 0; }
    .status-card { background: #ffffff; padding: 16px 24px; border-radius: 8px; border-left: 5px solid #478c3b; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 16px; }
    .custom-error-red { background-color: #fee2e2 !important; color: #991b1b !important; padding: 16px 24px; border-radius: 8px; border-left: 5px solid #ef4444; margin-bottom: 16px; }
    .operator-btn { width: 100%; background-color: #478c3b; color: white; font-weight: 600; padding: 12px; border-radius: 8px; border: none; cursor: pointer; text-align: center; }
    .operator-btn:hover { background-color: #3b7331; }
    </style>
    """, unsafe_allow_html=True)

# 4. INGESTÃO DE DADOS (Blindada)
@st.cache_data(ttl=10)
def carregar_dados_seguros():
    file_id = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"
    URL_CSV = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(URL_CSV, dtype=str).fillna('')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

df_pc = carregar_dados_seguros()

# 5. CABEÇALHO E BUSCA
st.markdown('<div class="header-modern">', unsafe_allow_html=True)
c1, c2 = st.columns([7, 3])
with c1: st.markdown('<p class="portal-title">Portal Gestão de Compras</p>', unsafe_allow_html=True)
with c2: busca = st.text_input("", placeholder="🔍 Rastrear SC, PC ou CC...")
st.markdown('</div>', unsafe_allow_html=True)

# 6. DICIONÁRIO DE COLUNAS AJUSTADO
DICIONARIO_COLUNAS_EXATAS = [
    {"planilha": "STATUS", "tela": "STATUS", "tipo": "texto"},
    {"planilha": "Centro de Custo", "tela": "Centro de Custo", "tipo": "texto"},
    {"planilha": "Solicitação", "tela": "Solicitação", "tipo": "texto"},
    {"planilha": "Pedido", "tela": "Pedidos", "tipo": "pedido"},   
    {"planilha": "Condição Pagamento", "tela": "Condição Pagamento", "tipo": "texto"},
    {"planilha": "Data Emissao", "tela": "Emissão", "tipo": "data"},
    {"planilha": "Data Liberação", "tela": "Aprovação", "tipo": "data"},
    {"planilha": "Envio", "tela": "Envio", "tipo": "data"},
    {"planilha": "Pagamento", "tela": "Pagamento", "tipo": "texto"}, 
    {"planilha": "Previsão de entrega", "tela": "Previsão de entrega", "tipo": "data"},
    {"planilha": "Entrega", "tela": "Entrega", "tipo": "data"},
    {"planilha": "Fornecedor", "tela": "Fornecedor", "tipo": "texto"},
    {"planilha": "Produto", "tela": "Produto", "tipo": "produto"},                 
    {"planilha": "Descricao", "tela": "Descrição", "tipo": "texto"},
    {"planilha": "UM", "tela": "UM", "tipo": "texto"},
    {"planilha": "Qtd", "tela": "Qtd", "tipo": "numero"},
    {"planilha": "Preço Unitário", "tela": "Preço Unitário", "tipo": "moeda"},
    {"planilha": "Valor Total", "tela": "Valor Total", "tipo": "moeda"}
]

# 7. MOTOR DE BUSCA
if busca:
    termo = busca.strip()
    mask = df_pc.apply(lambda row: row.astype(str).str.contains(termo, case=False).any(), axis=1)
    resultado = df_pc[mask].copy()
    
    if not resultado.empty:
        # Renomeia colunas para exibição final conforme o dicionário
        mapeamento = {item["planilha"]: item["tela"] for item in DICIONARIO_COLUNAS_EXATAS}
        resultado.rename(columns=mapeamento, inplace=True)
        
        st.markdown(f'<div class="status-card">🔍 {len(resultado)} registros localizados.</div>', unsafe_allow_html=True)
        st.dataframe(resultado, use_container_width=True)
    else:
        st.markdown('<div class="custom-error-red">⚠️ Nenhum registro localizado.</div>', unsafe_allow_html=True)

# 8. MENU OPERADOR (Senha: parente2026)
st.markdown("---")
with st.expander("🔒 Área do Operador"):
    senha = st.text_input("Senha:", type="password")
    if senha == "parente2026":
        st.link_button("📥 Abrir Planilha Google", "https://docs.google.com/spreadsheets/d/1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o/edit")
    elif senha:
        st.error("Senha incorreta.")

# 9. RODAPÉ
st.markdown("<p style='text-align:center; color:#94a3b8; font-size:12px;'>Parente Andrade | Coordenação de Suprimentos</p>", unsafe_allow_html=True)
