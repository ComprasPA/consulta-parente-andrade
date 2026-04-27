import streamlit as st
import pandas as pd
import base64
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | Parente Andrade",
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

# 3. CSS PARA INTERFACE, MARCA D'ÁGUA E AJUSTES DE BUSCA
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stAppDeployButton {{display:none;}}
    .stApp {{ background-color: #f0f2f6; }}
    
    .stApp > div > div > div > div > section > div {{
        background-image: url("data:image/png;base64,{base64_logo if base64_logo else ''}");
        background-size: 350px; background-position: center 250px;
        background-repeat: no-repeat; background-attachment: fixed; opacity: 0.05;
        z-index: -1;
    }}

    .block-container {{ padding-top: 1rem !important; }}

    /* Barra de Busca mais compacta */
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff;
        padding: 5px 15px !important;
        border-radius: 10px;
        border: 2px solid #478c3b;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        max-width: 600px; /* Limita a largura da busca */
    }}

    /* Botão de Download Amarelo PA */
    .stDownloadButton button {{
        background-color: #f2a933 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
    }}

    .footer-text {{ text-align: center; color: #478c3b; font-size: 12px; margin-top: 40px; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO (LOGO E BUSCA LADO A LADO)
col_logo, col_busca = st.columns([1, 3])
with col_logo:
    if base64_logo:
        st.image("logo", width=150)
    else:
        st.subheader("PARENTE ANDRADE")

with col_busca:
    st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True) # Ajuste de altura
    busca = st.text_input("", placeholder="🔍 O que você deseja consultar?", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO DE DADOS (XLSX)
URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        excel_data = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        df_follow = pd.read_excel(excel_data, sheet_name=0, dtype=str).fillna('')
        
        try:
            df_sc = pd.read_excel(excel_data, sheet_name="Protheus SC", dtype=str).fillna('')
        except:
            df_sc = pd.DataFrame()

        # Padronização
        if 'N° da SC' in df_follow.columns:
            df_follow['N° da SC'] = df_follow['N° da SC'].astype(str).str.zfill(7)
        
        if not df_sc.empty:
            col_sc_2 = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'Solicitação'
            if col_sc_2 in df_sc.columns:
                df_sc[col_sc_2] = df_sc[col_sc_2].astype(str).str.zfill(7)
                col_cot = 'Num. Cotacao' if 'Num. Cotacao' in df_sc.columns else 'Código Cotação'
                
                # Merge para incluir cotação
                df_follow = pd.merge(df_follow, df_sc[[col_sc_2, col_cot]], 
                                    left_on='N° da SC', right_on=col_sc_2, 
                                    how='left').fillna('')
        
        # Formatação de Datas
        col_datas = ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]
        for col in col_datas:
            if col in df_follow.columns:
                temp = pd.to_datetime(df_follow[col], errors='coerce')
                df_follow[col] = temp.dt.strftime('%d/%m/%y').fillna(df_follow[col]).replace(['NaT', 'nan'], '')
        
        return df_follow
    except Exception as e:
        st.error(f"Erro: {e}")
        return None

df = carregar_dados()

# 6. EXIBIÇÃO E DOWNLOAD
if df is not None:
    df_display = df.copy()
    if busca:
        mask = df_display.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df_display[mask]

    # ORDEM EXATA DAS COLUNAS SOLICITADA
    # Incluído 'Num. Cotacao' / 'Código Cotação' após 'N° da SC'
    col_v = [
        "STATUS", "N° da SC", "Num. Cotacao", "Código Cotação", "N° PC", "CC", 
        "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", 
        " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", 
        "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "
    ]
    
    # Filtra apenas as que existem no DataFrame final
    cols_finais = [c for c in col_v if c in df_display.columns]

    # Linha do Botão e Mensagem
    c_msg, c_down = st.columns([3, 1])
    with c_msg:
        st.write(f"📊 {len(df_display)} registros encontrados.")
    
    with c_down:
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_display[cols_finais].to_excel(writer, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Suprimentos_PA.xlsx")

    # Exibição da Tabela
    st.dataframe(df_display[cols_finais], use_container_width=True, hide_index=True)

st.markdown("<p class='footer-text'>PARENTE ANDRADE LTDA | Setor de Suprimentos</p>", unsafe_allow_html=True)
