import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Identidade Visual)
st.set_page_config(
    page_title="Portal de Suprimentos | Parente Andrade",
    page_icon="🏗️",
    layout="wide"
)

# Estilização CSS para aproximar ao site oficial
st.markdown("""
    <style>
    .main {
        background-color: #ffffff;
    }
    .stTextInput label {
        color: #1a1a1a !important;
        font-weight: bold;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
    }
    /* Cor do cabeçalho da tabela */
    thead tr th {
        background-color: #f1f1f1 !important;
        color: #333 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CABEÇALHO (Logo centralizada e Título)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Usando a logo que você enviou (convertida para link de imagem estável)
    st.image("https://www.parenteandrade.com.br/wp-content/uploads/2021/05/logo-parente-andrade.png", use_container_width=True)

st.markdown("<h2 style='text-align: center; color: #1a1a1a;'>Consulta de Status - Suprimentos</h2>", unsafe_allow_html=True)
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
    
    # 4. INTERFACE LIMPA DE BUSCA
    c1, c2 = st.columns([3, 1])
    with c1:
        busca = st.text_input("🔍 O que você deseja consultar?", placeholder="Digite o N° da SC, Produto ou Requisitante...")
    
    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        resultado = df[mask]
        
        if not resultado.empty:
            # Lista de colunas solicitadas
            colunas_visiveis = [
                "STATUS", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", 
                "DT entrega ", "CONDIÇÃO PGO", "N° da SC", "N° PC", "Fornecedor", 
                "Nome Fornecedor", "CC", "Produto", "Descricao", "UM", "QNT", 
                " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao"
            ]
            
            colunas_existentes = [col for col in colunas_visiveis if col in resultado.columns]
            
            # Exibição da Tabela de forma moderna
            st.write(f"Exibindo **{len(resultado)}** resultados encontrados:")
            st.dataframe(
                resultado[colunas_existentes], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.error("⚠️ Nenhum registro encontrado. Verifique o número ou termo digitado.")
    else:
        st.info("👋 Bem-vindo ao Portal de Suprimentos. Digite acima para iniciar a consulta em tempo real.")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")

# 5. RODAPÉ ESTILIZADO
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>© 2024 Parente Andrade Engenharia - Suprimentos Manaus / Urucu</p>", 
    unsafe_allow_html=True
)
