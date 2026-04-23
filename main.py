import streamlit as st
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | Parente Andrade",
    page_icon="🏗️",
    layout="wide"
)

# 2. CSS AVANÇADO PARA VISUAL CLEAN
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc !important; }
    .main-title {
        color: #478c3b;
        text-align: center;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 700;
        letter-spacing: -1px;
        margin-top: -20px;
        margin-bottom: 5px;
    }
    .custom-divider {
        height: 3px;
        background: linear-gradient(90deg, transparent, #f2a933, transparent);
        margin-bottom: 30px;
    }
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #eeeeee;
    }
    .stDataFrame {
        border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-radius: 10px;
    }
    .footer {
        text-align: center;
        color: #999;
        font-size: 11px;
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CABEÇALHO (Logo do Google Drive e Título)
# Função para converter link do Drive em link direto de imagem
def converter_link_drive(url):
    id_arquivo = url.split('/')[-2]
    return f'https://drive.google.com/uc?id={id_arquivo}'

c1, c2, c3 = st.columns([1.5, 1, 1.5])
with c2:
    url_logo = "https://drive.google.com/file/d/1KRgJzU5Ewa5I6IcVE6WGe3ekxqbsZzqD/view?usp=sharing"
    st.image(converter_link_drive(url_logo))

st.markdown("<h1 class='main-title'>Portal de Consulta Suprimentos</h1>", unsafe_allow_html=True)
st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

# 4. CARREGAMENTO DE DADOS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        df_raw = pd.read_csv(url_csv, dtype=str)
        if 'Produto' in df_raw.columns:
            df_raw['Produto'] = df_raw['Produto'].apply(
                lambda x: str(x).strip().zfill(10) if pd.notnull(x) and str(x).strip() != "" else x
            )
        return df_raw
    except:
        return None

df = carregar_dados()

if df is not None:
    # 5. BUSCA CENTRALIZADA E REDUZIDA
    sc1, sc2, sc3 = st.columns([1, 2, 1])
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
            
            st.markdown(f"**{len(resultado)}** itens encontrados para '{busca}':")
            st.dataframe(resultado[colunas_existentes], use_container_width=True, hide_index=True)
        else:
            st.warning(f"Nenhum registro encontrado para '{busca}'.")
    else:
        st.markdown("<p style='text-align: center; color: #666;'>Insira um termo acima para iniciar a consulta.</p>", unsafe_allow_html=True)
else:
    st.error("Erro ao carregar a base de dados.")

# 6. RODAPÉ
st.markdown("<p class='footer'>PARENTE ANDRADE LTDA<br>Setor de Suprimentos - Dashboard de Apoio Operacional</p>", unsafe_allow_html=True)
