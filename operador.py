import streamlit as st
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="Portal Gestão de Compras", layout="wide")

# 1. INGESTÃO DE DADOS
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

# 2. CABEÇALHO COM BOTÃO DE OPERADOR FIXO NO TOPO
col_head1, col_head2 = st.columns([8, 2])
with col_head1:
    st.title("Portal Gestão de Compras")
with col_head2:
    # Este botão fica sempre visível no topo da página
    if st.button("⚙️ Área do Operador", use_container_width=True):
        st.session_state.show_op = True

# 3. ÁREA DE AUTH E IMPORTAÇÃO
if st.session_state.get("show_op", False):
    st.info("Painel de Segurança")
    senha = st.text_input("Digite a senha para importar:", type="password")
    if senha == "parente2026":
        st.success("Acesso liberado!")
        st.link_button("📥 ACESSAR PLANILHA PARA IMPORTAR EXCEL", "https://docs.google.com/spreadsheets/d/1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o/edit", use_container_width=True)
    elif senha:
        st.error("Senha incorreta.")

# 4. BUSCA
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

st.markdown("---")
st.markdown("<p style='text-align:center; color:gray;'>Parente Andrade | Coordenação de Suprimentos</p>", unsafe_allow_html=True)
