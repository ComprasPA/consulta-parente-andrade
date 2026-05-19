import streamlit as st
import pandas as pd
import base64
import re
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
    except: 
        return None

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
        border-radius: 8px; border: 2px solid #478c3b !important; margin: 0 !important;
    }}
    .status-box {{ background-color: #478c3b; color: white; padding: 12px 20px; border-radius: 10px; font-weight: bold; font-size: 18px; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO COM BOTÃO DE ATUALIZAÇÃO FORÇADA
st.markdown('<div class="header-wrapper">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([1.2, 4.5, 1.3, 2.3])
with c1:
    if base64_logo: 
        st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:140px;">', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="portal-title">Portal Gestão de Compras Parente Andrade</p>', unsafe_allow_html=True)
with c3:
    if st.button("🔄 Atualizar Base", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with c4:
    busca = st.text_input("", placeholder="🔍 Digite SC ou Pedido...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# 5. NOVO SISTEMA DE MAPEAMENTO ROBUSTO
# ==========================================
# Define o nome que aparece na tela e uma lista de termos para o motor encontrar a coluna
MAPEAMENTO_MOCK = [
    {"label": "STATUS", "termos": ["STATUS"]},
    {"label": "Nº Solicitação (SC)", "termos": ["NUMERO", "SC"]},
    {"label": "Nº Pedido (PC)", "termos": ["NUMERO", "PC"]},
    {"label": "Centro de Custo", "termos": ["CENTRO", "CUSTO"]},
    {"label": "Fornecedor", "termos": ["NOME", "FORNECE"]},
    {"label": "Produto", "termos": ["PRODUTO"]},
    {"label": "Descrição", "termos": ["DESCRICAO"]},
    {"label": "UM", "termos": ["UNIDADE"]},
    {"label": "Qtd", "termos": ["QUANTIDADE"]},
    {"label": "Preço Unitário", "termos": ["PRC", "UNITARIO"]},
    {"label": "Valor Total", "termos": ["VLR", "TOTAL"]},
    {"label": "Data Emissão", "termos": ["DATA", "EMISSAO"]},
    {"label": "Data Liberação PC", "termos": ["LIB", "PC"]},
    {"label": "Data Envio", "termos": ["DT", "ENVIO"]},
    {"label": "Condição Pgto", "termos": ["CONDICAO", "PGO"]},
    {"label": "Data Pago À Vista", "termos": ["PGO", "AVISTA"]},
    {"label": "Prev. Entrega", "termos": ["PREV", "ENTREGA"]},
    {"label": "Data Entrega Real", "termos": ["DT", "ENTREGA"]},
    {"label": "Data Baixa", "termos": ["DT", "BAIXA"]},
    {"label": "Observação", "termos": ["OBSERVACAO"]}
]

def normalizar_texto(texto):
    # Remove acentos, espaços e caracteres especiais para comparação
    if not texto: return ""
    texto = str(texto).upper()
    texto = re.sub(r'[ÁÀÂÃ]', 'A', texto)
    texto = re.sub(r'[ÉÈÊ]', 'E', texto)
    texto = re.sub(r'[ÍÌÎ]', 'I', texto)
    texto = re.sub(r'[ÓÒÔÕ]', 'O', texto)
    texto = re.sub(r'[ÚÙÛ]', 'U', texto)
    texto = re.sub(r'[Ç]', 'C', texto)
    return re.sub(r'[^A-Z0-9]', '', texto)

def encontrar_coluna_original(df_colunas, lista_termos):
    # Varre as colunas reais da planilha buscando a melhor correspondência pelos termos chave
    for col in df_colunas:
        col_norm = normalizar_texto(col)
        # Verifica se todos os termos da lista estão contidos no nome da coluna normalizada
        if all(normalizar_texto(termo) in col_norm for termo in lista_termos):
            return col
    return None

@st.cache_data(ttl=60)
def carregar_dados_seguros():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # Carrega removendo espaços em branco extras das pontas das colunas
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [c.strip() for c in df_pc.columns]
        
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [c.strip() for c in df_sc.columns]
        
        return df_pc, df_sc
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_dados_seguros()


# ==========================================
# 6. LÓGICA DE BUSCA E MONTAGEM DA TABELA
# ==========================================
if busca:
    t = busca.lower().strip()
    
    # Realiza a busca no DataFrame completo de Pedidos (PC)
    res_pc = df_pc[df_pc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
    
    if not res_pc.empty:
        df_final = res_pc.copy()
        origem = "Planilha de Pedidos (PC)"
    else:
        # Se não achar na PC, busca na de Solicitações (SC)
        res_sc = df_sc[df_sc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
        if not res_sc.empty:
            df_final = res_sc.copy()
            
            # Inteligência de Status para registros na aba SC
            def definir_st(row):
                col_cot = encontrar_coluna_original(row.index, ["COTACAO"])
                val_cot = str(row[col_cot]).strip() if col_cot else ""
                if val_cot != "" and val_cot.lower() != "nan" and val_cot != "0":
                    return "EM COTAÇÃO"
                return "SC ABERTA"
            df_final['STATUS'] = df_final.apply(definir_st, axis=1)
            origem = "Planilha de Solicitações (SC)"
        else:
            df_final = pd.DataFrame()

    if not df_final.empty:
        # Constrói o painel com os índices corretos da busca
        df_painel = pd.DataFrame(index=df_final.index)
        
        for config in MAPEAMENTO_MOCK:
            nome_bonito = config["label"]
            termos_chave = config["termos"]
            
            # Localiza dinamicamente o nome real da coluna na planilha
            col_original = encontrar_coluna_original(df_final.columns, termos_chave)
            
            if col_original:
                # Tratamento unificado de datas para o formato nacional (DD/MM/AA)
                if any(x in normalizar_texto(col_original) for x in ["DATA", "DT", "PREV", "LIB"]):
                    datas_limpas = df_final[col_original].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    # Garante que campos vazios do Excel não virem erros de conversão
                    datas_limpas = datas_limpas.replace(['nan', 'NONE', ''], '')
                    df_painel[nome_bonito] = pd.to_datetime(datas_limpas, errors='coerce', format='mixed').dt.strftime('%d/%m/%y').fillna('')
                else:
                    df_painel[nome_bonito] = df_final[col_original]
            else:
                # Preenche com vazio se a coluna não pertencer à aba atual pesquisada
                df_painel[nome_bonito] = ""

        # Elimina linhas totalmente vazias
        df_painel = df_painel.dropna(how='all')

        st.markdown(f'<div class="status-box">🟢 Dados Vinculados de: {origem}</div>', unsafe_allow_html=True)
        st.write("")
        
        # Geração do arquivo para Download
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: 
            df_painel.to_excel(wr, index=False)
        
        st.download_button(
            label="📥 DESCARREGAR RELATÓRIO",
            data=out.getvalue(),
            file_name="Portal_Compras_Parente.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Exibição estruturada dos dados na tela
        st.dataframe(df_painel, use_container_width=True, hide_index=True)
    else:
        st.warning(f"⚠️ Nenhum registro localizado para: '{busca}'")
else:
    st.info("💡 Digite o número da SC ou Pedido para iniciar. Prioridade do Motor: PC (Completo) > SC (Pendente).")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
