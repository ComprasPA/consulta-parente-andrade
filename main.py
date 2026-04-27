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
    busca = st.text_input("", placeholder="🔍 Digite SC, Pedido, Fornecedor...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. MOTOR DE INTELIGÊNCIA E VÍNCULO
def normalizar(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']: return ""
    return str(val).split('.')[0].strip().lstrip('0')

@st.cache_data(ttl=600)
def carregar_e_processar_inteligencia():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]

        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [str(c).strip() for c in df_sc.columns]

        # União das bases
        df_mestre = pd.concat([df_pc, df_sc], ignore_index=True)
        df_mestre['CHAVE'] = df_mestre['Numero da SC'].apply(normalizar)
        
        # PROPAGAÇÃO DE VALORES (Garante que cada linha do grupo SC tenha os dados)
        colunas_vinc = ["STATUS", "Num. Cotacao", "Numero Pedido", "CC", "Nome Fornecedor", "Data Emissao", "Dt Liberacao", "DT Envio", "DT entrega"]
        for col in colunas_vinc:
            if col in df_mestre.columns:
                df_mestre[col] = df_mestre[col].replace('', pd.NA)
                df_mestre[col] = df_mestre.groupby('CHAVE')[col].transform('first').fillna('')

        # LÓGICA DE STATUS "EM COTAÇÃO" (Se Status vazio e Cotação preenchida)
        def definir_status(row):
            st_atual = str(row.get('STATUS', '')).strip()
            cot_atual = str(row.get('Num. Cotacao', '')).strip()
            if (st_atual == "" or st_atual.lower() == "nan") and cot_atual != "":
                return "EM COTAÇÃO"
            return st_atual

        df_mestre['STATUS'] = df_mestre.apply(definir_status, axis=1)

        # Formatação de Datas dd/mm/aa
        for col in df_mestre.columns:
            if any(d in col.upper() for d in ["DATA", "DT "]):
                df_mestre[col] = pd.to_datetime(df_mestre[col], errors='coerce').dt.strftime('%d/%m/%y').fillna('')

        return df_mestre.fillna('')
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return pd.DataFrame()

df_final = carregar_e_processar_inteligencia()

# Coluna "Num. Cotacao" removida da lista de exibição
COL_VISIVEL = ["STATUS", "Numero da SC", "Numero Pedido", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega"]

# 6. EXIBIÇÃO
if busca:
    t = busca.lower().strip()
    df_res = df_final[df_final.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
    
    if not df_res.empty:
        df_res = df_res.drop_duplicates(subset=['CHAVE', 'Produto', 'QNT', 'Descricao'])
        
        # Garante as colunas no painel
        for c in COL_VISIVEL:
            if c not in df_res.columns: df_res[c] = ""
            
        df_exibir = df_res[COL_VISIVEL]
        
        st.markdown(f'<div class="status-box">🟢 {len(df_res)} registros processados | Inteligência de Cotação Ativada</div>', unsafe_allow_html=True)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_exibir.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_Compras_PA.xlsx")
        
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nada encontrado para: {busca}")
else:
    st.info("💡 Digite o termo de busca. Status 'EM COTAÇÃO' gerado automaticamente via aba SC.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
