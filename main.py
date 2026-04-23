import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | Parente Andrade",
    page_icon="🏗️",
    layout="wide"
)

# 2. ESTILIZAÇÃO CSS (Cores Oficiais Parente Andrade)
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    .titulo-portal { color: #478c3b; text-align: center; font-family: 'Arial', sans-serif; font-weight: bold; margin-bottom: 0px; }
    .linha-amarela { height: 4px; background-color: #f2a933; margin-bottom: 25px; border-radius: 2px; }
    .stTextInput>div>div>input { border: 2px solid #478c3b !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. CABEÇALHO COM LOGO
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
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
        # Lendo como string para preservar qualquer formatação original
        df_raw = pd.read_csv(url_csv, dtype=str)
        
        # TRATAMENTO PARA EXIBIÇÃO: Garante que a coluna 'Produto' mostre 10 dígitos com zeros à esquerda
        if 'Produto' in df_raw.columns:
            df_raw['Produto'] = df_raw['Produto'].apply(
                lambda x: str(x).strip().zfill(10) if pd.notnull(x) and str(x).strip() != "" else x
            )
            
        return df_raw
    except Exception:
        return None

df = carregar_dados()

if df is not None:
    # 5. INTERFACE DE BUSCA (Retornada ao modelo anterior)
    busca = st.text_input("🔍 Pesquisar por SC, Produto, Requisitante ou Centro de Custo (CC):", 
                         placeholder="Ex: 001234, Cimento, Silvio ou 101001...")
    
    if busca:
        # Lógica de pesquisa original (varre todas as colunas)
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
            
            colunas_existentes = [col for col in colunas_visiveis if col in resultado.columns]
            
            st.success(f"Encontramos {len(resultado)} registro(s).")
            st.dataframe(
                resultado[colunas_existentes], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning(f"Nenhum registro encontrado para '{busca}'.")
    else:
        st.info("👋 Digite acima para consultar o status em tempo real.")
else:
    st.error("Erro ao carregar a base de dados.")

# 6. RODAPÉ
st.markdown("<br><br><br><p style='text-align: center; color: #478c3b; font-size: 12px;'>Parente Andrade Engenharia - Suprimentos © 2024</p>", unsafe_allow_html=True)
