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

# 2. FUNÇÃO LOGO
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

base64_logo = get_base64_logo()

# 3. CSS PARA INTERFACE (Título 40 e Justificação)
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    
    .portal-title {{
        color: #000000 !important;
        font-size: 40px !important;
        font-weight: bold !important;
        text-align: center !important;
        margin-bottom: 10px !important;
        line-height: 1.1;
    }}

    /* Ajuste da Barra de Busca */
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
    }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
col_logo, col_titulo, col_busca = st.columns([1, 4, 1.5])
with col_logo:
    if base64_logo:
        st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:150px; height:auto;">', unsafe_allow_html=True)
with col_titulo:
    st.markdown('<div class="portal-title">Portal Gestão de Compras Parente Andrade</div>', unsafe_allow_html=True)
with col_busca:
    st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    busca = st.text_input("", placeholder="🔍 SC, Cotação ou Produto...", label_visibility="collapsed")

st.markdown("<div style='height: 4px; background-color: #f2a933; margin-top: 15px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO DE DADOS (INTEGRAÇÃO AMPLIADA)
URL_XLSX = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        excel_file = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        abas = excel_file.sheet_names
        
        # Carrega Aba 1 (Follow Up / PC)
        df_follow = pd.read_excel(excel_file, sheet_name=abas[0], dtype=str).fillna('')
        
        # Identifica a aba de SC de forma dinâmica
        aba_sc_nome = next((s for s in abas if "SC" in s.upper() or "PROTHEUS" in s.upper() and s != abas[0]), None)
        
        if aba_sc_nome:
            df_sc = pd.read_excel(excel_file, sheet_name=aba_sc_nome, dtype=str).fillna('')
            
            # Normaliza colunas de ligação
            col_sc_f = 'N° da SC' if 'N° da SC' in df_follow.columns else None
            col_sc_s = next((c for c in df_sc.columns if "NUMERO" in c.upper() and "SC" in c.upper() or "SOLICIT" in c.upper()), None)
            
            if col_sc_f and col_sc_s:
                df_follow[col_sc_f] = df_follow[col_sc_f].astype(str).str.zfill(7)
                df_sc[col_sc_s] = df_sc[col_sc_s].astype(str).str.zfill(7)
                
                # Puxa informações extras da aba SC para a principal
                # Exemplo: Código de Cotação
                cot_col = next((c for c in df_sc.columns if "COTACAO" in c.upper() or "COTAÇÃO" in c.upper()), None)
                
                if cot_col:
                    df_follow = pd.merge(df_follow, df_sc[[col_sc_s, cot_col]], 
                                        left_on=col_sc_f, right_on=col_sc_s, 
                                        how='left').fillna('')

        # Formatação de Datas para exibição brasileira
        for c in ["DT Envio", "Data Emissao", "Dt Liberacao", "DT entrega ", "DT Prev de Entrega"]:
            if c in df_follow.columns:
                df_follow[c] = pd.to_datetime(df_follow[c], errors='coerce').dt.strftime('%d/%m/%y').fillna(df_follow[c])
        
        return df_follow
    except Exception as e:
        st.error(f"Erro na integração: {e}")
        return None

df = carregar_dados()

# 6. EXIBIÇÃO
if df is not None:
    df_disp = df.copy()
    if busca:
        # A busca agora varre todas as colunas, incluindo as trazidas da aba SC
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
        st.write(f"🟢 **{len(df_disp)}** registros.")
    with c2:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as wr:
            df_disp[cols_finais].to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL", output.getvalue(), "PortalCompras_PA.xlsx")

    # st.column_config garante que a coluna STATUS fique justificada (alinhada) ao texto
    st.dataframe(
        df_disp[cols_finais], 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "STATUS": st.column_config.TextColumn("STATUS", width="medium", help="Status atual do processo"),
        }
    )

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
