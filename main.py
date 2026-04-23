import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | Parente Andrade",
    page_icon="🏗️",
    layout="wide"
)

# 2. ESTILIZAÇÃO CSS (Cores Parente Andrade: Verde #478c3b e Amarelo #f2a933)
st.markdown(f"""
    <style>
    /* Fundo e Fonte */
    .stApp {{
        background-color: #FFFFFF;
    }}
    
    /* Título e Textos */
    h2 {{
        color: #1a1a1a !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }}
    
    /* Estilização da Barra de Busca */
    .stTextInput>div>div>input {{
        border: 2px solid #478c3b !important;
        border-radius: 8px;
    }}

    /* Botões e Sucessos */
    .stSuccess {{
        background-color: #478c3b !important;
        color: white !important;
    }}
    
    /* Ajuste da Tabela */
    [data-testid="stDataFrame"] {{
        border: 1px solid #f2a933;
        border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. CABEÇALHO COM LOGO (Via URL estável do site oficial)
# Centralizando a imagem usando colunas
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://www.parenteandrade.com.br/wp-content/uploads/2021/05/logo-parente-andrade.png", use_container_width=True)

st.markdown("<h2 style='text-align: center;'>Portal de Consulta - Suprimentos</h2>", unsafe_allow_html=True)
st.markdown("<div style='height: 2px; background-color: #f2a933; margin-bottom: 25px;'></div>", unsafe_allow_html=True)

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
    # 5. INTERFACE DE BUSCA
    busca = st.text_input("🔍 Digite o N° da SC, Produto ou Requisitante para pesquisar:", placeholder="Ex: 001234 ou Cimento")
    
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
            
            st.success(f"Encontramos {len(resultado)} registro(s)")
            st.dataframe(
                resultado[colunas_existentes], 
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("⚠️ Nenhum registro encontrado. Tente outro termo.")
    else:
        st.info("👋 Bem-vindo. Digite no campo acima para buscar informações da planilha.")
else:
    st.error("Erro ao carregar a planilha. Verifique se o compartilhamento no Google Sheets está para 'Qualquer pessoa com o link'.")

# 6. RODAPÉ
st.markdown("<br><br><hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #478c3b; font-weight: bold;'>Parente Andrade Engenharia</p>", unsafe_allow_html=True)
