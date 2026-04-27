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
        border-radius: 8px; border: 2px solid #478c3b !important; margin: 0 !important;
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
    busca = st.text_input("", placeholder="🔍 Buscar SC, Pedido, Fornecedor...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 5. MOTOR DE INTELIGÊNCIA DE STATUS (CORRIGIDO)
def normalizar(val):
    if pd.isna(val) or str(val).lower() in ['nan', 'none', '']: return ""
    return str(val).split('.')[0].strip().lstrip('0')

@st.cache_data(ttl=600)
def carregar_e_processar_status_final():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]

        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [str(c).strip() for c in df_sc.columns]

        # 1. Unificar bases e criar chave de ligação
        df_m = pd.concat([df_pc, df_sc], ignore_index=True)
        df_m['CHAVE'] = df_m['Numero da SC'].apply(normalizar)
        
        # 2. Propagação agressiva de dados entre linhas da mesma SC
        cols_vinc = ["STATUS", "Num. Cotacao", "Numero Pedido", "CC", "Nome Fornecedor", "Data Emissao", "DT entrega"]
        for col in cols_vinc:
            if col in df_m.columns:
                df_m[col] = df_m[col].replace(['', 'nan', 'NaN', 'None'], pd.NA)
                # O ffill/bfill garante que se existir em uma linha, existirá em todas do mesmo Numero da SC
                df_m[col] = df_m.groupby('CHAVE')[col].transform(lambda x: x.ffill().bfill())

        # 3. Lógica Definitiva da Coluna STATUS
        def aplicar_status_inteligente(row):
            status_planilha = str(row.get('STATUS', '')).strip()
            cotacao = str(row.get('Num. Cotacao', '')).strip()
            
            # Se o status da planilha PC estiver vazio/nulo, mas houver cotação na SC
            if (status_planilha in ['', 'nan', 'NaN', '<NA>', 'None']) and (cotacao not in ['', 'nan', 'NaN', 'None']):
                return "EM COTAÇÃO"
            
            return status_planilha if status_planilha not in ['nan', '<NA>', 'None'] else ""

        df_m['STATUS'] = df_m.apply(aplicar_status_inteligente, axis=1)

        # 4. Limpeza e Formatação de Datas
        for col in df_m.columns:
            if any(d in col.upper() for d in ["DATA", "DT "]):
                df_m[col] = pd.to_datetime(df_m[col], errors='coerce').dt.strftime('%d/%m/%y')

        return df_m.fillna('')
    except Exception as e:
        st.error(f"Erro no processamento do Status: {e}")
        return pd.DataFrame()

df_ready = carregar_e_processar_status_final()

# Definição das colunas do painel (Num. Cotacao fica oculta, mas foi usada para o Status)
COL_VISIVEL = ["STATUS", "Numero da SC", "Numero Pedido", "CC", "Nome Fornecedor", "Produto", "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega"]

# 6. EXIBIÇÃO
if busca:
    t = busca.lower().strip()
    df_res = df_ready[df_ready.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
    
    if not df_res.empty:
        # Remove duplicatas para não repetir o mesmo item da SC e PC
        df_res = df_res.drop_duplicates(subset=['CHAVE', 'Produto', 'QNT', 'Descricao'])
        
        # Filtra apenas as colunas desejadas
        cols_existentes = [c for c in COL_VISIVEL if c in df_res.columns]
        df_final = df_res[cols_existentes]
        
        st.markdown(f'<div class="status-box">🟢 {len(df_res)} registros localizados e validados</div>', unsafe_allow_html=True)
        
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df_final.to_excel(wr, index=False)
        st.download_button("📥 DESCARREGAR RELATÓRIO", out.getvalue(), "Portal_Compras_PA.xlsx")
        
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.warning(f"Nenhum dado encontrado para: {busca}")
else:
    st.info("💡 Digite o termo de busca. O sistema verifica automaticamente se há cotações pendentes na aba SC.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
