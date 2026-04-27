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
    .portal-title {{ color: #000000 !important; font-size: 40px !important; font-weight: bold !important; text-align: center !important; }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 2px 10px !important; border-radius: 8px; border: 2px solid #478c3b;
    }}
    .stDownloadButton button {{ background-color: #f2a933 !important; color: white !important; font-weight: bold !important; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CARREGAMENTO GLOBAL EM CACHE (O SEGREDO DA VELOCIDADE)
# O Streamlit guardará a planilha na memória por 10 minutos (600s)
@st.cache_data(ttl=600, show_spinner="Atualizando base de dados...")
def carregar_base_completa():
    URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        # Baixa as abas uma única vez
        with pd.ExcelFile(URL_XLSX, engine='openpyxl') as excel:
            abas = excel.sheet_names
            df_main = pd.read_excel(excel, sheet_name=abas[0], dtype=str).fillna('')
            
            # Tenta integrar com a aba Protheus SC se existir
            aba_sc = next((s for s in abas if "SC" in s.upper() or "PROTHEUS" in s.upper() and s != abas[0]), None)
            if aba_sc:
                df_sc = pd.read_excel(excel, sheet_name=aba_sc, dtype=str).fillna('')
                col_sc_f = 'N° da SC' if 'N° da SC' in df_main.columns else None
                col_sc_s = next((c for c in df_sc.columns if "NUMERO" in c.upper() and "SC" in c.upper() or "SOLICIT" in c.upper()), None)
                
                if col_sc_f and col_sc_s:
                    df_main[col_sc_f] = df_main[col_sc_f].astype(str).str.zfill(7)
                    df_sc[col_sc_s] = df_sc[col_sc_s].astype(str).str.zfill(7)
                    cot_col = next((c for c in df_sc.columns if "COTACAO" in c.upper() or "COTAÇÃO" in c.upper()), None)
                    if cot_col:
                        df_main = pd.merge(df_main, df_sc[[col_sc_s, cot_col]], left_on=col_sc_f, right_on=col_sc_s, how='left').fillna('')
        
        # Padronização de datas prévia ao cache
        for c in ["DT Envio", "Data Emissao", "Dt Liberacao", "DT entrega ", "DT Prev de Entrega"]:
            if c in df_main.columns:
                df_main[c] = pd.to_datetime(df_main[c], errors='coerce').dt.strftime('%d/%m/%y').fillna(df_main[c])
        
        return df_main
    except Exception as e:
        st.error(f"Erro ao baixar planilha: {e}")
        return pd.DataFrame()

# 5. CABEÇALHO
col_logo, col_titulo, col_busca = st.columns([1, 4, 1.5])
with col_logo:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:150px;">', unsafe_allow_html=True)
with col_titulo:
    st.markdown('<div class="portal-title">Portal Gestão de Compras Parente Andrade</div>', unsafe_allow_html=True)
with col_busca:
    st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    busca = st.text_input("", placeholder="🔍 Digite e aperte Enter...", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 15px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 6. EXECUÇÃO DA BUSCA (INSTANTÂNEA)
# Carrega a base da memória (se já foi baixada uma vez, é instantâneo)
df_base = carregar_base_completa()

if busca:
    # Busca local via vetorização (muito mais rápido que loops)
    termo = busca.lower()
    mask = df_base.apply(lambda row: row.astype(str).str.lower().str.contains(termo).any(), axis=1)
    df_resultado = df_base[mask]

    if not df_resultado.empty:
        col_v = ["N° da SC", "Num. Cotacao", "Código Cotação", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "STATUS"]
        cols_finais = [c for c in col_v if c in df_resultado.columns]

        c1, c2 = st.columns([3, 1])
        with c1: st.write(f"🟢 **{len(df_resultado)}** registros encontrados.")
        with c2:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                df_resultado[cols_finais].to_excel(wr, index=False)
            st.download_button("📥 BAIXAR EXCEL", out.getvalue(), f"Pesquisa_PA.xlsx")

        st.dataframe(df_resultado[cols_finais], use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum registro para '{busca}'.")
else:
    st.info("💡 Digite o número da SC, Pedido ou Fornecedor para iniciar a consulta.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Suprimentos</p>", unsafe_allow_html=True)
