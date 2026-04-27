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

# 2. FUNÇÃO LOGO BASE64
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return None

base64_logo = get_base64_logo()

# 3. CSS PARA INTERFACE E MARCA D'ÁGUA
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stAppDeployButton {{display:none;}}
    .stApp {{ background-color: #f0f2f6; }}
    .stApp > div > div > div > div > section > div {{
        background-image: url("data:image/png;base64,{base64_logo}");
        background-size: 350px;
        background-position: center 250px;
        background-repeat: no-repeat;
        background-attachment: fixed;
        opacity: 0.05;
        z-index: -1;
    }}
    .block-container {{ padding-top: 1rem !important; }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff;
        padding: 8px 15px !important;
        border-radius: 10px;
        border: 2px solid #478c3b;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }}
    .stDownloadButton button {{
        background-color: #f2a933 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
    }}
    .footer-text {{ text-align: center; color: #478c3b; font-size: 12px; margin-top: 40px; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
col_logo, col_busca = st.columns([1, 4])
with col_logo:
    try: st.image("logo", width=150)
    except: st.subheader("PARENTE ANDRADE")

with col_busca:
    busca = st.text_input("", placeholder="🔍 Consulte SC, Cotação, Pedido, Produto ou Fornecedor...", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO DE DADOS (INTEGRAÇÃO DE ABAS)
URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        # Carrega o arquivo Excel completo
        excel_file = pd.ExcelFile(URL_XLSX)
        
        # Carrega a aba de Follow Up (Aba 1) e a Protheus SC (Aba 2)
        df_follow = pd.read_excel(excel_file, sheet_name=0, dtype=str).fillna('')
        
        try:
            df_sc = pd.read_excel(excel_file, sheet_name="Protheus SC", dtype=str).fillna('')
        except:
            df_sc = pd.DataFrame()

        # Padronização de Colunas
        if 'N° da SC' in df_follow.columns:
            df_follow['N° da SC'] = df_follow['N° da SC'].astype(str).str.zfill(7)
        
        # Cruzamento de dados (Merge)
        if not df_sc.empty:
            # Identifica a coluna de SC na aba Protheus SC
            sc_col_origem = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'Solicitação'
            if sc_col_origem in df_sc.columns:
                df_sc[sc_col_origem] = df_sc[sc_col_origem].astype(str).str.zfill(7)
                
                # Identifica a coluna de Cotação
                cot_col = 'Num. Cotacao' if 'Num. Cotacao' in df_sc.columns else 'Código Cotação'
                
                # Merge 'outer' para mostrar SCs mesmo que ainda não tenham pedido no follow up
                df_final = pd.merge(df_follow, df_sc[[sc_col_origem, cot_col]], 
                                    left_on='N° da SC', right_on=sc_col_origem, 
                                    how='outer').fillna('')
                
                # Consolida as colunas de SC caso o outer merge tenha criado duplicatas de nome
                if 'N° da SC' in df_final.columns and sc_col_origem != 'N° da SC':
                    df_final['N° da SC'] = df_final['N° da SC'].replace('', df_final[sc_col_origem])
            else:
                df_final = df_follow
        else:
            df_final = df_follow

        # Ajuste de zeros e datas
        if 'Produto' in df_final.columns:
            df_final['Produto'] = df_final['Produto'].astype(str).str.zfill(10)
        
        col_datas = ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]
        for col in col_datas:
            if col in df_final.columns:
                temp = pd.to_datetime(df_final[col], errors='coerce')
                df_final[col] = temp.dt.strftime('%d/%m/%y').fillna(df_final[col]).replace(['NaT', 'nan'], '')
        
        return df_final
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None

df = carregar_dados()

# 6. EXIBIÇÃO DOS DADOS
if df is not None:
    df_display = df.copy()
    
    if busca:
        mask = df_display.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df_display[mask]

    # Ordem das colunas com Cotação entre SC e Pedido
    col_v = [
        "STATUS", "N° da SC", "Num. Cotacao", "Código Cotação", "N° PC", "CC", 
        "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", 
        " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio"
    ]
    
    cols = [c for c in col_v if c in df_display.columns]

    st.dataframe(df_display[cols], use_container_width=True, hide_index=True)
    
    # Download
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df_display[cols].to_excel(writer, index=False)
    st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Consulta_Suprimentos_PA.xlsx")

st.markdown("<p class='footer-text'>PARENTE ANDRADE LTDA | Setor de Suprimentos</p>", unsafe_allow_html=True)
