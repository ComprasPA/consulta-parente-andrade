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
@st.cache_data(ttl=86400)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return None

base64_logo = get_base64_logo()

# 3. CSS (DESIGN PADRÃO CONGELADO)
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    .header-wrapper {{
        border: 2px solid #478c3b; border-radius: 10px; padding: 15px 25px;
        background-color: #ffffff; display: flex; align-items: center;
        justify-content: space-between; margin-top: 10px; margin-bottom: 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}
    .portal-title {{ color: #000000 !important; font-size: 40px !important; font-weight: bold !important; margin: 0 !important; }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 0px 10px !important; 
        border-radius: 8px; border: 2px solid #478c3b !important;
    }}
    .status-box {{ background-color: #478c3b; color: white; padding: 12px 20px; border-radius: 10px; font-weight: bold; font-size: 18px; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO
st.markdown('<div class="header-wrapper">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.2, 5, 2.3])
with c1:
    if base64_logo: st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:140px;">', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="portal-title">Portal Gestão de Compras Parente Andrade</p>', unsafe_allow_html=True)
with c3:
    busca = st.text_input("", placeholder="🔍 Digite SC, SCM, Produto ou Fornecedor...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. MOTOR DE CONSOLIDAÇÃO BLINDADO
def normalizar_valor(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']: return ""
    return str(val).split('.')[0].strip().lstrip('0')

@st.cache_data(ttl=600)
def carregar_dados():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # Carrega e limpa nomes de colunas da aba PC
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str)
        df_pc.columns = [str(c).strip() for c in df_pc.columns]
        df_pc = df_pc.fillna('')

        # Localiza e limpa nomes de colunas da aba SC
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        if aba_sc_nome:
            df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str)
            df_sc.columns = [str(c).strip() for c in df_sc.columns]
            df_sc = df_sc.fillna('')
        else:
            df_sc = pd.DataFrame()

        # Identificação dinâmica das colunas de vínculo (evita erro de digitação)
        col_sc_pc = next((c for c in df_pc.columns if "SC" in c.upper() and "N" in c.upper()), "N° da SC")
        col_sc_sc = next((c for c in df_sc.columns if "SC" in c.upper() and "NUMERO" in c.upper()), "Numero da SC")

        # Criação da CHAVE de cruzamento (PROCV)
        df_pc['CHAVE'] = df_pc[col_sc_pc].apply(normalizar_valor)
        if not df_sc.empty:
            df_sc['CHAVE'] = df_sc[col_sc_sc].apply(normalizar_valor)

            # Cruzamento SC -> PC (Puxar Cotação e SCM)
            sc_map = df_sc[['CHAVE', 'Num. Cotacao', 'SCM']].drop_duplicates('CHAVE')
            df_pc = df_pc.merge(sc_map, on='CHAVE', how='left', suffixes=('', '_sc'))
            
            # Cruzamento PC -> SC (Puxar Pedido, Status, Fornecedor e CC)
            pc_map = df_pc[['CHAVE', 'STATUS', 'N° PC', 'Nome Fornecedor', 'CC', 'Data Emissao', 'DT entrega ']].drop_duplicates('CHAVE')
            df_sc = df_sc.merge(pc_map, on='CHAVE', how='left', suffixes=('', '_pc'))

            # Forçar preenchimento de lacunas em ambas as abas
            for df in [df_pc, df_sc]:
                for col in ['Num. Cotacao', 'SCM', 'STATUS', 'N° PC', 'Nome Fornecedor', 'CC']:
                    col_extra = f"{col}_sc" if f"{col}_sc" in df.columns else f"{col}_pc"
                    if col_extra in df.columns:
                        df[col] = df[col].replace('', pd.NA).fillna(df[col_extra]).fillna('')

        # Padroniza nomes para exibição uniforme
        df_sc = df_sc.rename(columns={col_sc_sc: "N° da SC"})
        return df_pc, df_sc

    except Exception as e:
        st.error(f"Erro no processamento das colunas: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_dados()

COLUNAS_PADRAO = ["STATUS", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]

# 6. BUSCA E EXIBIÇÃO
if busca:
    t = busca.lower().strip()
    
    # Filtra em ambas as bases enriquecidas
    res_pc = df_pc[df_pc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
    res_sc = df_sc[df_sc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]

    # Unifica resultados e remove duplicatas
    df_res = pd.concat([res_pc, res_sc], ignore_index=True)
    if not df_res.empty:
        df_res = df_res.drop_duplicates(subset=['CHAVE', 'Produto', 'QNT'])

    if not df_res.empty:
        for col in COLUNAS_PADRAO:
            if col not in df_res.columns: df_res[col] = ""
            
        df_final = df_res[COLUNAS_PADRAO].fillna('')
        st.markdown(f'<div class="status-box">🟢 {len(df_res)} registros localizados e vinculados</div>', unsafe_allow_html=True)
        
        # Download
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_final.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_Compras_PA.xlsx")
        
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum registro encontrado para: {busca}")
else:
    st.info("💡 Pesquise por SC, SCM, CC ou Fornecedor. O sistema preenche as lacunas automaticamente cruzando as abas.")
