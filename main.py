import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | Parente Andrade",
    page_icon="🏗️",
    layout="wide"
)

# 2. CSS PARA VISUAL CLEAN COM CORES DA PA (Verde: #478c3b | Amarelo: #f2a933)
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc !important; }
    .main-title {
        color: #478c3b;
        text-align: center;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 700;
        margin-top: -10px;
    }
    .custom-divider {
        height: 4px;
        background-color: #f2a933;
        margin-bottom: 30px;
        border-radius: 2px;
    }
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 2px solid #478c3b;
    }
    .stDataFrame { border-radius: 10px; }
    div.stAlert > div {
        background-color: #478c3b !important;
        color: white !important;
    }
    .footer {
        text-align: center;
        color: #666;
        font-size: 11px;
        margin-top: 50px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CABEÇALHO (Logo local no GitHub)
c1, c2, c3 = st.columns([1.3, 1, 1.3])
with c2:
    try:
        st.image("logo", use_container_width=True)
    except:
        st.error("⚠️ Arquivo 'logo' não encontrado no GitHub.")

st.markdown("<h1 class='main-title'>Portal de Consulta Suprimentos</h1>", unsafe_allow_html=True)
st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# 4. CARREGAMENTO DE DADOS (Google Sheets)
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        df_raw = pd.read_csv(url_csv, dtype=str)
        
        # --- LIMPEZA DE CÉLULAS VAZIAS ---
        # Substitui 'None', 'NaN' ou nulos por um espaço vazio ""
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
    # 5. BUSCA CENTRALIZADA
    sc1, sc2, sc3 = st.columns([1, 1.5, 1])
    with sc2:
        busca = st.text_input(
            "", 
            placeholder="🔍 Ex: 0123456, Cimento, ou 0000001234...",
            label_visibility="collapsed"
        )
    
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
            
            st.success(f"✅ **{len(resultado)}** itens encontrados para '{busca}':")
            st.dataframe(resultado[colunas_existentes], use_container_width=True, hide_index=True)
        else:
            st.warning(f"⚠️ Nenhum registro encontrado para '{busca}'.")
    else:
        st.info("👋 Digite o número da SC ou o final do código do produto para consultar.")
else:
    st.error("Erro ao carregar a base de dados.")

# 6. RODAPÉ
st.markdown(f"<p class='footer'>PARENTE ANDRADE LTDA<br><span style='color: #f2a933;'>Setor de Suprimentos - Dashboard de Apoio Operacional</span></p>", unsafe_allow_html=True)
