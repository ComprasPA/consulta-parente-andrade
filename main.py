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
    .header-wrapper {{
        border: 2px solid #478c3b; border-radius: 10px; padding: 15px 25px;
        background-color: #ffffff; display: flex; align-items: center;
        justify-content: space-between; margin-top: 10px; margin-bottom: 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}
    .portal-title {{ color: #000000 !important; font-size: 35px !important; font-weight: bold !important; margin: 0 !important; }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 0px 10px !important; 
        border-radius: 8px; border: 2px solid #478c3b !important; margin: 0 !important;
    }}
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
    busca = st.text_input("", placeholder="🔍 Digite Numero da SC ou Pedido...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. MOTOR DE BUSCA COM PRIORIDADE SEQUENCIAL (PC > SC)
def normalizar(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']: return ""
    return str(val).split('.')[0].strip().lstrip('0')

@st.cache_data(ttl=600)
def carregar_bases():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        # Carrega PC
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]
        # Carrega SC
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [str(c).strip() for c in df_sc.columns]
        return df_pc, df_sc
    except:
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_bases()

COL_PAINEL = ["STATUS", "Numero da SC", "Numero Pedido", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega"]

# 6. LÓGICA DE EXIBIÇÃO POR PRIORIDADE
if busca:
    t = busca.lower().strip()
    
    # BUSCA 1: Tenta localizar na planilha soberana (PC)
    res_pc = df_pc[df_pc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
    
    if not res_pc.empty:
        # Se achou na PC, mostra APENAS os dados da PC (Soberania)
        df_final = res_pc.copy()
        origem = "Planilha de Pedidos (PC)"
    else:
        # BUSCA 2: Se não achou nada na PC, tenta localizar na SC
        res_sc = df_sc[df_sc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
        if not res_sc.empty:
            df_final = res_sc.copy()
            # Inteligência de Status para itens que só existem na SC
            def status_sc(row):
                cot = str(row.get('Num. Cotacao', '')).strip()
                return "EM COTAÇÃO" if cot != "" and cot.lower() != "nan" else "SC ABERTA"
            df_final['STATUS'] = df_final.apply(status_sc, axis=1)
            origem = "Planilha de Solicitações (SC)"
        else:
            df_final = pd.DataFrame()

    if not df_final.empty:
        # Formatação de Datas
        for col in df_final.columns:
            if any(d in col.upper() for d in ["DATA", "DT "]):
                df_final[col] = pd.to_datetime(df_final[col], errors='coerce').dt.strftime('%d/%m/%y').fillna('')
        
        # Garantir colunas do painel
        for c in COL_PAINEL:
            if c not in df_final.columns: df_final[c] = ""
        
        df_exibir = df_final[COL_PAINEL].drop_duplicates()
        
        st.markdown(f'<div class="status-box">🟢 Exibindo dados de: {origem}</div>', unsafe_allow_html=True)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_exibir.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_Compras_PA.xlsx")
        
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum registro encontrado para: {busca}")
else:
    st.info("💡 Digite o termo de busca. O sistema pesquisa primeiro na aba PC e, caso não encontre, busca na aba SC.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
