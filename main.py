import streamlit as st
import pandas as pd

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Portal de Status - Parente Andrade", layout="wide")
st.title("🔍 Consulta de Solicitações e Pedidos")
# Adicione isso logo após o st.title
senha_acesso = st.sidebar.text_input("Senha de Acesso", type="password")

if senha_acesso != "SUA_SENHA_AQUI":
    st.warning("Por favor, insira a senha correta para visualizar os dados.")
    st.stop() # Interrompe o script aqui se a senha estiver errada

# LINK DO ONEDRIVE (Substitua pelo link que você gerou no Passo 1)
URL_ONEDRIVE = "https://parenteandrade.sharepoint.com/sites/PARENTEAM28/_layouts/15/Doc.aspx?sourcedoc={8e48b736-6d77-4387-b3fb-3f77e464dc55}&action=downloadview"
@st.cache_data(ttl=600) # Atualiza a cada 10 minutos
def carregar_dados():
    return pd.read_excel(URL_ONEDRIVE)

try:
    df = carregar_dados()
    
    # BUSCA
    busca = st.text_input("Pesquise por Número da SC, Item ou Requisitante:", placeholder="Ex: 001234 ou Cimento")

    if busca:
        # Filtro inteligente (não diferencia maiúsculas/minúsculas)
        filtro = df.apply(lambda row: busca.lower() in str(row.values).lower(), axis=1)
        resultado = df[filtro]
        
        if not resultado.empty:
            st.success(f"Encontramos {len(resultado)} registro(s).")
            st.dataframe(resultado, use_container_width=True)
        else:
            st.warning("Nenhum pedido encontrado com esse termo.")
    else:
        st.info("Digite um termo acima para iniciar a consulta.")

except Exception as e:
    st.error("Erro ao conectar com a base de dados no OneDrive. Verifique o link.")
