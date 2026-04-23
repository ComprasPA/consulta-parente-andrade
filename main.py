import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Portal de Status - Parente Andrade", layout="wide")

# 2. CABEÇALHO COM LOGO
st.sidebar.image("https://www.parenteandrade.com.br/wp-content/uploads/2021/05/logo-parente-andrade.png", width=150)
st.title("🔍 Consulta de Solicitações e Pedidos")
st.markdown("---")

# 3. LINK DO SHAREPOINT
URL_ONEDRIVE = "https://parenteandrade.sharepoint.com/sites/PARENTEAM28/_layouts/15/Doc.aspx?sourcedoc={8e48b736-6d77-4387-b3fb-3f77e464dc55}&action=downloadview"

@st.cache_data(ttl=600)
def carregar_dados():
    # Carrega a base de dados do Excel
    return pd.read_excel(URL_ONEDRIVE, engine='openpyxl')

try:
    df = carregar_dados()
    
    # 4. INTERFACE DE BUSCA
    busca = st.text_input("Pesquise por Número da SC, Item ou Requisitante:", placeholder="Ex: 001234 ou Cimento")

    if busca:
        # Filtro que busca o termo em todas as colunas
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        resultado = df[mask]
        
        if not resultado.empty:
            st.success(f"✅ Encontramos {len(resultado)} registro(s).")
            st.dataframe(resultado, use_container_width=True)
        else:
            st.warning("⚠️ Nenhum registro encontrado com esse termo.")
    else:
        st.info("💡 Digite um termo acima para iniciar a busca na base de dados de suprimentos.")

except Exception as e:
    st.error("❌ Erro ao conectar com a base de dados.")
    st.info("Certifique-se de que a planilha no SharePoint está configurada com acesso para 'Qualquer pessoa com o link'.")
