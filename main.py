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

# 3. CSS (DESIGN PADRÃO)
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
    .portal-title {{ color: #000000 !important; font-size: 35px !important; font-weight: bold !important; margin: 0 !important; }}
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

# 5. MOTOR DE CONSOLIDAÇÃO (COLUNAS PADRONIZADAS)
def normalizar_valor(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']: return ""
    return str(val).split('.')[0].strip().lstrip('0')

def formatar_datas(df):
    for col in df.columns:
        if any(d.upper() in col.upper() for d in ["DATA", "DT "]):
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%y').fillna('')
    return df

@st.cache_data(ttl=600)
def carregar_dados_padronizados():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # Carrega as duas abas
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]

        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [str(c).strip() for c in df_sc.columns]

        # Vínculo bidirecional usando a chave "Numero da SC"
        if "Numero da SC" in df_pc.columns and not df_sc.empty and "Numero da SC" in df_sc.columns:
            df_pc['CHAVE'] = df_pc["Numero da SC"].apply(normalizar_valor)
            df_sc['CHAVE'] = df_sc["Numero da SC"].apply(normalizar_valor)

            # Colunas para cruzar (exatamente como você renomeou)
            cols_de_pc = [c for c in ['CHAVE', 'STATUS', 'Numero Pedido', 'Nome Fornecedor', 'CC', 'Data Emissao', 'DT entrega'] if c in df_pc.columns]
            cols_de_sc = [c for c in ['CHAVE', 'Num. Cotacao', 'SCM'] if c in df_sc.columns]

            pc_info = df_pc[cols_de_pc].drop_duplicates('CHAVE')
            sc_info = df_sc[cols_de_sc].drop_duplicates('CHAVE')

            # Merge bidirecional
            df_pc = df_pc.merge(sc_info, on='CHAVE', how='left', suffixes=('', '_vinc'))
            df_sc = df_sc.merge(pc_info, on='CHAVE', how='left', suffixes=('', '_vinc'))

            # Preenchimento de lacunas (se o dado veio do vínculo, ele assume a célula vazia)
            for df in [df_pc, df_sc]:
                for col in df.columns:
                    if col.endswith('_vinc'):
                        orig = col.replace('_vinc', '')
                        if orig in df.columns:
                            df[orig] = df[orig].replace('', pd.NA).fillna(df[col]).fillna('')

        # Formatação de datas
        df_pc = formatar_datas(df_pc)
        df_sc = formatar_datas(df_sc)

        return df_pc, df_sc

    except Exception as e:
        st.error(f"Erro ao processar as colunas padronizadas: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_dados_padronizados()

# Colunas do Painel ajustadas conforme sua solicitação
COLUNAS_PAINEL = ["STATUS", "Numero da SC", "Num. Cotacao", "Numero Pedido", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega"]

# 6. EXIBIÇÃO
if busca:
    t = busca.lower().strip()
    res_pc = df_pc[df_pc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)] if not df_pc.empty else pd.DataFrame()
    res_sc = df_sc[df_sc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)] if not df_sc.empty else pd.DataFrame()

    df_res = pd.concat([res_pc, res_sc], ignore_index=True)
    if not df_res.empty:
        if 'CHAVE' in df_res.columns:
            df_res = df_res.drop_duplicates(subset=['CHAVE', 'Produto', 'QNT'])
        
        # Garante que todas as colunas do painel existam no resultado
        for c in COLUNAS_PAINEL:
            if c not in df_res.columns: df_res[c] = ""
            
        df_final = df_res[COLUNAS_PAINEL].fillna('')
        st.markdown(f'<div class="status-box">🟢 {len(df_res)} registros localizados e vinculados</div>', unsafe_allow_html=True)
        
        # Excel
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_final.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR EXCEL", out.getvalue(), "Portal_Compras_PA.xlsx")
        
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum registro para: {busca}")
else:
    st.info("💡 Colunas padronizadas: Numero da SC, Num. Cotacao e Numero Pedido. Datas em DD/MM/YY.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
