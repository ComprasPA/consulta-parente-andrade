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
# 5. NOVO DICIONÁRIO DE COLUNAS ALINHADO
# ==========================================
# Mapeia a "CHAVE LIMPA" para o "Nome Exato da Tela" baseado na nova lista da planilha
DICIONARIO_COLUNAS = {
    "STATUS": "STATUS",
    "NUMERODASC": "Nº Solicitação (SC)",
    "NUMEROPC": "Nº Pedido (PC)",
    "CENTROCUSTO": "Centro de Custo",
    "FORNECEDOR": "Cód. Fornecedor",
    "NOMEFORNECE": "Fornecedor",
    "PRODUTO": "Produto",
    "DESCRICAO": "Descrição",
    "UNIDADE": "UM",
    "QUANTIDADE": "Qtd",
    "PRCUNITARIO": "Preço Unitário",
    "VLRTOTAL": "Valor Total",
    "DATAEMISSAO": "Data Emissão",
    "DTLIBPC": "Data Liberação PC",
    "DTENVIO": "Data Envio",
    "CONDICAOPGO": "Condição Pgto",
    "DTPGOAVISTA": "Data Pago À Vista",
    "DTPREVDEENTREGA": "Prev. Entrega",
    "DTENTREGA": "Data Entrega Real",
    "OBSERVACAO": "Observação"
}

def limpar_nome_coluna(nome):
    # Tratamento para garantir o match mesmo se houver caracteres invisíveis
    return re.sub(r'[^a-zA-Z0-9]', '', str(nome)).upper()

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
                col_cot = next((c for c in row.index if "COTACAO" in limpar_nome_coluna(c)), None)
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
        
        for chave_limpa, nome_bonito in DICIONARIO_COLUNAS.items():
            # Procura o cabeçalho equivalente usando a higienização de strings
            col_original = next((c for c in df_final.columns if limpar_nome_coluna(c) == chave_limpa), None)
            
            if col_original:
                # Tratamento unificado de datas para o formato nacional (DD/MM/AA)
                if "DATA" in chave_limpa or "DT" in chave_limpa:
                    datas_limpas = df_final[col_original].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    df_painel[nome_bonito] = pd.to_datetime(datas_limpas, errors='coerce', format='mixed').dt.strftime('%d/%m/%y').fillna('')
                else:
                    df_painel[nome_bonito] = df_final[col_original]
            else:
                # Preenche com vazio se a coluna não pertencer à aba atual pesquisada
                df_painel[nome_bonito] = ""

        # Elimina linhas fantasmas do processamento
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
