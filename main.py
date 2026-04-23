import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Portal de Status - Parente Andrade", layout="wide")

# 2. DEFINIÇÃO DA SENHA MESTRA
# Altere 'PA2026' para a senha que você desejar
SENHA_CORRETA = "PA2026"

# 3. INTERFACE DE ACESSO NA BARRA LATERAL
st.sidebar.image("https://www.parenteandrade.com.br/wp-content/uploads/2021/05/logo-parente-andrade.png", width=150)
st.sidebar.title("🔐 Acesso Restrito")
senha_digitada = st.sidebar.text_input("Digite a senha para liberar a consulta:", type="password")

# 4. LÓGICA DE PROTEÇÃO
if senha_digitada == SENHA_CORRETA:
    st.title("🔍 Consulta de Solicitações e Pedidos")
    st.markdown("---")

    # LINK DO SEU SHAREPOINT (Já ajustado)
    URL_ONEDRIVE = "https://parenteandrade.sharepoint.com/sites/PARENTEAM28/_layouts/15/Doc.aspx?sourcedoc={8e48b736-6d77-4387-b3fb-3f77e464dc55}&action=downloadview"

    @st.cache_data(ttl=600)
    def carregar_dados():
        # Adicionamos o engine='openpyxl' para garantir a leitura do Excel
        return pd.read_excel(URL_ONEDRIVE, engine='openpyxl')

    try:
        df = carregar_dados()
        
        # BARRA DE PESQUISA
        busca = st.text_input("Pesquise por Número da SC, Item ou Requisitante:", placeholder="Ex: 001234 ou Cimento")

        if busca:
            # Filtro que ignora maiúsculas/minúsculas em todas as colunas
            mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
            resultado = df[mask]
            
            if not resultado.empty:
                st.success(f"✅ Encontramos {len(resultado)} registro(s).")
                st.dataframe(resultado, use_container_width=True)
            else:
                st.warning("⚠️ Nenhum registro encontrado com esse termo.")
        else:
            st.info("💡 Digite um termo acima para iniciar a busca na base de dados.")

    except Exception as e:
        st.error("❌ Erro ao conectar com a base de dados. Verifique se o arquivo no SharePoint está compartilhado corretamente.")
        st.info("Dica: O link deve permitir 'Qualquer pessoa com o link' visualizar.")

else:
    # MENSAGEM CASO A SENHA ESTEJA INCORRETA OU VAZIA
    if senha_digitada != "":
        st.sidebar.error("Senha Incorreta!")
    
    st.title("Portal de Suprimentos - Parente Andrade")
    st.warning("Aguardando liberação de acesso. Insira a senha na barra lateral esquerda.")
    st.image("https://cdn-icons-png.flaticon.com/512/3064/3064155.png", width=200)
