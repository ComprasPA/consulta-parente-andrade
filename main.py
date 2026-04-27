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

# 3. CSS PARA INTERFACE, TÍTULO E LOGO
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    
    /* Marca d'água */
    .stApp > div > div > div > div > section > div {{
        background-image: url("data:image/png;base64,{base64_logo if base64_logo else ''}");
        background-size: 350px; background-position: center 250px;
        background-repeat: no-repeat; background-attachment: fixed; opacity: 0.05;
        z-index: -1;
    }}

    /* Ajuste para a logo não ser cortada e espaçamento do cabeçalho */
    .block-container {{ 
        padding-top: 2rem !important; 
        padding-bottom: 1rem !important;
    }}

    /* Estilo do Título Principal */
    .main-title {{
        color: #478c3b;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 5px;
    }}

    /* Barra de Busca Compacta */
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff;
        padding: 5px 15px !important;
        border-radius: 10px;
        border: 2px solid #478c3b;
        max-width: 500px;
    }}

    .stDownloadButton button {{
        background-color: #f2a933 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO (LOGO E TÍTULO)
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    if base64_logo:
        # Uso de HTML para garantir que a imagem não seja cortada pelo container
        st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:160px; height:auto;">', unsafe_allow_html=True)
    else:
        st.subheader("PA")

with col_titulo:
    st.markdown('<p class="main-title">Portal Gestão de Compras Parente Andrade</p>', unsafe_allow_html=True)
    busca = st.text_input("", placeholder="🔍 O que deseja consultar? (SC, Cotação, Pedido...)", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 10px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO DE DADOS (XLSX)
URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        excel_file = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        df_follow = pd.read_excel(excel_file, sheet_name=0, dtype=str).fillna('')
        
        try:
            df_sc = pd.read_excel(excel_file, sheet_name="Protheus SC", dtype=str).fillna('')
        except:
            df_sc = pd.DataFrame()

        if 'N° da SC' in df_follow.columns:
            df_follow['N° da SC'] = df_follow['N° da SC'].astype(str).str.zfill(7)
        
        if not df_sc.empty:
            sc_col_2 = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'Solicitação'
            if sc_col_2 in df_sc.columns:
                df_sc[sc_col_2] = df_sc[sc_col_2].astype(str).str.zfill(7)
                cot_col = 'Num. Cotacao' if 'Num. Cotacao' in df_sc.columns else 'Código Cotação'
                
                df_follow = pd.merge(df_follow, df_sc[[sc_col_2, cot_col]], 
                                    left_on='N° da SC', right_on=sc_col_2, 
                                    how='left').fillna('')
        
        cols_dt = ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]
        for c in cols_dt:
            if c in df_follow.columns:
                temp = pd.to_datetime(df_follow[c], errors='coerce')
                df_follow[c] = temp.dt.strftime('%d/%m/%y').fillna(df_follow[c]).replace(['NaT', 'nan'], '')
        
        return df_follow
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

df = carregar_dados()

# 6. EXIBIÇÃO E DOWNLOAD
if df is not None:
    df_disp = df.copy()
    if busca:
        mask = df_disp.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_disp = df_disp[mask]

    # ORDEM DAS COLUNAS: STATUS POR ÚLTIMO
    col_v = [
        "N° da SC", "Num. Cotacao", "Código Cotação", "N° PC", "CC", 
        "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", 
        " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", 
        "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", 
        "DT entrega ", "STATUS"
    ]
    cols_finais = [c for c in col_v if c in df_disp.columns]

    # Botão de Download e Contador
    c1, c2 = st.columns([3, 1])
    with c1:
        st.write(f"🟢 **{len(df_disp)}** registros encontrados.")
    with c2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as wr:
            df_disp[cols_finais].to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL", output.getvalue(), "GestaoCompras_PA.xlsx")

    st.dataframe(df_disp[cols_finais], use_container_width=True, hide_index=True)

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
