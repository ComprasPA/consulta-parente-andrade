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

# 3. CSS (MOLDURA ÚNICA E LIMPA)
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    
    div[data-testid="column"], div[data-testid="stHorizontalBlock"] {{
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }}

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
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
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

    @media (max-width: 1200px) {{ .portal-title {{ font-size: 30px !important; }} }}
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

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 0px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# 5. TRATAMENTO E INTEGRAÇÃO (FOCO NO SCM)
def tratar_basico(df):
    for col in df.columns:
        df[col] = df[col].astype(str).str.split('.').str[0].str.strip().replace(['nan', 'NaT', 'None'], '')
    return df

@st.cache_data(ttl=600)
def carregar_dados():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        df_pc = tratar_basico(pd.read_excel(excel, sheet_name=0, dtype=str).fillna(''))
        
        aba_sc_name = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.DataFrame()
        
        if aba_sc_name:
            df_sc = tratar_basico(pd.read_excel(excel, sheet_name=aba_sc_name, dtype=str).fillna(''))
            
            # Identificação das colunas de vínculo
            # Na PC geralmente é 'N° da SC'. Na aba SC, pode ser 'Numero da SC' ou 'Solicitação'
            col_link_pc = "N° da SC" if "N° da SC" in df_pc.columns else "Numero da SC"
            col_link_sc = "Numero da SC" if "Numero da SC" in df_sc.columns else "Solicitação"
            
            # Coluna que de fato contém o código SCM (ex: SCM001234)
            # Se não houver coluna 'SCM', usamos a própria coluna de Solicitação da aba SC
            col_dado_scm = "SCM" if "SCM" in df_sc.columns else col_link_sc

            if col_link_pc in df_pc.columns and col_link_sc in df_sc.columns:
                # Criar dicionário de mapeamento
                mapa_scm = df_sc.drop_duplicates(subset=[col_link_sc]).set_index(col_link_sc)[col_dado_scm].to_dict()
                mapa_cot = df_sc.drop_duplicates(subset=[col_link_sc]).set_index(col_link_sc).get("Num. Cotacao", pd.Series(dtype=str)).to_dict()

                # Injetar os dados na PC
                df_pc['SCM'] = df_pc[col_link_pc].map(mapa_scm).fillna('')
                # Se a cotação estiver vazia na PC, busca na SC
                df_pc['Num. Cotacao'] = df_pc.apply(
                    lambda r: mapa_cot.get(r[col_link_pc], r.get('Num. Cotacao', '')) 
                    if not r.get('Num. Cotacao') else r.get('Num. Cotacao'), axis=1
                )
        
        return df_pc, df_sc
    except Exception as e:
        st.error(f"Erro ao vincular SCM: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_dados()

COLUNAS_PADRAO = [
    "STATUS", "SCM", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", 
    "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", 
    "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", 
    "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "
]

# 6. BUSCA E EXIBIÇÃO
if busca:
    termo = busca.lower()
    df_res = df_pc[df_pc.apply(lambda r: r.astype(str).str.lower().str.contains(termo).any(), axis=1)].copy()
    origem = "Protheus PC (Vinculado)"

    if df_res.empty and not df_sc.empty:
        df_res = df_sc[df_sc.apply(lambda r: r.astype(str).str.lower().str.contains(termo).any(), axis=1)].copy()
        origem = "Protheus SC"
        # Ajuste de nomes para exibição caso a busca venha da aba SC
        if "Solicitação" in df_res.columns: df_res['SCM'] = df_res['Solicitação']
        if "Numero da SC" in df_res.columns: df_res['N° da SC'] = df_res['Numero da SC']

    if not df_res.empty:
        for c in COLUNAS_PADRAO:
            if c not in df_res.columns: df_res[c] = ""
        
        df_final = df_res[COLUNAS_PADRAO]
        st.markdown(f'<div class="status-box">🟢 {origem} - {len(df_final)} registros</div>', unsafe_allow_html=True)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_final.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR RESULTADOS", out.getvalue(), "Portal_PA_SCM.xlsx")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
else:
    st.info("💡 Digite o Fornecedor, SC ou SCM para pesquisar.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Suprimentos</p>", unsafe_allow_html=True)
