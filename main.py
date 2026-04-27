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
        color: #000000 !important; 
        font-size: 40px !important; 
        font-weight: bold !important; 
        text-align: center !important; 
        margin: 0;
    }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 2px 10px !important; 
        border-radius: 8px; border: 2px solid #478c3b;
    }}
    .stDownloadButton button {{ 
        background-color: #f2a933 !important; 
        color: white !important; 
        font-weight: bold !important; 
    }}
    </style>
    """, unsafe_allow_html=True)

# 4. CARREGAMENTO DE DADOS COM CACHE DE ALTA PERFORMANCE
@st.cache_data(ttl=600, show_spinner="Sincronizando base de dados...")
def carregar_dados_portal():
    # Usamos o formato XLSX por ser mais estável para múltiplas abas
    URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    
    try:
        # Carrega o arquivo inteiro para a memória
        excel = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        abas = excel.sheet_names
        
        # Carrega Aba 1 (Follow Up)
        df_main = pd.read_excel(excel, sheet_name=abas[0], dtype=str).fillna('')
        
        # Carrega Aba 2 (Protheus SC) - Busca por nome parcial para evitar erro 400
        aba_sc = next((s for s in abas if "SC" in s.upper() or "PROTHEUS" in s.upper() and s != abas[0]), None)
        
        if aba_sc:
            df_sc = pd.read_excel(excel, sheet_name=aba_sc, dtype=str).fillna('')
            
            # Normalização de N° SC (7 dígitos)
            if 'N° da SC' in df_main.columns:
                df_main['N° da SC'] = df_main['N° da SC'].astype(str).str.zfill(7)
            
            col_sc_2 = next((c for c in df_sc.columns if "NUMERO" in c.upper() and "SC" in c.upper() or "SOLICIT" in c.upper()), None)
            
            if col_sc_2:
                df_sc[col_sc_2] = df_sc[col_sc_2].astype(str).str.zfill(7)
                # Traz apenas a Cotação para não pesar
                cot_col = next((c for c in df_sc.columns if "COTACAO" in c.upper() or "COTAÇÃO" in c.upper()), None)
                if cot_col:
                    # PROCV (Merge)
                    df_main = pd.merge(df_main, df_sc[[col_sc_2, cot_col]], 
                                      left_on='N° da SC', right_on=col_sc_2, 
                                      how='left').fillna('')

        # Limpeza de strings para busca não falhar com espaços vazios
        for col in df_main.columns:
            df_main[col] = df_main[col].astype(str).str.strip()
            
        return df_main
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# 5. CABEÇALHO (LOGO | TÍTULO | BUSCA)
col_logo, col_titulo, col_busca = st.columns([1, 4, 1.5])
with col_logo:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:140px;">', unsafe_allow_html=True)
with col_titulo:
    st.markdown('<div class="portal-title">Portal Gestão de Compras Parente Andrade</div>', unsafe_allow_html=True)
with col_busca:
    st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    busca = st.text_input("", placeholder="🔍 Digite e pressione Enter...", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 15px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 6. LÓGICA DE BUSCA
df_base = carregar_dados_portal()

if busca and not df_base.empty:
    termo = busca.lower().strip()
    
    # Busca "Deep Search": varre todas as colunas da base integrada
    mask = df_base.apply(lambda row: row.astype(str).str.lower().str.contains(termo, na=False).any(), axis=1)
    df_res = df_base[mask]

    if not df_res.empty:
        # Colunas na ordem solicitada com STATUS por último
        col_v = [
            "N° da SC", "Num. Cotacao", "Código Cotação", "N° PC", "CC", 
            "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", 
            " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", 
            "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", 
            "DT entrega ", "STATUS"
        ]
        cols_finais = [c for c in col_v if c in df_res.columns]

        c1, c2 = st.columns([3, 1])
        with c1: st.write(f"🟢 **{len(df_res)}** registros encontrados.")
        with c2:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                df_res[cols_finais].to_excel(wr, index=False)
            st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_PA.xlsx")

        st.dataframe(df_res[cols_finais], use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhuma informação encontrada para: '{busca}'")
elif not busca:
    st.info("💡 Bem-vindo! Digite qualquer termo (SC, Cotação, Produto ou Fornecedor) para pesquisar.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
