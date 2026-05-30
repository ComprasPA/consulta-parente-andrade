import streamlit as st
import pandas as pd
import re
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA (Sidebar aberta por padrão para o botão ser visível)
st.set_page_config(
    page_title="Portal Gestão de Compras | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS PARA O BOTÃO DE DESTAQUE E MODO OPERADOR
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .header-modern { background: #ffffff; padding: 16px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .op-btn { background-color: #ef4444 !important; color: white !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. BARRA LATERAL (Botão de Operador em evidência)
with st.sidebar:
    st.title("Menu do Portal")
    st.markdown("---")
    st.subheader("⚙️ Área Restrita")
    if "autenticado" not in st.session_state: st.session_state.autenticado = False
    
    if not st.session_state.autenticado:
        senha_input = st.text_input("Senha do Operador:", type="password")
        if st.button("Entrar no Modo Operador"):
            if senha_input == "parente2026":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    else:
        st.success("Operador Autenticado!")
        st.link_button("📥 Abrir Planilha Google", "https://docs.google.com/spreadsheets/d/1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o/edit", use_container_width=True)
        if st.button("Sair do Modo Operador"):
            st.session_state.autenticado = False
            st.rerun()

# 4. INGESTÃO DE DADOS
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

# 5. BUSCA E EXIBIÇÃO
st.markdown('<div class="header-modern"><h1>Portal Gestão de Compras</h1></div>', unsafe_allow_html=True)
busca = st.text_input("🔍 Rastrear SC, PC ou Centro de Custo...")

if busca:
    mask = df_pc.apply(lambda row: row.astype(str).str.contains(busca.strip(), case=False).any(), axis=1)
    resultado = df_pc[mask].copy()
    
    # Mapeamento de colunas conforme solicitado
    mapeamento = {
        "Centro de Custo": "Centro de Custo",
        "Solicitação": "Solicitação",
        "Pedido": "Pedidos"
    }
    resultado.rename(columns=mapeamento, inplace=True)
    
    if not resultado.empty:
        st.dataframe(resultado, use_container_width=True)
    else:
        st.error("Nenhum registro encontrado.")
