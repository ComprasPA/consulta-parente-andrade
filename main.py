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

# 3. CSS (Mantido o padrão anterior com ajustes)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    .stApp { background-color: #f0f2f6; }
    .stApp > div > div > div > div > section > div {
        background-image: url("data:image/png;base64,""" + str(base64_logo) + """");
        background-size: 350px;
        background-position: center 250px;
        background-repeat: no-repeat;
        background-attachment: fixed;
        opacity: 0.05;
        z-index: -1;
    }
    .block-container { padding-top: 1rem !important; }
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 8px 15px !important;
        border-radius: 10px;
        border: 2px solid #478c3b;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .stDownloadButton button {
        background-color: #f2a933 !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
    }
    .footer-text { text-align: center; color: #478c3b; font-size: 12px; margin-top: 40px; font-weight: bold; }
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

# 5. CARREGAMENTO DE DADOS (Lógica de Múltiplas Abas)
URL_BASE = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP"

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        # GID da aba principal (Follow Up) e da nova aba Protheus SC (2)
        # Nota: O gid da aba 'Protheus SC (2)' geralmente é encontrado na URL ao clicar nela.
        # Caso o GID mude, ajuste aqui.
        url_follow_up = f"{URL_BASE}/export?format=csv&gid=0" 
        url_protheus_sc = f"{URL_BASE}/export?format=csv&gid=1626027376" # GID Exemplo para a aba 2

        df_pedidos = pd.read_csv(url_follow_up, dtype=str).fillna('')
        try:
            df_sc = pd.read_csv(url_protheus_sc, dtype=str).fillna('')
        except:
            df_sc = pd.DataFrame()

        # Padronização de Colunas para o Merge
        if not df_pedidos.empty:
            df_pedidos['N° da SC'] = df_pedidos['N° da SC'].astype(str).str.zfill(7)
        
        if not df_sc.empty:
            # Ajuste o nome da coluna de SC na aba 2 se for diferente
            col_sc_aba2 = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'N° da SC'
            df_sc[col_sc_aba2] = df_sc[col_sc_aba2].astype(str).str.zfill(7)
            
            # Realiza o Merge para trazer Cotações de SCs que ainda não tem Pedido
            # 'outer' garante que SCs sem pedidos apareçam
            df_final = pd.merge(df_pedidos, df_sc, left_on='N° da SC', right_on=col_sc_aba2, how='outer', suffixes=('', '_sc'))
        else:
            df_final = df_pedidos

        # --- TRATAMENTO DE COLUNAS ---
        if 'Produto' in df_final.columns:
            df_final['Produto'] = df_final['Produto'].astype(str).str.zfill(10)
        
        # Criação/Ajuste da coluna de Cotação (ajuste o nome conforme sua planilha aba 2)
        if 'Num. Cotacao' not in df_final.columns:
            df_final['Num. Cotacao'] = df_final['Numero da Cotacao'] if 'Numero da Cotacao' in df_final.columns else ''

        # Formatação de Datas
        col_datas = ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]
        for col in col_datas:
            if col in df_final.columns:
                temp = pd.to_datetime(df_final[col], errors='coerce')
                df_final[col] = temp.dt.strftime('%d/%m/%y').fillna(df_final[col]).replace(['NaT', 'nan'], '')
        
        return df_final.fillna('')
    except Exception as e:
        st.error(f"Erro ao processar as bases: {e}")
        return None

df = carregar_dados()

# 6. EXIBIÇÃO DOS DADOS
if df is not None:
    df_display = df.copy()
    
    if busca:
        mask = df_display.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df_display[mask]

    # Ordem das colunas com a inclusão de NUM. COTAÇÃO
    col_v = [
        "STATUS", 
        "N° da SC", 
        "Num. Cotacao", # Nova Coluna Solicitada
        "N° PC", 
        "CC", 
        "Nome Fornecedor", 
        "Produto", 
        "Descricao", 
        "UM", "QNT", " Prc Unitario", " Vlr.Total", 
        "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", 
        "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "
    ]
    
    cols = [c for c in col_v if c in df_display.columns]

    c_msg, c_down = st.columns([3, 1])
    with c_msg:
        st.info(f"📊 {len(df_display)} registros encontrados na base integrada.")
    
    with c_down:
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
            df_display[cols].to_excel(writer, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "FollowUp_ParenteAndrade.xlsx")

    st.dataframe(df_display[cols], use_container_width=True, hide_index=True)

st.markdown("<p class='footer-text'>PARENTE ANDRADE LTDA | Setor de Suprimentos</p>", unsafe_allow_html=True)
