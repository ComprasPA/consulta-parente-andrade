import streamlit as st
import pandas as pd
import re

# 1. CONFIGURAÇÃO DA PÁGINA (Sidebar colapsada por padrão)
st.set_page_config(page_title="Portal Gestão de Compras", layout="wide", initial_sidebar_state="collapsed")

# 2. LÓGICA DO "CONSULTOR" (O mesmo que Operador)
with st.sidebar:
    st.markdown("### 🔒 Acesso Restrito")
    # Este é o campo igual ao da sua imagem
    senha_input = st.text_input("Senha Consultor", type="password")
    
    if st.button("Logar"):
        if senha_input == "parente2026":
            st.session_state.autenticado = True
            st.success("Acesso liberado!")
        else:
            st.error("Senha incorreta!")

# 3. CONTEÚDO DO PAINEL (Só aparece se a senha estiver correta)
st.title("Portal Gestão de Compras")

if st.session_state.get("autenticado", False):
    st.info("Painel do Operador Ativo")
    st.link_button("📥 ACESSAR PLANILHA PARA IMPORTAR EXCEL", 
                   "https://docs.google.com/spreadsheets/d/1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o/edit")
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()
else:
    # AQUI ENTRA A SUA LÓGICA DE BUSCA NORMAL
    busca = st.text_input("🔍 Rastrear SC, PC ou Centro de Custo...")
    st.write("Digite sua busca ou use o menu lateral para logar como consultor.")

# 4. INGESTÃO DE DADOS (Mantendo a mesma de antes)
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
