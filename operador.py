import streamlit as st
import pandas as pd
import re
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Portal Gestão de Compras", layout="wide", initial_sidebar_state="collapsed")

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

# 3. INTERFACE (Cabeçalho e Busca)
st.markdown("<h1 style='text-align: center;'>Portal Gestão de Compras</h1>", unsafe_allow_html=True)
busca = st.text_input("🔍 Rastrear SC, PC ou Centro de Custo...")

if busca:
    mask = df_pc.apply(lambda row: row.astype(str).str.contains(busca.strip(), case=False).any(), axis=1)
    resultado = df_pc[mask].copy()
    mapeamento = {"Centro de Custo": "Centro de Custo", "Solicitação": "Solicitação", "Pedido": "Pedidos"}
    resultado.rename(columns=mapeamento, inplace=True)
    if not resultado.empty: st.dataframe(resultado, use_container_width=True)
    else: st.error("Nenhum registro encontrado.")
else:
    st.info("👋 Olá! Digite um código para rastrear.")

# 4. BOTÃO DO OPERADOR (DESTAQUE MÁXIMO)
st.markdown("---")
st.markdown("<h3 style='text-align: center;'>⚙️ Painel do Operador</h3>", unsafe_allow_html=True)
c1, c2, c3 = st.columns([3, 4, 3])
with c2:
    senha = st.text_input("Senha de acesso ao painel de importação:", type="password")
    if senha == "parente2026":
        st.success("Senha correta!")
        st.link_button("📥 ACESSAR PLANILHA PARA IMPORTAR EXCEL", "https://docs.google.com/spreadsheets/d/1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o/edit", use_container_width=True)
    elif senha:
        st.error("Senha incorreta.")

st.markdown("<p style='text-align:center; color:gray;'>Parente Andrade | Coordenação de Suprimentos</p>", unsafe_allow_html=True)
