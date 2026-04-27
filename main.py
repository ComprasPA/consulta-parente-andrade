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

# 2. FUNÇÃO LOGO (Local)
@st.cache_data(ttl=86400)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

base64_logo = get_base64_logo()

# 3. CSS (Título 40 e Layout)
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

# 4. FUNÇÃO DE CARREGAMENTO (Tratamento de Erro 400)
@st.cache_data(ttl=300)
def carregar_dados():
    # URL Base da sua planilha
    ID_PLANILHA = "1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP"
    URL_BASE = f"https://docs.google.com/spreadsheets/d/{ID_PLANILHA}/gviz/tq?tqx=out:csv"
    
    try:
        # Carrega a aba principal (Follow Up)
        # O parâmetro &sheet= permite usar o nome da aba em vez do GID, o que evita o Erro 400
        df_main = pd.read_csv(f"{URL_BASE}&sheet=SCM%20SILVIO", dtype=str).fillna('')
        
        try:
            # Tenta carregar a aba Protheus SC
            df_sc = pd.read_csv(f"{URL_BASE}&sheet=Protheus%20SC", dtype=str).fillna('')
            
            # Normalização para o PROCV
            df_main['N° da SC'] = df_main['N° da SC'].astype(str).str.zfill(7)
            col_sc_2 = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'Solicitação'
            
            if col_sc_2 in df_sc.columns:
                df_sc[col_sc_2] = df_sc[col_sc_2].astype(str).str.zfill(7)
                # Traz apenas a Cotação
                df_main = pd.merge(df_main, df_sc[[col_sc_2, 'Num. Cotacao']], 
                                  left_on='N° da SC', right_on=col_sc_2, how='left').fillna('')
        except:
            pass # Se a aba 2 falhar, segue apenas com a 1
            
        return df_main
    except Exception as e:
        st.error(f"Erro de Conexão: {e}. Verifique se a planilha está compartilhada como 'Qualquer pessoa com o link'.")
        return pd.DataFrame()

# 5. CABEÇALHO
col_logo, col_titulo, col_busca = st.columns([1, 4, 1.5])
with col_logo:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:140px;">', unsafe_allow_html=True)
with col_titulo:
    st.markdown('<div class="portal-title">Portal Gestão de Compras Parente Andrade</div>', unsafe_allow_html=True)
with col_busca:
    st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    busca = st.text_input("", placeholder="🔍 O que deseja consultar?", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 15px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 6. RESULTADOS
df_base = carregar_dados()

if busca and not df_base.empty:
    termo = busca.lower()
    mask = df_base.apply(lambda row: row.astype(str).str.lower().str.contains(termo).any(), axis=1)
    df_res = df_base[mask]

    if not df_res.empty:
        col_v = ["N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "STATUS"]
        cols_finais = [c for c in col_v if c in df_res.columns]

        c1, c2 = st.columns([3, 1])
        with c1: st.write(f"🟢 **{len(df_res)}** registros.")
        with c2:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                df_res[cols_finais].to_excel(wr, index=False)
            st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_PA.xlsx")

        st.dataframe(df_res[cols_finais], use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum resultado para '{busca}'.")
elif not busca:
    st.info("👋 Digite uma informação acima para iniciar a busca instantânea.")
