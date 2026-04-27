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
    busca = st.text_input("", placeholder="🔍 Buscar SC, Pedido, Fornecedor...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. MOTOR ANTI-DUPLICIDADE E VÍNCULO MESTRE
def normalizar(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']: return ""
    return str(val).split('.')[0].strip().lstrip('0')

@st.cache_data(ttl=600)
def carregar_e_limpar_duplicados():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # Carregar abas
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]

        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [str(c).strip() for c in df_sc.columns]

        # Criar chaves para cruzamento
        df_pc['CHAVE_SC'] = df_pc['Numero da SC'].apply(normalizar)
        df_sc['CHAVE_SC'] = df_sc['Numero da SC'].apply(normalizar)

        # 1. Criar um dicionário de informações da PC (onde o fornecedor e pedido estão)
        # Agrupamos por CHAVE_SC para pegar os dados do cabeçalho do pedido
        pc_cabecalho = df_pc[['CHAVE_SC', 'STATUS', 'Numero Pedido', 'Nome Fornecedor', 'CC']].drop_duplicates('CHAVE_SC')

        # 2. Integrar as informações da PC na aba SC
        df_sc = df_sc.merge(pc_cabecalho, on='CHAVE_SC', how='left', suffixes=('_sc', ''))

        # 3. Concatenar as duas abas, mas priorizar a aba PC para evitar duplicar itens
        # Criamos uma chave única de ITEM (SC + Produto)
        df_pc['CHAVE_ITEM'] = df_pc['CHAVE_SC'] + "_" + df_pc['Produto'].apply(normalizar)
        df_sc['CHAVE_ITEM'] = df_sc['CHAVE_SC'] + "_" + df_sc['Produto'].apply(normalizar)

        # Unimos as bases e removemos duplicados baseados na CHAVE_ITEM
        # Isso garante que se o item está na PC e na SC, manteremos apenas um registro consolidado
        df_mestre = pd.concat([df_pc, df_sc], ignore_index=True)
        df_mestre = df_mestre.sort_values(by=['Nome Fornecedor'], ascending=False) # Prioriza linhas preenchidas
        df_mestre = df_mestre.drop_duplicates(subset=['CHAVE_ITEM'], keep='first')

        # 4. Lógica de Status "EM COTAÇÃO"
        def definir_status(row):
            st_atual = str(row.get('STATUS', '')).strip()
            cot = str(row.get('Num. Cotacao', '')).strip()
            if st_atual in ['', 'nan', 'NaN'] and cot != "":
                return "EM COTAÇÃO"
            return st_atual if st_atual not in ['nan', 'NaN'] else ""

        df_mestre['STATUS'] = df_mestre.apply(definir_status, axis=1)

        # 5. Formatação de Datas
        for col in df_mestre.columns:
            if any(d in col.upper() for d in ["DATA", "DT "]):
                df_mestre[col] = pd.to_datetime(df_mestre[col], errors='coerce').dt.strftime('%d/%m/%y').fillna('')

        return df_mestre.fillna('')
    except Exception as e:
        st.error(f"Erro na limpeza de duplicidade: {e}")
        return pd.DataFrame()

df_limpo = carregar_e_limpar_duplicados()

COL_PAINEL = ["STATUS", "Numero da SC", "Numero Pedido", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega"]

# 6. EXIBIÇÃO
if busca:
    t = busca.lower().strip()
    df_res = df_limpo[df_limpo.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
    
    if not df_res.empty:
        df_exibir = df_res[[c for c in COL_PAINEL if c in df_res.columns]]
        
        st.markdown(f'<div class="status-box">🟢 {len(df_res)} itens únicos localizados e vinculados</div>', unsafe_allow_html=True)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_exibir.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL LIMPO", out.getvalue(), "Portal_Compras_Final.xlsx")
        
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum registro para: {busca}")
else:
    st.info("💡 Busque para visualizar os itens sem duplicidade de fornecedores.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
