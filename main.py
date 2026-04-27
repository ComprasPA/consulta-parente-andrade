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

# 3. CSS (DESIGN PADRÃO CONGELADO)
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
    busca = st.text_input("", placeholder="🔍 Buscar na Planilha de Pedidos (PC)...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. CARREGAMENTO EXCLUSIVO DA ABA PC
@st.cache_data(ttl=600)
def carregar_aba_pc_exclusiva():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        # Carrega apenas a primeira aba (Aba 0 - Pedidos PC)
        df = pd.read_excel(URL, sheet_name=0, dtype=str).fillna('')
        # Limpa espaços nos nomes das colunas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Formatação de Datas dd/mm/yy imediata
        for col in df.columns:
            if any(d in col.upper() for d in ["DATA", "DT "]):
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%y').fillna('')
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar a aba de Pedidos: {e}")
        return pd.DataFrame()

df_pc = carregar_aba_pc_exclusiva()

# Colunas oficiais do painel
COL_ORDEM = ["STATUS", "Numero da SC", "Numero Pedido", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega"]

# 6. LÓGICA DE BUSCA EXCLUSIVA
if busca:
    t = busca.lower().strip()
    
    # Filtra apenas na base de Pedidos
    df_res = df_pc[df_pc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]

    if not df_res.empty:
        # Garantia de Colunas do Painel
        for c in COL_ORDEM:
            if c not in df_res.columns: df_res[c] = ""
        
        # Exibe apenas as colunas solicitadas e remove duplicatas
        df_exibir = df_res[COL_ORDEM].drop_duplicates()
        
        st.markdown(f'<div class="status-box">🟢 Exibindo informações exclusivas da Planilha PC</div>', unsafe_allow_html=True)
        
        # Download do Excel
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_exibir.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL (PC)", out.getvalue(), "Portal_Pedidos_PC.xlsx")
        
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum registro de Pedido encontrado para: {busca}")
else:
    st.info("💡 Digite o termo de busca. O sistema está configurado para pesquisar APENAS na aba de Pedidos (PC).")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
