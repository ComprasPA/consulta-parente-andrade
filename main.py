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

# 2. FUNÇÃO LOGO
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except: return None

base64_logo = get_base64_logo()

# 3. CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stApp { background-color: #f0f2f6; }
    .stApp > div > div > div > div > section > div {
        background-image: url("data:image/png;base64,""" + str(base64_logo) + """");
        background-size: 350px; background-position: center 250px;
        background-repeat: no-repeat; background-attachment: fixed; opacity: 0.05; z-index: -1;
    }
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff; padding: 8px 15px !important;
        border-radius: 10px; border: 2px solid #478c3b;
    }
    .stDownloadButton button { background-color: #f2a933 !important; color: white !important; font-weight: bold !important; }
    .footer-text { text-align: center; color: #478c3b; font-size: 12px; margin-top: 40px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
col_logo, col_busca = st.columns([1, 4])
with col_logo:
    try: st.image("logo", width=150)
    except: st.subheader("PARENTE ANDRADE")
with col_busca:
    busca = st.text_input("", placeholder="🔍 Consulte SC, Cotação, Pedido, Produto...", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO DE DADOS
URL_BASE = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP"

def get_csv_url(gid):
    return f"{URL_BASE}/export?format=csv&gid={gid}"

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        # Tente carregar a aba principal (GID 0 costuma ser a primeira aba)
        df_pedidos = pd.read_csv(get_csv_url("0"), dtype=str).fillna('')
        
        # ABA PROTHEUS SC (2) - Verifique se o GID é este mesmo na sua URL
        # Se continuar dando erro 400, é porque este número (1626027376) está errado para o seu arquivo.
        gid_sc2 = "1626027376" 
        df_sc = pd.read_csv(get_csv_url(gid_sc2), dtype=str).fillna('')

        # Padronização de Colunas
        if 'N° da SC' in df_pedidos.columns:
            df_pedidos['N° da SC'] = df_pedidos['N° da SC'].astype(str).str.zfill(7)
        
        # Identificando a coluna de SC na segunda aba (ajuste o nome se necessário)
        sc_col_aba2 = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'N° da SC'
        if sc_col_aba2 in df_sc.columns:
            df_sc[sc_col_aba2] = df_sc[sc_col_aba2].astype(str).str.zfill(7)

        # Merge (União das bases)
        # Trazemos a cotação da aba 2 para a base principal
        df_final = pd.merge(df_pedidos, df_sc[[sc_col_aba2, 'Num. Cotacao']], 
                            left_on='N° da SC', right_on=sc_col_aba2, 
                            how='left').fillna('')

        # Se a SC não existe na base de pedidos, ela deve ser adicionada? 
        # Se sim, usamos how='outer'. Se quer apenas completar os dados, usamos 'left'.
        
        # Tratamento de Zeros no Produto
        if 'Produto' in df_final.columns:
            df_final['Produto'] = df_final['Produto'].astype(str).str.zfill(10)

        # Formatação de Datas
        for col in ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]:
            if col in df_final.columns:
                temp = pd.to_datetime(df_final[col], errors='coerce')
                df_final[col] = temp.dt.strftime('%d/%m/%y').fillna(df_final[col]).replace(['NaT', 'nan'], '')
        
        return df_final
    except Exception as e:
        st.error(f"Erro ao processar as bases: {e}")
        return None

df = carregar_dados()

# 6. EXIBIÇÃO
if df is not None:
    df_display = df.copy()
    if busca:
        mask = df_display.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df_display[mask]

    # Ordem das colunas com Num. Cotacao entre SC e PC
    cols_check = [
        "STATUS", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", 
        "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", 
        "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", 
        "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "
    ]
    cols = [c for c in cols_check if c in df_display.columns]

    st.dataframe(df_display[cols], use_container_width=True, hide_index=True)
    
    # Botão de Download
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df_display[cols].to_excel(writer, index=False)
    st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Suprimentos_PA.xlsx")

st.markdown("<p class='footer-text'>PARENTE ANDRADE LTDA | Setor de Suprimentos</p>", unsafe_allow_html=True)
