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

# 3. CSS PARA ALINHAMENTO MILIMÉTRICO E RETÂNGULO DO TÍTULO
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    
    [data-testid="stHorizontalBlock"] {{
        align-items: center !important;
        display: flex !important;
    }}

    /* Estilização do Retângulo que cerca o Título */
    .portal-title-container {{
        background-color: #ffffff; /* Fundo sólido para o retângulo */
        border: 2px solid #478c3b; /* Borda verde acompanhando a identidade */
        border-radius: 12px;
        padding: 10px 30px;
        display: inline-block;
        width: 100%;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}

    .portal-title {{ 
        color: #000000 !important; 
        font-size: 40px !important; 
        font-weight: bold !important; 
        text-align: center !important; 
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.1;
        white-space: nowrap;
    }}

    /* Barra de Busca (Retornada ao Padrão) */
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; 
        padding: 0px 10px !important; 
        border-radius: 8px; 
        border: 2px solid #478c3b;
        margin-top: 0px !important;
    }}

    .stDownloadButton button {{ 
        background-color: #f2a933 !important; color: white !important; font-weight: bold !important; 
    }}
    
    .status-box {{
        background-color: #478c3b; color: white; padding: 12px 20px;
        border-radius: 10px; font-weight: bold; font-size: 18px;
    }}

    @media (max-width: 1200px) {{
        .portal-title {{ font-size: 30px !important; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO EM LINHA ÚNICA
col_logo, col_titulo, col_busca = st.columns([1.2, 5, 2.3])

with col_logo:
    if base64_logo: 
        st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:140px; vertical-align: middle;">', unsafe_allow_html=True)
    else:
        st.write("### PA")

with col_titulo:
    # Título envolto pelo retângulo (container) solicitado
    st.markdown('''
        <div class="portal-title-container">
            <p class="portal-title">Portal Gestão de Compras Parente Andrade</p>
        </div>
    ''', unsafe_allow_html=True)

with col_busca:
    busca = st.text_input("", placeholder="🔍 Buscar...", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 10px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# 5. TRATAMENTO DE DADOS
def tratar_dados(df):
    cols_dt = ["Data Emissao", "Dt Liberacao", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]
    for col in cols_dt:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%y').fillna(df[col]).replace(['NaT', 'nan'], '')
    
    if "Produto" in df.columns:
        df["Produto"] = df["Produto"].astype(str).str.split('.').str[0].str.strip().str.zfill(10).replace('0000000nan', '')
    
    for col in df.columns:
        if any(x in col.upper() for x in ["NUMERO", "N°", "SC", "PC", "PEDIDO", "COTACAO"]):
            df[col] = df[col].astype(str).str.split('.').str[0].str.strip().replace('nan', '')
    return df

@st.cache_data(ttl=600)
def carregar_e_vincular_bases():
    URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        df_pc = tratar_dados(pd.read_excel(excel, sheet_name=0, dtype=str).fillna(''))
        
        aba_sc = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.DataFrame()
        if aba_sc:
            df_sc = tratar_dados(pd.read_excel(excel, sheet_name=aba_sc, dtype=str).fillna(''))
            link_pc, link_sc = "N° da SC", "Numero da SC"
            if link_pc in df_pc.columns and link_sc in df_sc.columns:
                map_cot = df_sc.set_index(link_sc)["Num. Cotacao"].to_dict()
                df_pc['Num. Cotacao'] = df_pc.apply(lambda r: map_cot.get(r[link_pc], r.get('Num. Cotacao', '')), axis=1)
        return df_pc, df_sc
    except: return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_e_vincular_bases()

COLUNAS_PADRAO = ["STATUS", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]

# 6. BUSCA E EXIBIÇÃO
if busca:
    termo = busca.lower().strip()
    mask_pc = df_pc.apply(lambda row: row.astype(str).str.lower().str.contains(termo, na=False).any(), axis=1)
    df_res = df_pc[mask_pc].copy()
    origem = "Protheus PC (Vinculado)"

    if df_res.empty and not df_sc.empty:
        mask_sc = df_sc.apply(lambda row: row.astype(str).str.lower().str.contains(termo, na=False).any(), axis=1)
        df_res = df_sc[mask_sc].copy()
        origem = "Protheus SC"
        df_res = df_res.rename(columns={"Numero da SC": "N° da SC", "Numero Pedido": "N° PC"})

    if not df_res.empty:
        for col in COLUNAS_PADRAO:
            if col not in df_res.columns: df_res[col] = ""
        df_final = df_res[COLUNAS_PADRAO]
        
        st.markdown(f'<div class="status-box">🟢 {origem} - {len(df_res)} registros</div>', unsafe_allow_html=True)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_final.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_PA.xlsx")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
else:
    st.info("💡 Digite um termo acima para pesquisar.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Suprimentos</p>", unsafe_allow_html=True)
