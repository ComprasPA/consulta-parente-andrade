import streamlit as st
import pandas as pd
import base64
import re
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
    busca = st.text_input("", placeholder="🔍 Digite SC ou Pedido...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. MOTOR DE CARREGAMENTO COM LIMPEZA DE CABEÇALHO
def limpar_nome_coluna(nome):
    # Remove espaços, pontuação e caracteres especiais para garantir o match
    return re.sub(r'[^a-zA-Z0-9]', '', str(nome)).upper()

@st.cache_data(ttl=600)
def carregar_dados_seguros():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # --- CARREGAR ABA PC ---
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        # Criamos um mapa: Nome Limpo -> Nome Original para não perder a estética
        mapa_pc = {limpar_nome_coluna(col): col for col in df_pc.columns}
        
        # --- CARREGAR ABA SC ---
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        mapa_sc = {limpar_nome_coluna(col): col for col in df_sc.columns}
        
        return df_pc, df_sc, mapa_pc, mapa_sc
    except:
        return pd.DataFrame(), pd.DataFrame(), {}, {}

df_pc, df_sc, mapa_pc, mapa_sc = carregar_dados_seguros()

# Colunas que DEVEM aparecer (usamos chaves limpas para busca interna)
COLUNAS_DISPLAY = [
    ("STATUS", "STATUS"), ("NUMERODASC", "Numero da SC"), ("NUMEROPEDIDO", "Numero Pedido"), 
    ("CC", "CC"), ("NOMEFORNECEDOR", "Nome Fornecedor"), ("PRODUTO", "Produto"), 
    ("DESCRICAO", "Descricao"), ("UM", "UM"), ("QNT", "QNT"), 
    ("PRCUNITARIO", " Prc Unitario"), ("VLRTOTAL", " Vlr.Total"), 
    ("DATAEMISSAO", "Data Emissao"), ("DTLIBERACAO", "Dt Liberacao"), 
    ("DTENVIO", "DT Envio"), ("CONDICAOPGO", "CONDIÇÃO PGO"), 
    ("DTPGOAVISTA", "DT Pgo (AVISTA)"), ("DTPREVDEENTREGA", "DT Prev de Entrega"), 
    ("DTENTREGA", "DT entrega")
]

# 6. LÓGICA DE BUSCA SEQUENCIAL CORRIGIDA
if busca:
    t = busca.lower().strip()
    
    # 1. Busca na PC
    res_pc = df_pc[df_pc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
    
    if not res_pc.empty:
        df_final = res_pc.copy()
        origem = "Planilha de Pedidos (PC)"
        mapa_atual = mapa_pc
    else:
        # 2. Busca na SC
        res_sc = df_sc[df_sc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
        if not res_sc.empty:
            df_final = res_sc.copy()
            # Inteligência de Status
            def definir_st(row):
                # Busca a coluna de cotação independente de como esteja escrita
                col_cot = next((c for c in row.index if "COTACAO" in limpar_nome_coluna(c)), None)
                val_cot = str(row[col_cot]).strip() if col_cot else ""
                return "EM COTAÇÃO" if val_cot != "" and val_cot.lower() != "nan" else "SC ABERTA"
            df_final['STATUS'] = df_final.apply(definir_st, axis=1)
            origem = "Planilha de Solicitações (SC)"
            mapa_atual = mapa_sc
        else:
            df_final = pd.DataFrame()

    if not df_final.empty:
        # Reconstrução da tabela para garantir que UM, QNT, Fornecedor e Datas apareçam
        df_painel = pd.DataFrame()
        
        for chave_limpa, nome_bonito in COLUNAS_DISPLAY:
            # Tenta achar a coluna original na base que veio da planilha
            col_original = next((c for c in df_final.columns if limpar_nome_coluna(c) == chave_limpa), None)
            
            if col_original:
                df_painel[nome_bonito] = df_final[col_original]
                # Formata se for data
                if "DATA" in chave_limpa or "DT" in chave_limpa:
                    df_painel[nome_bonito] = pd.to_datetime(df_painel[nome_bonito], errors='coerce').dt.strftime('%d/%m/%y').fillna('')
            else:
                df_painel[nome_bonito] = ""

        st.markdown(f'<div class="status-box">🟢 Dados Vinculados de: {origem}</div>', unsafe_allow_html=True)
        
        # Download
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_painel.to_excel(wr, index=False)
        st.download_button("📥 DESCARREGAR RELATÓRIO", out.getvalue(), "Portal_Compras_Parente.xlsx")
        
        st.dataframe(df_painel, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum registro localizado para: {busca}")
else:
    st.info("💡 Digite o número da SC ou Pedido. Prioridade: PC (Completo) > SC (Pendente).")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
