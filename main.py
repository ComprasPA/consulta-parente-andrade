import streamlit as st
import pandas as pd
import base64
from io import BytesIO
import urllib.parse

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
        with open(image_path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

base64_logo = get_base64_logo()

# 3. CSS CUSTOMIZADO
st.markdown(f"""
    <style>
    .stApp {{ background-color: #f0f2f6; }}
    .stApp > div > div > div > div > section > div {{
        background-image: url("data:image/png;base64,{base64_logo}");
        background-size: 350px; background-position: center 250px;
        background-repeat: no-repeat; background-attachment: fixed; opacity: 0.05;
    }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 8px 15px !important;
        border-radius: 10px; border: 2px solid #478c3b;
    }}
    .stDownloadButton button {{ background-color: #f2a933 !important; color: white !important; font-weight: bold !important; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CARREGAMENTO DOS DADOS
URL_BASE = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP"

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        # Aba principal (Follow Up) - Geralmente gid=0
        url_follow = f"{URL_BASE}/export?format=csv&gid=0"
        df_follow = pd.read_csv(url_follow, dtype=str).fillna('')

        # Aba Protheus SC
        # Usando o nome da aba codificado para evitar Erro 400
        nome_aba = urllib.parse.quote("Protheus SC")
        url_sc = f"{URL_BASE}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
        df_sc = pd.read_csv(url_sc, dtype=str).fillna('')

        # Padronização e Limpeza
        if 'N° da SC' in df_follow.columns:
            df_follow['N° da SC'] = df_follow['N° da SC'].astype(str).str.zfill(7)
        
        # Identificar coluna de SC na aba Protheus SC
        col_sc_origem = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'Solicitação'
        
        if col_sc_origem in df_sc.columns:
            df_sc[col_sc_origem] = df_sc[col_sc_origem].astype(str).str.zfill(7)
            
            # Cruzamento de dados (PROCV) para trazer a Cotação
            # Ajuste 'Num. Cotacao' para o nome exato da coluna na sua aba "Protheus SC"
            col_cotacao = 'Num. Cotacao' if 'Num. Cotacao' in df_sc.columns else 'Código Cotação'
            
            df_final = pd.merge(
                df_follow, 
                df_sc[[col_sc_origem, col_cotacao]], 
                left_on='N° da SC', 
                right_on=col_sc_origem, 
                how='left'
            ).fillna('')
        else:
            df_final = df_follow

        return df_final
    except Exception as e:
        st.error(f"Erro na conexão com o Google Sheets: {e}")
        return None

# 5. EXECUÇÃO E FILTROS
df = carregar_dados()

if df is not None:
    col1, col2 = st.columns([1, 4])
    with col1:
        try: st.image("logo", width=150)
        except: st.subheader("PARENTE ANDRADE")
    with col2:
        busca = st.text_input("", placeholder="🔍 O que deseja consultar? (SC, Cotação, Pedido...)", label_visibility="collapsed")

    if busca:
        mask = df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df[mask]
    else:
        df_display = df

    # Definição das colunas com a Cotação entre SC e Pedido
    # Ajuste os nomes conforme aparecem no seu DataFrame
    cols_referencia = [
        "STATUS", "N° da SC", "Num. Cotacao", "Código Cotação", "N° PC", "CC", 
        "Nome Fornecedor", "Produto", "Descricao", "Data Emissao"
    ]
    cols_existentes = [c for c in cols_referencia if c in df_display.columns]

    st.dataframe(df_display[cols_existentes], use_container_width=True, hide_index=True)

    # Download
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as writer:
        df_display.to_excel(writer, index=False)
    st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "FollowUp_Completo.xlsx")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold;'>Suprimentos | Parente Andrade</p>", unsafe_allow_html=True)
