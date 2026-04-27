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

# 3. CSS (TÍTULO 40 PRETO E CENTRALIZADO)
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    .portal-title {{ 
        color: #000000 !important; font-size: 40px !important; 
        font-weight: bold !important; text-align: center !important; margin: 0;
    }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 2px 10px !important; 
        border-radius: 8px; border: 2px solid #478c3b;
    }}
    .stDownloadButton button {{ 
        background-color: #f2a933 !important; color: white !important; font-weight: bold !important; 
    }}
    </style>
    """, unsafe_allow_html=True)

# 4. FUNÇÕES DE FORMATAÇÃO (DATAS E PRODUTO)
def tratar_dados(df):
    # Formatação de Datas (DD/MM/AA)
    colunas_data = ["Data Emissao", "Dt Liberacao", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]
    for col in colunas_data:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%y').fillna(df[col]).replace(['NaT', 'nan'], '')
    
    # Formatação do Produto (10 dígitos com zeros à esquerda)
    if "Produto" in df.columns:
        df["Produto"] = df["Produto"].astype(str).str.split('.').str[0] # Remove decimais se houver
        df["Produto"] = df["Produto"].str.zfill(10).replace('0000000nan', '')
        
    return df

# 5. CARREGAMENTO DAS ABAS EM CACHE
@st.cache_data(ttl=600, show_spinner="Sincronizando bases...")
def carregar_bases():
    URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        
        # Aba 1 - Prioridade (PC)
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc = tratar_dados(df_pc)
        
        # Aba 2 - Secundária (SC)
        df_sc = pd.DataFrame()
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        if aba_sc_nome:
            df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('')
            df_sc = tratar_dados(df_sc)
            
        return df_pc, df_sc
    except Exception as e:
        st.error(f"Erro ao carregar bases: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 6. CABEÇALHO
col_logo, col_titulo, col_busca = st.columns([1, 4, 1.5])
with col_logo:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:140px;">', unsafe_allow_html=True)
with col_titulo:
    st.markdown('<div class="portal-title">Portal Gestão de Compras Parente Andrade</div>', unsafe_allow_html=True)
with col_busca:
    st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    busca = st.text_input("", placeholder="🔍 O que deseja consultar?", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 15px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 7. LÓGICA DE BUSCA HIERÁRQUICA
df_pc, df_sc = carregar_bases()

if busca:
    termo = busca.lower().strip()
    
    mask_pc = df_pc.apply(lambda row: row.astype(str).str.lower().str.contains(termo, na=False).any(), axis=1)
    df_res = df_pc[mask_pc]
    origem = "Protheus PC"

    if df_res.empty and not df_sc.empty:
        mask_sc = df_sc.apply(lambda row: row.astype(str).str.lower().str.contains(termo, na=False).any(), axis=1)
        df_res = df_sc[mask_sc]
        origem = "Protheus SC"

    if not df_res.empty:
        col_v = [
            "N° da SC", "Num. Cotacao", "Código Cotação", "N° PC", "CC", 
            "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", 
            " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", 
            "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", 
            "STATUS", "DT entrega "
        ]
        cols_finais = [c for c in col_v if c in df_res.columns]

        c1, c2 = st.columns([3, 1])
        with c1: st.write(f"🟢 Encontrado em: **{origem}** ({len(df_res)} registros)")
        with c2:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                df_res[cols_finais].to_excel(wr, index=False)
            st.download_button("📥 BAIXAR EXCEL", out.getvalue(), f"Busca_{origem}.xlsx")

        st.dataframe(df_res[cols_finais], use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhuma informação localizada para: '{busca}'")
else:
    st.info("💡 Digite um termo para iniciar a busca prioritária (PC -> SC).")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
