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
    busca = st.text_input("", placeholder="🔍 Buscar SC ou Pedido...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. MOTOR DE BUSCA COM SOBERANIA (PC > SC)
def normalizar(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']: return ""
    return str(val).split('.')[0].strip().lstrip('0')

@st.cache_data(ttl=600)
def carregar_dados_hierarquicos():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # 1. Carregar Planilha SOBERANA (PC)
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]
        # Criar chave única para identificar o item (SC + Produto)
        df_pc['CHAVE_UNICA'] = df_pc['Numero da SC'].apply(normalizar) + "_" + df_pc['Produto'].apply(normalizar)

        # 2. Carregar Planilha de APOIO (SC)
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [str(c).strip() for c in df_sc.columns]
        df_sc['CHAVE_UNICA'] = df_sc['Numero da SC'].apply(normalizar) + "_" + df_sc['Produto'].apply(normalizar)

        # 3. FILTRAR ITENS: Pegar na SC apenas o que NÃO tem pedido na PC
        itens_sem_pedido = df_sc[~df_sc['CHAVE_UNICA'].isin(df_pc['CHAVE_UNICA'])].copy()
        
        # Atribuir status para itens que ainda estão na fase de SC
        def status_pendente(row):
            cot = str(row.get('Num. Cotacao', '')).strip()
            return "EM COTAÇÃO" if cot != "" and cot.lower() != "nan" else "SC ABERTA"
        
        if not itens_sem_pedido.empty:
            itens_sem_pedido['STATUS'] = itens_sem_pedido.apply(status_pendente, axis=1)

        # 4. UNIR AS BASES: PC (Soberana com Fornecedor) + Itens da SC (Aguardando pedido)
        df_final = pd.concat([df_pc, itens_sem_pedido], ignore_index=True)

        # 5. Formatação de Datas para o padrão dd/mm/yy
        for col in df_final.columns:
            if any(d in col.upper() for d in ["DATA", "DT "]):
                df_final[col] = pd.to_datetime(df_final[col], errors='coerce').dt.strftime('%d/%m/%y').fillna('')

        return df_final.fillna('')
    except Exception as e:
        st.error(f"Erro ao processar soberania das planilhas: {e}")
        return pd.DataFrame()

df_portal = carregar_dados_hierarquicos()

# Ordem das colunas conforme sua necessidade
COL_FINAL = ["STATUS", "Numero da SC", "Numero Pedido", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega"]

# 6. EXIBIÇÃO DOS RESULTADOS
if busca:
    t = busca.lower().strip()
    # Busca focada em SC e PC (Soberania PC > SC)
    df_res = df_portal[df_portal.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
    
    if not df_res.empty:
        # Garante que colunas faltantes fiquem vazias e remove duplicados de processamento
        for c in COL_FINAL:
            if c not in df_res.columns: df_res[c] = ""
            
        df_exibir = df_res[COL_FINAL].drop_duplicates()
        
        st.markdown(f'<div class="status-box">🟢 {len(df_exibir)} itens localizados (Hierarquia PC > SC)</div>', unsafe_allow_html=True)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_exibir.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR RELATÓRIO", out.getvalue(), "Portal_Gestao_Parente.xlsx")
        
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum registro encontrado para: {busca}")
else:
    st.info("💡 Digite o número da SC ou Pedido. O sistema prioriza dados da aba PC e complementa com a SC se não houver pedido.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
