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

# 5. MOTOR DE CONSOLIDAÇÃO (VÍNCULO E DATAS DD/MM/YY)
def normalizar_valor(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']: return ""
    return str(val).split('.')[0].strip().lstrip('0')

def formatar_datas_brasileiras(df):
    cols_data = ["Data Emissao", "Dt Liberacao", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]
    for col in cols_data:
        if col in df.columns:
            # Converte para datetime e depois para string dd/mm/yy
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%y')
            df[col] = df[col].fillna('')
    return df

@st.cache_data(ttl=600)
def carregar_dados():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # Carrega Pedidos (PC)
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]

        # Carrega Solicitações (SC)
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [str(c).strip() for c in df_sc.columns]

        # Mapeamento Inteligente de Colunas
        def achar_col(lista, termos):
            for t in termos:
                for c in lista:
                    if t.upper() in c.upper(): return c
            return None

        c_sc_pc = achar_col(df_pc.columns, ["N° da SC", "NUMERO DA SC", "SC"])
        c_pc_pc = achar_col(df_pc.columns, ["N° PC", "PEDIDO", "PC"])
        c_sc_sc = achar_col(df_sc.columns, ["NUMERO DA SC", "N° DA SC", "SC"])
        c_pc_sc = achar_col(df_sc.columns, ["N° PC", "PEDIDO", "NUMERO PEDIDO"])

        if c_sc_pc and not df_sc.empty and c_sc_sc:
            df_pc['CHAVE'] = df_pc[c_sc_pc].apply(normalizar_valor)
            df_sc['CHAVE'] = df_sc[c_sc_sc].apply(normalizar_valor)

            # --- PROCV REFORÇADO (PC para SC) ---
            cols_doar = [c for c in [c_pc_pc, 'STATUS', 'Nome Fornecedor', 'CC', 'Data Emissao', 'DT entrega ', 'DT Pgo (AVISTA)', 'DT Prev de Entrega'] if c in df_pc.columns]
            pc_map = df_pc[['CHAVE'] + cols_doar].drop_duplicates('CHAVE')
            
            df_sc = df_sc.merge(pc_map, on='CHAVE', how='left', suffixes=('', '_pc'))

            # Preenchimento compulsório do N° PC e Datas na aba SC
            target_pc = c_pc_sc if c_pc_sc else 'N° PC'
            if f"{c_pc_pc}_pc" in df_sc.columns:
                df_sc[target_pc] = df_sc[target_pc].replace('', pd.NA).fillna(df_sc[f"{c_pc_pc}_pc"]).fillna('')
            
            # Preenche Status e Datas vindos da PC
            for f in ['STATUS', 'Nome Fornecedor', 'CC', 'Data Emissao', 'DT entrega ', 'DT Pgo (AVISTA)', 'DT Prev de Entrega']:
                if f"{f}_pc" in df_sc.columns:
                    df_sc[f] = df_sc[f].replace('', pd.NA).fillna(df_sc[f"{f}_pc"]).fillna('')

        # Padronização de nomes
        if not df_pc.empty: df_pc = df_pc.rename(columns={c_sc_pc: "N° da SC", c_pc_pc: "N° PC"})
        if not df_sc.empty: df_sc = df_sc.rename(columns={c_sc_sc: "N° da SC", c_pc_sc: "N° PC"})

        # APLICAÇÃO FINAL DA FORMATAÇÃO DE DATA BRASILEIRA
        df_pc = formatar_datas_brasileiras(df_pc)
        df_sc = formatar_datas_brasileiras(df_sc)

        return df_pc, df_sc

    except Exception as e:
        st.error(f"Erro na integração: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_dados()

COLUNAS_PADRAO = ["STATUS", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]

# 6. BUSCA E EXIBIÇÃO
if busca:
    t = busca.lower().strip()
    res_pc = df_pc[df_pc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)] if not df_pc.empty else pd.DataFrame()
    res_sc = df_sc[df_sc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)] if not df_sc.empty else pd.DataFrame()

    df_res = pd.concat([res_pc, res_sc], ignore_index=True)
    if not df_res.empty:
        if 'CHAVE' in df_res.columns: df_res = df_res.drop_duplicates(subset=['CHAVE', 'Produto', 'QNT'])

        for col in COLUNAS_PADRAO:
            if col not in df_res.columns: df_res[col] = ""
            
        df_final = df_res[COLUNAS_PADRAO].fillna('')
        st.markdown(f'<div class="status-box">🟢 {len(df_res)} registros localizados e formatados</div>', unsafe_allow_html=True)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_final.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_Compras_PA.xlsx")
        st.dataframe(df_final, use_container_width=True, hide_index=True)
else:
    st.info("💡 Digite um termo para pesquisar. Datas formatadas em DD/MM/YY.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
