import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | PA",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CSS PARA LAYOUT COMPACTO E FONTE REDUZIDA
st.markdown("""
    <style>
    /* Diminuir fonte global e da tabela */
    html, body, [class*="css"], .stDataFrame {
        font-size: 12px !important;
    }
    
    /* Remover espaços do topo */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Estilo da barra de busca lateral */
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 5px 15px !important;
        border-radius: 8px;
        border: 1px solid #478c3b;
        margin-top: 0px !important;
    }

    /* Ajuste de contraste das mensagens */
    div.stAlert > div {
        background-color: #d4edda !important;
        color: #155724 !important;
        padding: 5px 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CABEÇALHO COMPACTO (Logo à esquerda e Busca ao lado)
# Ajustei a proporção para 1 (logo) para 4 (busca)
col_logo, col_busca = st.columns([1, 4])

with col_logo:
    try:
        # Logo pequena e alinhada
        st.image("logo", width=120)
    except:
        st.write("**PARENTE ANDRADE**")

with col_busca:
    # O campo de busca fica na mesma linha que a logo
    busca = st.text_input(
        "", 
        placeholder="🔍 Pesquisar SC, Produto, Requisitante ou CC...",
        label_visibility="collapsed"
    )

# Divisor fino em Amarelo PA
st.markdown("<div style='height: 2px; background-color: #f2a933; margin-bottom: 15px;'></div>", unsafe_allow_html=True)

# 4. CARREGAMENTO DE DADOS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        df_raw = pd.read_csv(url_csv, dtype=str)
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
            
            st.success(f"✅ {len(resultado)} item(s) encontrado(s)")
            st.dataframe(resultado[colunas_existentes], use_container_width=True, hide_index=True)
        else:
            st.warning(f"⚠️ Nenhum registro para '{busca}'.")
    else:
        # Se não houver busca, mostra uma mensagem discreta
        st.info("💡 Digite o termo de busca acima para visualizar os dados.")
else:
    st.error("Erro ao carregar base de dados.")

# 5. RODAPÉ COMPACTO
st.markdown("<p style='text-align: center; color: #999; font-size: 10px; margin-top: 20px;'>PARENTE ANDRADE LTDA - Suprimentos</p>", unsafe_allow_html=True)
