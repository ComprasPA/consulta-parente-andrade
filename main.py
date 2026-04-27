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

# 2. FUNÇÃO LOGO (Arquivo Local no Streamlit)
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        # Tenta ler o arquivo local 'logo'
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        return None

base64_logo = get_base64_logo()

# 3. CSS PARA MARCA D'ÁGUA E INTERFACE
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f0f2f6; }}
    /* Marca d'água */
    .stApp > div > div > div > div > section > div {{
        background-image: url("data:image/png;base64,{base64_logo if base64_logo else ''}");
        background-size: 350px;
        background-position: center 250px;
        background-repeat: no-repeat;
        background-attachment: fixed;
        opacity: 0.05;
        z-index: -1;
    }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff;
        padding: 8px 15px !important;
        border-radius: 10px;
        border: 2px solid #478c3b;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    .stDownloadButton button {{
        background-color: #f2a933 !important;
        color: white !important;
        font-weight: bold !important;
    }}
    .footer-text {{ text-align: center; color: #478c3b; font-size: 12px; margin-top: 40px; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CARREGAMENTO DE DADOS (PLANILHA GOOGLE DRIVE)
URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        # Lê o Excel do Drive (Necessário openpyxl no requirements.txt)
        excel_data = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        
        # Aba 1 (Follow Up) e Aba 2 (Protheus SC)
        df_follow = pd.read_excel(excel_data, sheet_name=0, dtype=str).fillna('')
        
        try:
            df_sc = pd.read_excel(excel_data, sheet_name="Protheus SC", dtype=str).fillna('')
        except:
            df_sc = pd.DataFrame()

        # Padronização de Colunas
        if 'N° da SC' in df_follow.columns:
            df_follow['N° da SC'] = df_follow['N° da SC'].astype(str).str.zfill(7)
        
        if not df_sc.empty:
            col_sc_2 = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'Solicitação'
            if col_sc_2 in df_sc.columns:
                df_sc[col_sc_2] = df_sc[col_sc_2].astype(str).str.zfill(7)
                
                # Identifica a coluna de Cotação na aba 2
                col_cot = 'Num. Cotacao' if 'Num. Cotacao' in df_sc.columns else 'Código Cotação'
                
                # Merge (PROCV)
                df_final = pd.merge(df_follow, df_sc[[col_sc_2, col_cot]], 
                                    left_on='N° da SC', right_on=col_sc_2, 
                                    how='left').fillna('')
            else:
                df_final = df_follow
        else:
            df_final = df_follow

        return df_final
    except Exception as e:
        st.error(f"Erro ao carregar os dados da planilha: {e}")
        return None

# 5. INTERFACE
col_logo, col_busca = st.columns([1, 4])
with col_logo:
    if base64_logo:
        st.image("logo", width=150)
    else:
        st.subheader("PARENTE ANDRADE")

df = carregar_dados()

if df is not None:
    busca = st.text_input("", placeholder="🔍 O que deseja consultar? (SC, Cotação, Pedido...)", label_visibility="collapsed")
    
    df_display = df.copy()
    if busca:
        mask = df_display.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df_display[mask]

    # Ordem das colunas: SC -> Cotação -> Pedido
    cols_ref = [
        "STATUS", "N° da SC", "Num. Cotacao", "Código Cotação", "N° PC", 
        "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", 
        " Prc Unitario", " Vlr.Total", "Data Emissao"
    ]
    cols_finais = [c for c in cols_ref if c in df_display.columns]

    st.dataframe(df_display[cols_finais], use_container_width=True, hide_index=True)

st.markdown("<p class='footer-text'>PARENTE ANDRADE | Suprimentos</p>", unsafe_allow_html=True)
