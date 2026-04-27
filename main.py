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

# 3. CSS
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    .portal-title {{ color: #000000 !important; font-size: 40px !important; font-weight: bold !important; text-align: center !important; margin: 0 !important; }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{ background-color: #ffffff; padding: 2px 10px !important; border-radius: 8px; border: 2px solid #478c3b; }}
    [data-testid="column"] {{ display: flex; align-items: center; justify-content: center; }}
    .stDownloadButton button {{ background-color: #f2a933 !important; color: white !important; font-weight: bold !important; }}
    .status-box {{ background-color: #478c3b; color: white; padding: 12px 20px; border-radius: 10px; font-weight: bold; font-size: 18px; margin-bottom: 15px; }}
    </style>
    """, unsafe_allow_html=True)

# 4. TRATAMENTO DE DADOS E NORMALIZAÇÃO DE CHAVES (PROCV)
def tratar_dados(df):
    # Formatação de Datas
    cols_dt = ["Data Emissao", "Dt Liberacao", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]
    for col in cols_dt:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%y').fillna(df[col]).replace(['NaT', 'nan'], '')
    
    # Formatação de Produto
    if "Produto" in df.columns:
        df["Produto"] = df["Produto"].astype(str).str.split('.').str[0].str.strip().str.zfill(10).replace('0000000nan', '')
    
    # Normalização de Números para o PROCV (Remover decimais e espaços)
    for col in df.columns:
        if any(x in col.upper() for x in ["NUMERO", "N°", "SC", "PC", "PEDIDO", "COTACAO"]):
            df[col] = df[col].astype(str).str.split('.').str[0].str.strip().replace('nan', '')
            
    return df

# 5. CARREGAMENTO COM PROCV ENTRE GUIAS
@st.cache_data(ttl=600, show_spinner="Sincronizando e Vinculando bases...")
def carregar_e_vincular_bases():
    URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        
        # 1. Carrega Guia Principal (PC)
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc = tratar_dados(df_pc)
        
        # 2. Carrega Guia Secundária (SC)
        df_sc = pd.DataFrame()
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        
        if aba_sc_nome:
            df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('')
            df_sc = tratar_dados(df_sc)
            
            # --- LÓGICA DE PROCV (MERGE) ---
            # Identifica as colunas de ligação
            col_link_pc = "N° da SC" if "N° da SC" in df_pc.columns else "Numero da SC"
            col_link_sc = "Numero da SC" if "Numero da SC" in df_sc.columns else "N° da SC"
            
            if col_link_pc in df_pc.columns and col_link_sc in df_sc.columns:
                # Puxa a cotação da guia SC para a guia PC baseada no número da SC
                col_cot_sc = "Num. Cotacao" if "Num. Cotacao" in df_sc.columns else "Numero da Cotacao"
                
                if col_cot_sc in df_sc.columns:
                    # Cria um dicionário de cotações { 'numero_sc': 'numero_cotacao' }
                    mapeamento_cotacao = df_sc.set_index(col_link_sc)[col_cot_sc].to_dict()
                    
                    # Preenche a coluna de cotação na PC onde estiver vazio
                    df_pc['Num. Cotacao'] = df_pc.apply(
                        lambda row: mapeamento_cotacao.get(row[col_link_pc], row.get('Num. Cotacao', '')) 
                        if not str(row.get('Num. Cotacao', '')).strip() or row.get('Num. Cotacao') == ''
                        else row.get('Num. Cotacao'), axis=1
                    )
            
        return df_pc, df_sc
    except Exception as e:
        st.error(f"Erro no processamento: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_e_vincular_bases()

COLUNAS_PADRAO = [
    "STATUS", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", 
    "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", 
    "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", 
    "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "
]

# 6. CABEÇALHO
col_logo, col_titulo, col_busca = st.columns([1, 5, 2])
with col_logo:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:130px;">', unsafe_allow_html=True)
with col_titulo:
    st.markdown('<p class="portal-title">Portal Gestão de Compras Parente Andrade</p>', unsafe_allow_html=True)
with col_busca:
    busca = st.text_input("", placeholder="🔍 Buscar...", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 10px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 7. BUSCA INTEGRADA
if busca:
    termo = busca.lower().strip()
    mask_pc = df_pc.apply(lambda row: row.astype(str).str.lower().str.contains(termo, na=False).any(), axis=1)
    df_res = df_pc[mask_pc].copy()
    origem = "Protheus PC (Com dados vinculados da SC)"

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
        
        c_down, _ = st.columns([1, 3])
        with c_down:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                df_final.to_excel(wr, index=False)
            st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_PA_Integrado.xlsx")

        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhuma informação para: '{busca}'")
else:
    st.info("💡 Digite um termo acima para pesquisar.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Suprimentos</p>", unsafe_allow_html=True)
