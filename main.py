import streamlit as st
import pandas as pd
import base64
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Portal Gestão de Compras | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. FUNÇÃO LOGO
@st.cache_data(ttl=86400)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

base64_logo = get_base64_logo()

# 3. CSS (DESIGN LIMPO)
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    
    .header-wrapper {{
        border: 2px solid #478c3b;
        border-radius: 10px;
        padding: 15px 25px;
        background-color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 10px;
        margin-bottom: 20px;
    }}

    .portal-title {{ 
        color: #000000 !important; font-size: 40px !important; font-weight: bold !important; 
        text-align: center !important; margin: 0 !important; line-height: 1.1; white-space: nowrap;
    }}

    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 0px 10px !important; 
        border-radius: 8px; border: 2px solid #478c3b !important; margin: 0 !important;
    }}

    .stDownloadButton button {{ background-color: #f2a933 !important; color: white !important; font-weight: bold !important; }}
    .status-box {{ background-color: #478c3b; color: white; padding: 12px 20px; border-radius: 10px; font-weight: bold; font-size: 18px; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
st.markdown('<div class="header-wrapper">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.2, 5, 2.3])
with c1:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:140px;">', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="portal-title">Portal Gestão de Compras Parente Andrade</p>', unsafe_allow_html=True)
with c3:
    busca = st.text_input("", placeholder="🔍 Buscar...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. TRATAMENTO E VÍNCULO (LIMPEZA TOTAL DE COLUNAS)
def preparar_dados(df):
    # Transforma nomes de colunas em MAIÚSCULAS e remove espaços
    df.columns = [str(c).strip().upper() for c in df.columns]
    for col in df.columns:
        df[col] = df[col].astype(str).str.split('.').str[0].str.strip().replace(['nan', 'NaT', 'None'], '')
    return df

@st.cache_data(ttl=600)
def carregar_e_vincular():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        # Carrega aba de Pedidos (PC)
        df_pc = preparar_dados(pd.read_excel(excel, sheet_name=0, dtype=str).fillna(''))
        
        # Procura a aba SC (Solicitações)
        nome_aba_sc = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.DataFrame()

        if nome_aba_sc:
            df_sc = preparar_dados(pd.read_excel(excel, sheet_name=nome_aba_sc, dtype=str).fillna(''))
            
            # Encontra as colunas de ligação (Chaves) de forma flexível (em maiúsculas)
            col_chave_pc = next((c for c in df_pc.columns if "SC" in c or "SOLICIT" in c), None)
            col_chave_sc = next((c for c in df_sc.columns if "SC" in c or "SOLICIT" in c), None)
            
            # Valor SCM
            col_val_scm = next((c for c in df_sc.columns if "SCM" in c), col_chave_sc)

            if col_chave_pc and col_chave_sc:
                # Cria mapa de SCM
                mapa_scm = df_sc.drop_duplicates(subset=[col_chave_sc]).set_index(col_chave_sc)[col_val_scm].to_dict()
                df_pc['SCM_VINC'] = df_pc[col_chave_pc].map(mapa_scm).fillna('')
                
                # Mapa de Cotação
                col_cot_sc = next((c for c in df_sc.columns if "COT" in c), None)
                if col_cot_sc:
                    mapa_cot = df_sc.drop_duplicates(subset=[col_chave_sc]).set_index(col_chave_sc)[col_cot_sc].to_dict()
                    # Coluna de cotação na PC
                    col_cot_pc = next((c for c in df_pc.columns if "COT" in c), "NUM. COTACAO")
                    df_pc[col_cot_pc] = df_pc.apply(
                        lambda r: mapa_cot.get(r[col_chave_pc], r.get(col_cot_pc, '')) 
                        if not str(r.get(col_cot_pc, '')).strip() else r.get(col_cot_pc), axis=1
                    )
        return df_pc, df_sc
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_e_vincular()

# MAPEAMENTO PARA EXIBIÇÃO AMIGÁVEL
COLUNAS_PADRAO = [
    "STATUS", "SCM_VINC", "N° DA SC", "NUM. COTACAO", "N° PC", "CC", "NOME FORNECEDOR", 
    "PRODUTO", "DESCRICAO", "UM", "QNT", " PRC UNITARIO", " VLR.TOTAL", 
    "DATA EMISSAO", "DT LIBERACAO", "DT ENVIO", "CONDICAO PGO", 
    "DT PGO (AVISTA)", "DT PREV DE ENTREGA", "DT ENTREGA "
]

# 6. EXIBIÇÃO
if busca:
    termo = busca.upper().strip()
    df_res = df_pc[df_pc.apply(lambda r: r.astype(str).str.upper().str.contains(termo).any(), axis=1)].copy()
    
    if not df_res.empty:
        # Renomeia colunas para o padrão de visualização
        df_res = df_res.rename(columns={"SCM_VINC": "SCM"})
        # Garante que as colunas existam
        for col in COLUNAS_PADRAO:
            c_upper = col.upper()
            if c_upper not in df_res.columns: df_res[c_upper] = ""
        
        st.dataframe(df_res[[c.upper() for c in COLUNAS_PADRAO if c != "SCM_VINC"] + ["SCM"]], use_container_width=True, hide_index=True)
else:
    st.info("💡 Digite um termo para pesquisar.")
