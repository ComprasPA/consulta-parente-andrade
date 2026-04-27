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

# 5. MOTOR DE CONSOLIDAÇÃO TOTAL (VÍNCULO BIDIRECIONAL)
def normalizar_valor(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']: return ""
    return str(val).split('.')[0].strip().lstrip('0')

def formatar_datas(df):
    cols_data = ["Data Emissao", "Dt Liberacao", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]
    for col in cols_data:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%d/%m/%y').fillna('')
    return df

@st.cache_data(ttl=600)
def carregar_e_vincular_tudo():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # 1. Carregar Pedidos (PC)
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]

        # 2. Carregar Solicitações (SC)
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [str(c).strip() for c in df_sc.columns]

        # 3. Identificar Colunas Chave
        c_sc_pc = next((c for c in df_pc.columns if "N° DA SC" in c.upper() or "NUMERO DA SC" in c.upper()), "N° da SC")
        c_pc_pc = next((c for c in df_pc.columns if "N° PC" in c.upper() or "NUMERO PC" in c.upper()), "N° PC")
        c_sc_sc = next((c for c in df_sc.columns if "NUMERO DA SC" in c.upper() or "N° DA SC" in c.upper()), "Numero da SC")
        c_pc_sc = next((c for c in df_sc.columns if "N° PC" in c.upper() or "NUMERO PEDIDO" in c.upper()), "N° PC")

        # 4. Criar Chaves de Ligação Normatizadas
        df_pc['CHAVE'] = df_pc[c_sc_pc].apply(normalizar_valor)
        if not df_sc.empty:
            df_sc['CHAVE'] = df_sc[c_sc_sc].apply(normalizar_valor)

            # --- MAPA DE INFORMAÇÕES (O que cada aba tem de melhor) ---
            # O que a SC tem: Cotação, SCM
            sc_info = df_sc[['CHAVE', 'Num. Cotacao', 'SCM']].drop_duplicates('CHAVE')
            # O que a PC tem: Status, N° PC, Fornecedor, CC, Datas
            pc_info = df_pc[['CHAVE', 'STATUS', c_pc_pc, 'Nome Fornecedor', 'CC', 'Data Emissao', 'DT entrega ', 'DT Pgo (AVISTA)', 'DT Prev de Entrega']].drop_duplicates('CHAVE')

            # --- VÍNCULO BIDIRECIONAL (O CORAÇÃO DO CÓDIGO) ---
            # Levando dados da SC para a PC
            df_pc = df_pc.merge(sc_info, on='CHAVE', how='left', suffixes=('', '_vinc'))
            # Levando dados da PC para a SC
            df_sc = df_sc.merge(pc_info, on='CHAVE', how='left', suffixes=('', '_vinc'))

            # --- PREENCHIMENTO COMPULSÓRIO (Garantir que nada fique vazio) ---
            campos_cruzados = ['Num. Cotacao', 'SCM', 'STATUS', 'Nome Fornecedor', 'CC', 'Data Emissao', 'DT entrega ']
            
            # Preencher na PC
            for campo in campos_cruzados:
                if f"{campo}_vinc" in df_pc.columns:
                    df_pc[campo] = df_pc[campo].replace('', pd.NA).fillna(df_pc[f"{campo}_vinc"]).fillna('')
            
            # Preencher na SC (Incluindo o N° PC que é o alvo principal)
            for campo in campos_cruzados + [c_pc_pc]:
                col_extra = f"{campo}_vinc" if f"{campo}_vinc" in df_sc.columns else f"{c_pc_pc}_vinc"
                col_destino = campo if campo in df_sc.columns else c_pc_sc
                if col_extra in df_sc.columns:
                    df_sc[col_destino] = df_sc[col_destino].replace('', pd.NA).fillna(df_sc[col_extra]).fillna('')

        # 5. Padronização de nomes e Formatação de Datas
        df_pc = df_pc.rename(columns={c_sc_pc: "N° da SC", c_pc_pc: "N° PC"})
        df_sc = df_sc.rename(columns={c_sc_sc: "N° da SC", c_pc_sc: "N° PC"})
        
        df_pc = formatar_datas(df_pc)
        df_sc = formatar_datas(df_sc)

        return df_pc, df_sc

    except Exception as e:
        st.error(f"Erro na consolidação das abas: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_e_vincular_tudo()

COLUNAS_PADRAO = ["STATUS", "N° da SC", "Num. Cotacao", "N° PC", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "]

# 6. BUSCA E EXIBIÇÃO
if busca:
    t = busca.lower().strip()
    res_pc = df_pc[df_pc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)] if not df_pc.empty else pd.DataFrame()
    res_sc = df_sc[df_sc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)] if not df_sc.empty else pd.DataFrame()

    df_res = pd.concat([res_pc, res_sc], ignore_index=True)
    if not df_res.empty:
        # Remove duplicatas de cruzamento (mesma SC, Produto e QNT)
        df_res = df_res.drop_duplicates(subset=['CHAVE', 'Produto', 'QNT'])

        for col in COLUNAS_PADRAO:
            if col not in df_res.columns: df_res[col] = ""
            
        df_final = df_res[COLUNAS_PADRAO].fillna('')
        st.markdown(f'<div class="status-box">🟢 {len(df_res)} registros consolidados (PC + SC)</div>', unsafe_allow_html=True)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_final.to_excel(wr, index=False)
        st.download_button("📥 BAIXAR RESULTADO COMPLETO", out.getvalue(), "Relatorio_Compras_PA.xlsx")
        
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum registro encontrado para: {busca}")
else:
    st.info("💡 Digite um termo para pesquisar. O sistema vincula SC, Cotação e Pedido independente da aba original.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
