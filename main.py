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

# 3. CSS PADRÃO
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
    .portal-title {{ color: #000000 !important; font-size: 40px !important; font-weight: bold !important; margin: 0 !important; }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 0px 10px !important; 
        border-radius: 8px; border: 2px solid #478c3b !important;
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
    busca = st.text_input("", placeholder="🔍 Digite SC, SCM, Produto ou Fornecedor...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. MOTOR DE CONSOLIDAÇÃO (PROCV REFORMULADO E NORMALIZADO)
def normalizar_id(val):
    """Remove zeros à esquerda, decimais e espaços para garantir o vínculo"""
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']: return ""
    # Remove .0, tira espaços e remove zeros à esquerda (ex: 000123 -> 123)
    return str(val).split('.')[0].strip().lstrip('0')

@st.cache_data(ttl=600)
def carregar_e_consolidar():
    URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()

        # Criação de chaves normatizadas para o vínculo
        df_pc['LINK_NORMAL'] = df_pc['N° da SC'].apply(normalizar_id)
        df_sc['LINK_NORMAL'] = df_sc['Numero da SC'].apply(normalizar_id)

        # 1. Cruzamento SC -> PC (Trazer Cotação e SCM para os Pedidos)
        # Removemos duplicatas da chave para não gerar linhas extras no merge
        sc_vlookup = df_sc[['LINK_NORMAL', 'Num. Cotacao', 'SCM']].drop_duplicates('LINK_NORMAL')
        df_pc = df_pc.merge(sc_vlookup, on='LINK_NORMAL', how='left', suffixes=('', '_extra'))
        
        # Preenche se estiver vazio
        if 'Num. Cotacao_extra' in df_pc.columns:
            df_pc['Num. Cotacao'] = df_pc['Num. Cotacao'].replace('', pd.NA).fillna(df_pc['Num. Cotacao_extra']).fillna('')
        if 'SCM' in df_pc.columns:
            df_pc['SCM'] = df_pc['SCM'].replace('', pd.NA).fillna(df_pc.get('SCM_extra', '')).fillna('')

        # 2. Cruzamento PC -> SC (Trazer Status, N° PC e Datas para as Solicitações)
        pc_vlookup = df_pc[['LINK_NORMAL', 'STATUS', 'N° PC', 'Data Emissao', 'DT entrega ', 'Nome Fornecedor', 'CC']].drop_duplicates('LINK_NORMAL')
        df_sc = df_sc.merge(pc_vlookup, on='LINK_NORMAL', how='left', suffixes=('', '_extra'))

        # Preenchimento forçado de lacunas na SC
        cols_preencher = ['STATUS', 'N° PC', 'Data Emissao', 'DT entrega ', 'Nome Fornecedor', 'CC']
        for col in cols_preencher:
            col_extra = f"{col}_extra"
            if col_extra in df_sc.columns:
                df_sc[col] = df_sc[col].replace('', pd.NA).fillna(df_sc[col_extra]).fillna('')

        # Padroniza nomes para exibição
        df_sc = df_sc.rename(columns={"Numero da SC": "N° da SC", "Numero Pedido": "N° PC"})
        
        return df_pc, df_sc
    except Exception as e:
        st.error(f"Erro na integração: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_e_consolidar()

COLUNAS_PADRAO = ["STATUS", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]

# 6. BUSCA E EXIBIÇÃO
if busca:
    t = busca.lower().strip()
    
    # Filtra em ambas as bases já vinculadas
    res_pc = df_pc[df_pc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
    res_sc = df_sc[df_sc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]

    # Une os resultados. Se for a mesma SC/Produto/QNT, o drop_duplicates mantém apenas uma linha
    df_res = pd.concat([res_pc, res_sc], ignore_index=True)
    if 'LINK_NORMAL' in df_res.columns:
        df_res = df_res.drop_duplicates(subset=['LINK_NORMAL', 'Produto', 'QNT'])

    if not df_res.empty:
        for col in COLUNAS_PADRAO:
            if col not in df_res.columns: df_res[col] = ""
            
        df_final = df_res[COLUNAS_PADRAO].fillna('')
        st.markdown(f'<div class="status-box">🟢 {len(df_res)} registros localizados e vinculados</div>', unsafe_allow_html=True)
        
        # Download
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_final.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_ParenteAndrade.xlsx")
        
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum resultado para: {busca}")
else:
    st.info("💡 Digite um termo para pesquisar. O sistema cruza os dados entre Pedidos e Solicitações automaticamente.")
    
