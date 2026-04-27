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
        color: #000000 !important; 
        font-size: 40px !important; 
        font-weight: bold !important; 
        text-align: center !important; 
        margin: 0 !important;
        line-height: 1.1;
        white-space: nowrap;
    }}

    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; 
        padding: 0px 10px !important; 
        border-radius: 8px; 
        border: 2px solid #478c3b !important;
        margin: 0 !important;
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
    if base64_logo: 
        st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:140px; vertical-align: middle;">', unsafe_allow_html=True)

with c2:
    st.markdown('<p class="portal-title">Portal Gestão de Compras Parente Andrade</p>', unsafe_allow_html=True)

with c3:
    busca = st.text_input("", placeholder="🔍 Buscar...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 0px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# 5. TRATAMENTO DE DADOS (CORREÇÃO SCM)
def tratar_dados(df):
    cols_dt = ["Data Emissao", "Dt Liberacao", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]
    for col in cols_dt:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%y').fillna(df[col]).replace(['NaT', 'nan'], '')
    
    if "Produto" in df.columns:
        df["Produto"] = df["Produto"].astype(str).str.split('.').str[0].str.strip().str.zfill(10).replace('0000000nan', '')
    
    # Limpeza de strings e remoção de .0 de IDs
    for col in df.columns:
        if any(x in col.upper() for x in ["NUMERO", "N°", "SC", "PC", "PEDIDO", "COTACAO", "SCM"]):
            df[col] = df[col].astype(str).str.split('.').str[0].str.strip().replace('nan', '')
    return df

@st.cache_data(ttl=600)
def carregar_e_vincular_bases():
    URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        df_pc = tratar_dados(pd.read_excel(excel, sheet_name=0, dtype=str).fillna(''))
        
        # Identifica a aba SC (Solicitação de Compras)
        aba_sc_name = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        
        if aba_sc_name:
            df_sc = tratar_dados(pd.read_excel(excel, sheet_name=aba_sc_name, dtype=str).fillna(''))
            
            # Normalização de nomes para garantir o vínculo
            col_sc_pc = "N° da SC" if "N° da SC" in df_pc.columns else "Numero da SC"
            col_sc_sc = "Numero da SC" if "Numero da SC" in df_sc.columns else "N° da SC"
            
            if col_sc_pc in df_pc.columns and col_sc_sc in df_sc.columns:
                # Criar dicionário de SCM e Cotação baseado na SC
                # Verificamos se as colunas existem na aba SC antes de mapear
                cols_to_map = [c for c in ["Num. Cotacao", "SCM"] if c in df_sc.columns]
                
                if cols_to_map:
                    map_data = df_sc.drop_duplicates(subset=[col_sc_sc]).set_index(col_sc_sc)[cols_to_map].to_dict('index')
                    
                    def vincular_scm(row):
                        key = row[col_sc_pc]
                        if key in map_data:
                            for c in cols_to_map:
                                row[c] = map_data[key].get(c, '')
                        return row

                    df_pc = df_pc.apply(vincular_scm, axis=1)
            
            return df_pc, df_sc
        return df_pc, pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_e_vincular_bases()

# ORDEM DAS COLUNAS SOLICITADA
COLUNAS_PADRAO = [
    "STATUS", "SCM", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", 
    "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", 
    "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", 
    "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "
]

# 6. BUSCA E EXIBIÇÃO
if busca:
    termo = busca.lower().strip()
    mask_pc = df_pc.apply(lambda row: row.astype(str).str.lower().str.contains(termo, na=False).any(), axis=1)
    df_res = df_pc[mask_pc].copy()
    origem = "Protheus PC (Vinculado)"

    # Se não achar no PC, busca direto no SC
    if df_res.empty and not df_sc.empty:
        mask_sc = df_sc.apply(lambda row: row.astype(str).str.lower().str.contains(termo, na=False).any(), axis=1)
        df_res = df_sc[mask_sc].copy()
        origem = "Protheus SC"
        # Garante nomes compatíveis para exibição
        if "Numero da SC" in df_res.columns: df_res = df_res.rename(columns={"Numero da SC": "N° da SC"})
        if "Numero Pedido" in df_res.columns: df_res = df_res.rename(columns={"Numero Pedido": "N° PC"})

    if not df_res.empty:
        # Garante que todas as colunas padrão existam no resultado
        for col in COLUNAS_PADRAO:
            if col not in df_res.columns: df_res[col] = ""
        
        df_final = df_res[COLUNAS_PADRAO]
        st.markdown(f'<div class="status-box">🟢 {origem} - {len(df_res)} registros encontrados</div>', unsafe_allow_html=True)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_final.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_Gestao_PA.xlsx")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
else:
    st.info("💡 Digite um termo (Fornecedor, SC, PC, Descrição) para pesquisar.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Suprimentos</p>", unsafe_allow_html=True)
