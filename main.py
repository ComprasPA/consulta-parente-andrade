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

# 2. FUNÇÃO LOGO (Arquivo Local)
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

base64_logo = get_base64_logo()

# 3. CSS PARA INTERFACE E TÍTULO (FONTE 40)
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    
    /* Título solicitado: Preto, Tamanho 40, Centralizado */
    .portal-title {{
        color: #000000 !important;
        font-size: 40px !important;
        font-weight: bold !important;
        text-align: center !important;
        margin: 0px !important;
        padding: 0px !important;
        line-height: 1.1;
        display: block;
        width: 100%;
    }}

    /* Container do cabeçalho */
    .block-container {{ 
        padding-top: 1.5rem !important; 
    }}

    /* Barra de Busca à direita */
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff;
        padding: 2px 10px !important;
        border-radius: 8px;
        border: 2px solid #478c3b;
    }}

    .stDownloadButton button {{
        background-color: #f2a933 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO (LOGO ESQUERDA | TÍTULO CENTRO | BUSCA DIREITA)
# Usando colunas para organizar o layout
col_logo, col_titulo, col_busca = st.columns([1, 3.5, 1.2])

with col_logo:
    if base64_logo:
        st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:160px; height:auto;">', unsafe_allow_html=True)

with col_titulo:
    # Div com classe portal-title para forçar o tamanho 40 via CSS
    st.markdown('<div class="portal-title">Portal Gestão de Compras Parente Andrade</div>', unsafe_allow_html=True)

with col_busca:
    st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    busca = st.text_input("", placeholder="🔍 Buscar...", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 15px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO DE DADOS (GOOGLE DRIVE)
URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        excel_file = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        abas = excel_file.sheet_names
        df_follow = pd.read_excel(excel_file, sheet_name=abas[0], dtype=str).fillna('')
        
        # Lógica para segunda aba (Protheus/SC)
        aba_sc = next((s for s in abas if "PROTHEUS" in s.upper() or "SC" in s.upper() and s != abas[0]), None)
        if aba_sc:
            df_sc = pd.read_excel(excel_file, sheet_name=aba_sc, dtype=str).fillna('')
            if 'N° da SC' in df_follow.columns:
                df_follow['N° da SC'] = df_follow['N° da SC'].astype(str).str.zfill(7)
            
            sc_col = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'Solicitação'
            if sc_col in df_sc.columns:
                df_sc[sc_col] = df_sc[sc_col].astype(str).str.zfill(7)
                cot_col = next((c for c in df_sc.columns if "COTACAO" in c.upper() or "COTAÇÃO" in c.upper()), None)
                if cot_col:
                    df_follow = pd.merge(df_follow, df_sc[[sc_col, cot_col]], left_on='N° da SC', right_on=sc_col, how='left').fillna('')
        
        # Formatação de Datas
        for c in ["DT Envio", "Data Emissao", "Dt Liberacao", "DT entrega "]:
            if c in df_follow.columns:
                df_follow[c] = pd.to_datetime(df_follow[c], errors='coerce').dt.strftime('%d/%m/%y').fillna(df_follow[c])
        
        return df_follow
    except Exception as e:
        st.error(f"Erro técnico: {e}")
        return None

df = carregar_dados()

# 6. TABELA E DOWNLOAD
if df is not None:
    df_disp = df.copy()
    if busca:
        mask = df_disp.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_disp = df_disp[mask]

    col_v = [
        "N° da SC", "Num. Cotacao", "Código Cotação", "N° PC", "CC", 
        "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", 
        " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", 
        "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", 
        "DT entrega ", "STATUS"
    ]
    cols_finais = [c for c in col_v if c in df_disp.columns]

    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(f"🟢 **{len(df_disp)}** registros encontrados.")
    with c2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as wr:
            df_disp[cols_finais].to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL", output.getvalue(), "PortalCompras_PA.xlsx")

    st.dataframe(df_disp[cols_finais], use_container_width=True, hide_index=True)

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
