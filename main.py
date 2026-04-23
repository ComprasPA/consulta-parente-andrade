import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | Parente Andrade",
    page_icon="🏗️",
    layout="wide"
)

# 2. ESTILIZAÇÃO CSS FORÇADA (Cores Oficiais)
st.markdown("""
    <style>
    /* Forçar fundo branco */
    .stApp {
        background-color: #FFFFFF !important;
    }
    
    /* Customização do Título e Divisor */
    .titulo-portal {
        color: #478c3b;
        text-align: center;
        font-family: 'Arial', sans-serif;
        font-weight: bold;
        margin-bottom: 0px;
    }
    
    .linha-amarela {
        height: 4px;
        background-color: #f2a933;
        margin-bottom: 25px;
        border-radius: 2px;
    }

    /* Estilo do campo de busca */
    .stTextInput>div>div>input {
        border: 2px solid #478c3b !important;
    }

    /* Texto de boas-vindas */
    .stInfo {
        background-color: #f8f9fa !important;
        color: #1a1a1a !important;
        border-left: 5px solid #f2a933 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CABEÇALHO COM LOGO
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    # Link direto da logo oficial
    st.image("https://www.parenteandrade.com.br/wp-content/uploads/2021/05/logo-parente-andrade.png", use_container_width=True)

st.markdown("<h2 class='titulo-portal'>Portal de Consulta - Suprimentos</h2>", unsafe_allow_html=True)
st.markdown("<div class='linha-amarela'></div>", unsafe_allow_html=True)

# 4. CONFIGURAÇÃO DO GOOGLE SHEETS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        return pd.read_csv(url_csv)
    except Exception:
        return None

df = carregar_dados()

if df is not None:
    # 5. INTERFACE DE BUSCA (Incluindo CC e Produto na orientação)
    busca = st.text_input("🔍 Pesquisar por SC, Produto, Requisitante ou Centro de Custo (CC):", 
                         placeholder="Ex: 001234, Cimento, Silvio ou 101001...")
    
    if busca:
        # A pesquisa agora varre todas as colunas, incluindo 'CC' e 'Produto' automaticamente
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        resultado = df[mask]
        
        if not resultado.empty:
            # Lista de colunas visíveis solicitadas
            colunas_visiveis = [
                "STATUS", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", 
                "DT entrega ", "CONDIÇÃO PGO", "N° da SC", "N° PC", "Fornecedor", 
                "Nome Fornecedor", "CC", "Produto", "Descricao", "UM", "QNT", 
                " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao"
            ]
            
            # Filtra apenas colunas existentes para evitar erro de nomes
            colunas_existentes = [col for col in colunas_visiveis if col in resultado.columns]
            
            st.success(f"Encontramos {len(resultado)} registro(s) para sua busca.")
            st.dataframe(
                resultado[colunas_existentes], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning(f"Nenhum registro encontrado para '{busca}'. Verifique o termo e tente novamente.")
    else:
        st.info("👋 Olá! Utilize o campo acima para consultar o status de qualquer pedido na base da Parente Andrade.")
else:
    st.error("Erro técnico: Não foi possível ler a planilha do Google Sheets. Verifique o compartilhamento.")

# 6. RODAPÉ
st.markdown("<br><br><br><p style='text-align: center; color: #478c3b; font-size: 12px;'>Parente Andrade Engenharia - Suprimentos © 2024</p>", unsafe_allow_html=True)
