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

# 2. FUNÇÃO LOGO (Cache de longa duração)
@st.cache_data(ttl=86400)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

base64_logo = get_base64_logo()

# 3. CSS OTIMIZADO
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    .portal-title {{ color: #000000 !important; font-size: 40px !important; font-weight: bold !important; text-align: center !important; margin:0;}}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 2px 10px !important; border-radius: 8px; border: 2px solid #478c3b;
    }}
    .stDownloadButton button {{ background-color: #f2a933 !important; color: white !important; font-weight: bold !important; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CARREGAMENTO ULTRA RÁPIDO (CSV GID)
@st.cache_data(ttl=300, show_spinner="Otimizando base de dados...")
def carregar_dados_leves():
    # Usando exportação CSV por GID (muito mais leve que XLSX)
    BASE_URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=csv"
    
    try:
        # Carrega Aba Principal (GID 0)
        df_main = pd.read_csv(f"{BASE_URL}&gid=0", dtype=str).fillna('')
        
        # Carrega Aba Protheus SC (Troque pelo GID correto da sua aba se necessário)
        # O GID da aba Protheus SC geralmente é o número longo no final da URL
        try:
            df_sc = pd.read_csv(f"{BASE_URL}&gid=1626027376", dtype=str).fillna('')
            
            # Normalização e Merge Relâmpago
            df_main['N° da SC'] = df_main['N° da SC'].astype(str).str.zfill(7)
            df_sc['Numero da SC'] = df_sc['Numero da SC'].astype(str).str.zfill(7)
            
            # Traz apenas a coluna necessária para não pesar a memória
            df_final = pd.merge(df_main, df_sc[['Numero da SC', 'Num. Cotacao']], 
                                left_on='N° da SC', right_on='Numero da SC', 
                                how='left').fillna('')
        except:
            df_final = df_main

        # Pré-processamento de datas para busca rápida
        cols_datas = ["DT Envio", "Data Emissao", "Dt Liberacao", "DT entrega "]
        for c in cols_datas:
            if c in df_final.columns:
                df_final[c] = pd.to_datetime(df_final[c], errors='coerce').dt.strftime('%d/%m/%y').fillna(df_final[c])
        
        return df_final
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# 5. CABEÇALHO
col_logo, col_titulo, col_busca = st.columns([1, 4, 1.5])
with col_logo:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:140px;">', unsafe_allow_html=True)
with col_titulo:
    st.markdown('<div class="portal-title">Portal Gestão de Compras Parente Andrade</div>', unsafe_allow_html=True)
with col_busca:
    st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    busca = st.text_input("", placeholder="🔍 Digite e aguarde...", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 15px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 6. FILTRAGEM INSTANTÂNEA
df_base = carregar_dados_leves()

if busca:
    # Filtro de alta performance
    termo = busca.lower()
    df_resultado = df_base[df_base.apply(lambda row: row.astype(str).str.lower().str.contains(termo).any(), axis=1)]

    if not df_resultado.empty:
        col_v = ["N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "STATUS"]
        cols_finais = [c for c in col_v if c in df_resultado.columns]

        c1, c2 = st.columns([3, 1])
        with c1: st.write(f"🟢 **{len(df_resultado)}** registros.")
        with c2:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                df_resultado[cols_finais].to_excel(wr, index=False)
            st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_PA.xlsx")

        st.dataframe(df_resultado[cols_finais], use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum registro encontrado.")
else:
    st.info("💡 Digite qualquer informação para pesquisar na base integrada.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
