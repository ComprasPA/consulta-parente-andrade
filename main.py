import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Portal de Status - Parente Andrade", layout="wide")

# 2. CABEÇALHO E IDENTIDADE
st.sidebar.image("https://www.parenteandrade.com.br/wp-content/uploads/2021/05/logo-parente-andrade.png", width=150)
st.title("🔍 Consulta de Solicitações e Pedidos")
st.markdown("---")

# 3. CONFIGURAÇÃO DO GOOGLE SHEETS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    url_csv = preparar_url_google(URL_PLANILHA)
    return pd.read_csv(url_csv)

try:
    df = carregar_dados()
    
    # 4. CAMPO DE PESQUISA
    busca = st.text_input("Digite o número da SC, nome do item ou requisitante:", placeholder="Ex: 001234 ou Cimento")

    if busca:
        # Filtro que percorre todas as colunas da planilha
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        resultado = df[mask]
        
        if not resultado.empty:
            st.success(f"✅ Encontramos {len(resultado)} registro(s).")
            
            # --- LISTA DE COLUNAS SOLICITADAS ---
            colunas_visiveis = [
                "STATUS", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", 
                "DT entrega ", "CONDIÇÃO PGO", "N° da SC", "N° PC", "Fornecedor", 
                "Nome Fornecedor", "CC", "Produto", "Descricao", "UM", "QNT", 
                " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao"
            ]
            
            # Filtra apenas as colunas que realmente existem na planilha para evitar erro
            colunas_existentes = [col for col in colunas_visiveis if col in resultado.columns]
            
            # Exibe apenas as colunas selecionadas
            st.dataframe(resultado[colunas_existentes], use_container_width=True)
            
        else:
            st.warning("⚠️ Nenhum registro encontrado para este termo.")
    else:
        st.info("💡 Digite um termo acima para iniciar a busca.")

except Exception as e:
    st.error(f"❌ Erro ao processar os dados: {e}")

# Rodapé
st.markdown("---")
st.caption("Sistema de Consulta Interna - Parente Andrade")
