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

# 2. FUNÇÃO LOGO
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

base64_logo = get_base64_logo()

# 3. CSS PARA MARCA D'ÁGUA E ESTILO
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f0f2f6; }}
    .stApp > div > div > div > div > section > div {{
        background-image: url("data:image/png;base64,{base64_logo}");
        background-size: 350px; background-position: center 250px;
        background-repeat: no-repeat; background-attachment: fixed; opacity: 0.05;
    }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 8px 15px !important;
        border-radius: 10px; border: 2px solid #478c3b;
    }}
    .stDownloadButton button {{ background-color: #f2a933 !important; color: white !important; font-weight: bold !important; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CARREGAMENTO DE DADOS
URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        # Tenta ler o Excel usando o motor openpyxl
        excel_file = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        
        # Aba 1: Follow Up | Aba 2: Protheus SC
        df_follow = pd.read_excel(excel_file, sheet_name=0, dtype=str).fillna('')
        
        try:
            df_sc = pd.read_excel(excel_file, sheet_name="Protheus SC", dtype=str).fillna('')
        except:
            df_sc = pd.DataFrame()

        # Padronização de Colunas (Zeros à esquerda)
        if 'N° da SC' in df_follow.columns:
            df_follow['N° da SC'] = df_follow['N° da SC'].astype(str).str.zfill(7)
        
        # Integração das Abas
        if not df_sc.empty:
            col_sc_2 = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'Solicitação'
            if col_sc_2 in df_sc.columns:
                df_sc[col_sc_2] = df_sc[col_sc_2].astype(str).str.zfill(7)
                col_cot = 'Num. Cotacao' if 'Num. Cotacao' in df_sc.columns else 'Código Cotação'
                
                df_final = pd.merge(df_follow, df_sc[[col_sc_2, col_cot]], 
                                    left_on='N° da SC', right_on=col_sc_2, 
                                    how='left').fillna('')
            else:
                df_final = df_follow
        else:
            df_final = df_follow

        return df_final

    except ModuleNotFoundError:
        st.error("❌ Erro: A biblioteca 'openpyxl' não está instalada. Adicione 'openpyxl' ao seu arquivo requirements.txt.")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar os dados: {e}")
        return None

# 5. INTERFACE
df = carregar_dados()

if df is not None:
    busca = st.text_input("", placeholder="🔍 O que deseja consultar? (SC, Cotação, Pedido...)", label_visibility="collapsed")
    
    df_display = df.copy()
    if busca:
        mask = df_display.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df_display[mask]

    # Ordem das Colunas: SC -> Cotação -> Pedido
    cols_ref = ["STATUS", "N° da SC", "Num. Cotacao", "Código Cotação", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao"]
    cols_reais = [c for c in cols_ref if c in df_display.columns]

    st.dataframe(df_display[cols_reais], use_container_width=True, hide_index=True)

st.markdown("<p style='text-align:center; color:#478c3b; font-size:12px;'>PARENTE ANDRADE | Suprimentos</p>", unsafe_allow_html=True)
