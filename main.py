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

# 3. CSS (DESIGN PADRÃO)
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    div[data-testid="column"], div[data-testid="stHorizontalBlock"] {{
        border: none !important; box-shadow: none !important; background-color: transparent !important;
    }}
    .header-wrapper {{
        border: 2px solid #478c3b; border-radius: 10px; padding: 15px 25px;
        background-color: #ffffff; display: flex; align-items: center;
        justify-content: space-between; margin-top: 10px; margin-bottom: 20px;
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
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
st.markdown('<div class="header-wrapper">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.2, 5, 2.3])
with c1:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:140px; vertical-align: middle;">', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="portal-title">Portal Gestão de Compras Parente Andrade</p>', unsafe_allow_html=True)
with c3:
    busca = st.text_input("", placeholder="🔍 Buscar (SCM, CC, Produto, SC...)", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 0px; margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# 5. TRATAMENTO DE DADOS
def tratar_dados(df):
    cols_dt = ["Data Emissao", "Dt Liberacao", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]
    for col in cols_dt:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%y').fillna(df[col]).replace(['NaT', 'nan', 'None'], '')
    if "Produto" in df.columns:
        df["Produto"] = df["Produto"].astype(str).str.split('.').str[0].str.strip().str.zfill(10).replace('0000000nan', '')
    for col in df.columns:
        if any(x in col.upper() for x in ["NUMERO", "N°", "SC", "PC", "PEDIDO", "COTACAO", "CC", "SCM"]):
            df[col] = df[col].astype(str).str.split('.').str[0].str.strip().replace(['nan', 'None'], '')
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
            
            # CHAVES DE LIGAÇÃO
            link_pc, link_sc = "N° da SC", "Numero da SC"
            
            if link_pc in df_pc.columns and link_sc in df_sc.columns:
                # 1. Trazer Cotação e SCM para a aba PC (VLOOKUP PC <- SC)
                df_sc_map = df_sc.drop_duplicates(subset=[link_sc]).set_index(link_sc)
                map_cot = df_sc_map["Num. Cotacao"].to_dict() if "Num. Cotacao" in df_sc_map.columns else {}
                map_scm = df_sc_map["SCM"].to_dict() if "SCM" in df_sc_map.columns else {}
                
                df_pc['Num. Cotacao'] = df_pc[link_pc].map(map_cot).fillna(df_pc.get('Num. Cotacao', ''))
                df_pc['SCM_INTERNO'] = df_pc[link_pc].map(map_scm)
                
                # 2. Trazer Status e Datas do Pedido para a aba SC (VLOOKUP SC <- PC)
                # Criamos um mapa das informações que costumam faltar na SC
                df_pc_map = df_pc.drop_duplicates(subset=[link_pc]).set_index(link_pc)
                cols_para_vincular = ["STATUS", "N° PC", "Data Emissao", "DT entrega ", "DT Pgo (AVISTA)", "Nome Fornecedor"]
                
                for col in cols_para_vincular:
                    if col in df_pc_map.columns:
                        map_pc_info = df_pc_map[col].to_dict()
                        # Só preenche na SC se a coluna original estiver vazia
                        df_sc[col] = df_sc.apply(
                            lambda r: map_pc_info.get(r[link_sc], r.get(col, '')) if not str(r.get(col, '')).strip() else r.get(col), 
                            axis=1
                        )
            
        return df_pc, df_sc
    except: return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_e_vincular_bases()

COLUNAS_PADRAO = ["STATUS", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]

# 6. LÓGICA DE BUSCA
if busca:
    termo = busca.lower().strip()
    
    def filtrar_df(df, t):
        # Busca em todas as colunas (incluindo SCM_INTERNO se houver)
        mask = df.apply(lambda row: row.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)
        # Prioridade para CC se for número
        if t.isdigit() and "CC" in df.columns:
            mask_cc = df["CC"].str.contains(t, na=False)
            if mask_cc.any(): mask = mask_cc
        return df[mask].copy()

    # Tenta primeiro na aba de Pedidos (PC)
    df_res = filtrar_df(df_pc, termo)
    origem = "Protheus PC (Vinculado)"

    # Se não achar na PC, busca na SC (que agora já recebeu o "PROCV" da PC)
    if df_res.empty and not df_sc.empty:
        df_res = filtrar_df(df_sc, termo)
        origem = "Protheus SC (Info. Pedido)"
        if "Numero da SC" in df_res.columns:
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
        st.warning(f"Nenhum registro encontrado para: '{busca}'")
else:
    st.info("💡 Digite um termo (SCM, CC, SC ou Produto) para pesquisar.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
