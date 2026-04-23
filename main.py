import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Portal de Status - Parente Andrade", layout="wide")

# 2. CABEÇALHO E IDENTIDADE
st.sidebar.image("https://www.parenteandrade.com.br/wp-content/uploads/2021/05/logo-parente-andrade.png", width=150)
st.title("🔍 Consulta de Solicitações e Pedidos")
st.markdown("---")

# 3. CONFIGURAÇÃO DO GOOGLE SHEETS
# Link fornecido da planilha
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

# Função para converter o link de edição em link de exportação CSV
def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300) # Atualiza a cada 5 minutos
def carregar_dados():
    url_csv = preparar_url_google(URL_PLANILHA)
    # Lendo os dados como CSV do Google Sheets
    return pd.read_csv(url_csv)

try:
    df = carregar_dados()
    
    # 4. CAMPO DE PESQUISA
   # 4. CAMPO DE PESQUISA
    busca = st.text_input("Digite o número da SC, numero PC ou requisitante:", placeholder="Ex: 001234 ou Cimento")

    if busca:
        # Filtro que percorre todas as colunas
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        resultado = df[mask]
        
        if not resultado.empty:
            st.success(f"✅ Encontramos {len(resultado)} registro(s).")
            
            # --- SELEÇÃO DE COLUNAS ---
            # Liste aqui EXATAMENTE os nomes das colunas que você QUER mostrar
            # Exemplo: colunas_visiveis = ["NUMERO_SC", "ITEM", "STATUS", "PREVISAO"]
            colunas_visiveis = ["Solicitação", "Item", "Requisitante", "Status", "Previsão"] 
            
            # Verificamos se as colunas existem na sua planilha antes de filtrar
            colunas_existentes = [col for col in colunas_visiveis if col in resultado.columns]
            
            # Exibe apenas as colunas selecionadas
            st.dataframe(resultado[colunas_existentes], use_container_width=True)
            # --------------------------
            
        else:
            st.warning("⚠️ Nenhum registro encontrado para este termo.")

except Exception as e:
    st.error(f"❌ Erro ao conectar com o Google Sheets: {e}")
    st.info("Dica: Verifique se a planilha está compartilhada para 'Qualquer pessoa com o link' como Leitor.")

# Rodapé simples
st.markdown("---")
st.caption("Sistema de Consulta Interna - Parente Andrade")
