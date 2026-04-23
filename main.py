import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CSS PARA LAYOUT SUPERIOR COMPACTO (FONTE ORIGINAL)
st.markdown("""
    <style>
    /* Remover espaços excessivos do topo */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* Ocultar menus padrão */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Estilo da caixa de busca */
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 5px 15px !important;
        border-radius: 10px;
        border: 1px solid #478c3b;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Ajuste de contraste das mensagens de alerta */
    div.stAlert > div {
        background-color: #d4edda !important;
        color: #155724 !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CABEÇALHO EM LINHA (Logo à esquerda e Busca ao lado)
col_logo, col_busca = st.columns([1, 4])

with col_logo:
    try:
        # Logo em tamanho moderado para alinhar com a busca
        st.image("logo", width=150)
    except:
        st.subheader("PARENTE ANDRADE")

with col_busca:
    # Campo de busca na parte superior ao lado da logo
    busca = st.text_input(
        "", 
        placeholder="🔍 Pesquisar por SC, Produto, Requisitante ou Centro de Custo (CC)...",
        label_visibility="collapsed"
    )

# Divisor horizontal com a cor da marca
st.markdown("<div style='height: 3px; background-color: #f2a933; margin-bottom: 20px; border-radius: 2px;'></div>", unsafe_allow_html=True)

# 4. CARREGAMENTO DE DADOS (Google Sheets)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        df_raw = pd.read_csv(url_csv, dtype=str)
        # Limpeza de células vazias
        df_raw = df_raw.fillna('')
        
        if 'Produto' in df_raw.columns:
            df_raw['Produto'] = df_raw['Produto'].apply(
                lambda x: str(x).strip().zfill(10) if x != '' else x
            )
        return df_raw
    except:
        return None

df = carregar_dados()

if df is not None:
    if busca:
        # Filtro global
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        resultado = df[mask]
        
        if not resultado.empty:
            colunas_visiveis = [
                "STATUS", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", 
                "DT entrega ", "CONDIÇÃO PGO", "N° da SC", "N° PC", "Fornecedor", 
                "Nome Fornecedor", "CC", "Produto", "Descricao", "UM", "QNT", 
                " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao"
            ]
            colunas_existentes = [col for col in colunas_visiveis if col in resultado.columns]
            
            st.success(f"✅ {len(resultado)} item(s) encontrado(s) para sua pesquisa.")
            st.dataframe(resultado[colunas_existentes], use_container_width=True, hide_index=True)
        else:
            st.warning(f"⚠️ Nenhum registro encontrado para '{busca}'.")
    else:
        st.info("💡 Bem-vindo! Digite acima para consultar o status dos pedidos em tempo real.")
else:
    st.error("Erro ao carregar a base de dados do Google Sheets.")

# 5. RODAPÉ
st.markdown("<p style='text-align: center; color: #666; font-size: 12px; margin-top: 30px;'>PARENTE ANDRADE LTDA<br>Setor de Suprimentos</p>", unsafe_allow_html=True)
