import streamlit as st
import pandas as pd
import base64
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. FUNÇÃO LOGO (Arquivo Local)
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

base64_logo = get_base64_logo()

# 3. CSS E ESTILIZAÇÃO
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f0f2f6; }}
    .stApp > div > div > div > div > section > div {{
        background-image: url("data:image/png;base64,{base64_logo if base64_logo else ''}");
        background-size: 350px; background-position: center 250px;
        background-repeat: no-repeat; background-attachment: fixed; opacity: 0.05;
    }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 8px 15px !important;
        border-radius: 10px; border: 2px solid #478c3b;
    }}
    </style>
    """, unsafe_allow_html=True)

# 4. CARREGAMENTO DOS DADOS (GOOGLE DRIVE)
URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        # Carrega o Excel completo usando o motor openpyxl
        excel_data = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        
        # Aba 1: Follow Up
        df_follow = pd.read_excel(excel_data, sheet_name=0, dtype=str).fillna('')
        
        # Aba 2: Protheus SC
        try:
            df_sc = pd.read_excel(excel_data, sheet_name="Protheus SC", dtype=str).fillna('')
        except:
            df_sc = pd.DataFrame()

        # Limpeza básica (N° da SC com 7 dígitos)
        if 'N° da SC' in df_follow.columns:
            df_follow['N° da SC'] = df_follow['N° da SC'].astype(str).str.zfill(7)

        # Se a aba de cotações existir, faz o merge
        if not df_sc.empty:
            col_sc_2 = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'Solicitação'
            if col_sc_2 in df_sc.columns:
                df_sc[col_sc_2] = df_sc[col_sc_2].astype(str).str.zfill(7)
                col_cot = 'Num. Cotacao' if 'Num. Cotacao' in df_sc.columns else 'Código Cotação'
                
                # Merge 'left' para não perder dados da aba principal
                df_final = pd.merge(df_follow, df_sc[[col_sc_2, col_cot]], 
                                    left_on='N° da SC', right_on=col_sc_2, 
                                    how='left').fillna('')
                return df_final

        return df_follow
    except Exception as e:
        st.error(f"Erro na Planilha: {e}")
        return None

# 5. RENDERIZAÇÃO DA TELA
col_logo, col_vazio = st.columns([1, 4])
with col_logo:
    if base64_logo:
        st.image("logo", width=150)
    else:
        st.subheader("PARENTE ANDRADE")

df = carregar_dados()

if df is not None:
    busca = st.text_input("", placeholder="🔍 Digite para filtrar (SC, Cotação, Produto...)", label_visibility="collapsed")
    
    # Filtro de busca
    if busca:
        mask = df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df[mask]
    else:
        df_display = df

    # Seleção de colunas existentes (Evita erro de tela branca)
    cols_desejadas = [
        "STATUS", "N° da SC", "Num. Cotacao", "Código Cotação", "N° PC", 
        "CC", "Nome Fornecedor", "Produto", "Descricao", "Data Emissao"
    ]
    cols_visiveis = [c for c in cols_desejadas if c in df_display.columns]

    if not df_display.empty:
        st.dataframe(df_display[cols_visiveis], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado encontrado para a busca.")
else:
    st.warning("Aguardando conexão com a base de dados...")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold;'>Suprimentos | Parente Andrade</p>", unsafe_allow_html=True)
