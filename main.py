import streamlit as st
import pandas as pd
import re
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA (Sidebar expandida por padrão)
st.set_page_config(
    page_title="Portal Gestão de Compras | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded" # Sidebar sempre aberta
)

# 2. INGESTÃO DE DADOS
@st.cache_data(ttl=10)
def carregar_dados():
    file_id = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"
    URL = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(URL, dtype=str).fillna('')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

df_pc = carregar_dados()

# 3. MENU DE OPERADOR NA SIDEBAR (Sempre Visível)
with st.sidebar:
    st.markdown("### ⚙️ Painel do Operador")
    senha = st.text_input("Senha de acesso:", type="password")
    if senha == "parente2026":
        st.success("Acesso Liberado!")
        st.link_button("📥 Abrir Planilha Google", "https://docs.google.com/spreadsheets/d/1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o/edit", use_container_width=True)
    elif senha:
        st.error("Senha incorreta.")
    st.markdown("---")
    st.caption("Parente Andrade | Suprimentos")

# 4. INTERFACE PRINCIPAL
st.title("Portal Gestão de Compras")
busca = st.text_input("🔍 Rastrear SC, PC ou Centro de Custo...")

if busca:
    mask = df_pc.apply(lambda row: row.astype(str).str.contains(busca.strip(), case=False).any(), axis=1)
    resultado = df_pc[mask].copy()
    
    # Mapeamento de colunas
    mapeamento = {"Centro de Custo": "Centro de Custo", "Solicitação": "Solicitação", "Pedido": "Pedidos"}
    resultado.rename(columns=mapeamento, inplace=True)
    
    if not resultado.empty:
        st.dataframe(resultado, use_container_width=True)
    else:
        st.error("Nenhum registro encontrado.")
else:
    st.info("👋 Olá! Digite um código no campo acima para rastrear.")
