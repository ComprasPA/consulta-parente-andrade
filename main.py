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
    }}
    .portal-title {{ 
        color: #000000 !important; font-size: 40px !important; font-weight: bold !important; 
        text-align: center !important; margin: 0 !important;
    }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 0px 10px !important; 
        border-radius: 8px; border: 2px solid #478c3b !important;
    }}
    .status-box {{ background-color: #478c3b; color: white; padding: 12px 20px; border-radius: 10px; font-weight: bold; }}
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

# 5. TRATAMENTO E VÍNCULO (CORREÇÃO DO PROCV)
def limpar_id(texto):
    """Limpa IDs para garantir que a comparação funcione (remove .0, espaços e nulos)"""
    if pd.isna(texto) or str(texto).lower() in ['nan', 'none', '']: return ""
    return str(texto).split('.')[0].strip()

def tratar_datas(df):
    cols_dt = ["Data Emissao", "Dt Liberacao", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]
    for col in cols_dt:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%y').fillna('').replace(['NaT', 'nan'], '')
    return df

@st.cache_data(ttl=600)
def carregar_dados_consolidados():
    URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        
        # Carregar Aba PC (Pedidos)
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc = tratar_datas(df_pc)
        
        # Carregar Aba SC (Solicitações)
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc = tratar_datas(df_sc)

        # Padronização de Colunas Chave para o Vínculo
        link_pc = "N° da SC"
        link_sc = "Numero da SC"

        if link_pc in df_pc.columns and link_sc in df_sc.columns:
            # Criar IDs limpos para comparação
            df_pc['ID_LINK'] = df_pc[link_pc].apply(limpar_id)
            df_sc['ID_LINK'] = df_sc[link_sc].apply(limpar_id)

            # --- PROCV: Trazer dados da SC para a PC ---
            sc_info = df_sc.drop_duplicates('ID_LINK').set_index('ID_LINK')
            map_cot = sc_info['Num. Cotacao'].to_dict() if 'Num. Cotacao' in sc_info.columns else {}
            map_scm = sc_info['SCM'].to_dict() if 'SCM' in sc_info.columns else {}
            
            df_pc['Num. Cotacao'] = df_pc.apply(lambda r: map_cot.get(r['ID_LINK'], r.get('Num. Cotacao', '')), axis=1)
            df_pc['SCM_BUSCA'] = df_pc['ID_LINK'].map(map_scm)

            # --- PROCV: Trazer dados da PC para a SC ---
            pc_info = df_pc.drop_duplicates('ID_LINK').set_index('ID_LINK')
            # Colunas que a SC deve "sugar" da PC para não ficar em branco
            cols_vinc = ["STATUS", "N° PC", "Data Emissao", "DT entrega ", "Nome Fornecedor", "CC"]
            
            for col in cols_vinc:
                if col in pc_info.columns:
                    map_pc = pc_info[col].to_dict()
                    # Preenche apenas se a SC estiver vazia naquelas colunas
                    df_sc[col] = df_sc.apply(
                        lambda r: map_pc.get(r['ID_LINK'], r.get(col, '')) if not str(r.get(col, '')).strip() else r.get(col),
                        axis=1
                    )
            
            # Ajuste de nomes de colunas para exibição uniforme
            if "Numero da SC" in df_sc.columns: df_sc = df_sc.rename(columns={"Numero da SC": "N° da SC"})
            if "Numero Pedido" in df_sc.columns: df_sc = df_sc.rename(columns={"Numero Pedido": "N° PC"})

        return df_pc, df_sc
    except: return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_dados_consolidados()

COLUNAS_PADRAO = ["STATUS", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]

# 6. BUSCA E EXIBIÇÃO
if busca:
    termo = busca.lower().strip()
    
    def filtrar(df):
        return df[df.apply(lambda r: r.astype(str).str.lower().str.contains(termo, na=False).any(), axis=1)].copy()

    # Prioridade 1: Buscar na base de Pedidos (PC) já vinculada
    df_res = filtrar(df_pc)
    origem = "Pedidos (PC)"

    # Prioridade 2: Se não achou no Pedido, busca na Solicitação (SC)
    if df_res.empty and not df_sc.empty:
        df_res = filtrar(df_sc)
        origem = "Solicitações (SC)"

    if not df_res.empty:
        # Garante que todas as colunas do padrão existam
        for col in COLUNAS_PADRAO:
            if col not in df_res.columns: df_res[col] = ""
            
        df_final = df_res[COLUNAS_PADRAO].fillna('')
        st.markdown(f'<div class="status-box">🟢 Localizado em: {origem} ({len(df_res)} itens)</div>', unsafe_allow_html=True)
        
        # Download Excel
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_final.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR RESULTADO", out.getvalue(), "Busca_Portal.xlsx")
        
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum dado encontrado para: {busca}")
else:
    st.info("💡 Digite SC, SCM, Fornecedor ou Produto para pesquisar.")
