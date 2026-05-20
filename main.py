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
    busca = st.text_input("", placeholder="🔍 Digite o número da SC...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# 5. ESTRUTURA DE COLUNAS CORRIGIDA (TEXTO EXATO)
# ==========================================
DICIONARIO_COLUNAS_EXATAS = [
    {"planilha": "STATUS", "tela": "STATUS", "tipo": "texto"},
    {"planilha": "Envio", "tela": "Envio", "tipo": "data"},
    {"planilha": "Pagamento", "tela": "Pagamento", "tipo": "data"},
    {"planilha": "Previsão de entrega", "tela": "Previsão de entrega", "tipo": "data"},
    {"planilha": "Entrega", "tela": "Entrega", "tipo": "data"},
    {"planilha": "Condição Pagamento", "tela": "Condição Pagamento", "tipo": "texto"},
    {"planilha": "Nº Solicitação (SC)", "tela": "Nº Solicitação (SC)", "tipo": "texto"},
    {"planilha": "Nº Pedido (PC)", "tela": "Nº Pedido (PC)", "tipo": "pedido"}, 
    {"planilha": "Fornecedor", "tela": "Fornecedor", "tipo": "texto"},
    {"planilha": "Centro de Custo (CC)", "tela": "Centro de Custo (CC)", "tipo": "texto"},
    {"planilha": "Produto", "tela": "Produto", "tipo": "texto"},
    {"planilha": "Descricao", "tela": "Descrição", "tipo": "texto"},
    {"planilha": "UM", "tela": "UM", "tipo": "texto"},
    {"planilha": "Qtd", "tela": "Qtd", "tipo": "texto"},
    {"planilha": "Preço Unitário", "tela": "Preço Unitário", "tipo": "texto"},
    {"planilha": "Valor Total", "tela": "Valor Total", "tipo": "texto"},
    {"planilha": "Data Emissao", "tela": "Data Emissão", "tipo": "data"},
    {"planilha": "Data Liberação", "tela": "Data Liberação", "tipo": "data"}
]

def formatar_codigo_10_digitos(valor):
    val_limpo = str(valor).split('.')[0].strip()
    if val_limpo and val_limpo.lower() != 'nan' and val_limpo != '0':
        return val_limpo.zfill(10)
    return val_limpo

@st.cache_data(ttl=60)
def carregar_dados_seguros():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # Carrega a guia Protheus PC (Pedidos)
        aba_pc_nome = next((s for s in excel.sheet_names if "PC" in s.upper()), excel.sheet_names[0])
        df_pc = pd.read_excel(excel, sheet_name=aba_pc_nome, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]
        
        # Carrega a guia Protheus SC (Solicitações)
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != aba_pc_nome), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [str(c).strip() for c in df_sc.columns]
        
        return df_pc, df_sc
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_dados_seguros()


# ==========================================
# 6. LÓGICA DE PROCV COM PRIORIDADE DE GUIA
# ==========================================
if busca:
    t = busca.lower().strip()
    
    # Prepara o número da SC pura e também com preenchimento de zeros (caso inserido incompleto)
    t_10 = t.zfill(10) if t.isdigit() else t
    
    df_final = pd.DataFrame()
    origem = ""
    
    # ---- PASSO 1: PROCV NA GUIA "Protheus PC" (Coluna Nº Solicitação (SC)) ----
    if not df_pc.empty and "Nº Solicitação (SC)" in df_pc.columns:
        # Filtra na coluna D da PC se ela contém o número procurado
        col_sc_pc = df_pc["Nº Solicitação (SC)"].astype(str).str.lower().str.strip()
        res_pc = df_pc[(col_sc_pc == t) | (col_sc_pc == t_10)]
        
        if not res_pc.empty:
            df_final = res_pc.copy()
            origem = "Guia Protheus PC (Pedido Vinculado)"

    # ---- PASSO 2: SE NÃO ACHOU NO PEDIDO, PROCV NA GUIA "Protheus SC" ----
    if df_final.empty and not df_sc.empty:
        # Tenta mapear o termo tanto na coluna oficial quanto na variação "SCM" se houver
        col_busca_sc = "Nº Solicitação (SC)" if "Nº Solicitação (SC)" in df_sc.columns else (next((c for c in df_sc.columns if "SCM" in c.upper()), None))
        
        if col_busca_sc:
            col_sc_real = df_sc[col_busca_sc].astype(str).str.lower().str.strip()
            res_sc = df_sc[(col_sc_real == t) | (col_sc_real == t_10)]
            
            if not res_sc.empty:
                df_final = res_sc.copy()
                origem = "Guia Protheus SC (Solicitação Aberta)"

    # ---- MONTAGEM DA TABELA TRATADA ----
    if not df_final.empty:
        df_painel = pd.DataFrame(index=df_final.index)
        
        for col_config in DICIONARIO_COLUNAS_EXATAS:
            nome_original_planilha = col_config["planilha"]
            nome_exibicao_tela = col_config["tela"]
            tipo_campo = col_config["tipo"]
            
            # Se a coluna não existir com o nome padrão (Ex: SCM na aba SC), tenta achar o equivalente por posição ou nome parcial
            col_real = nome_original_planilha
            if nome_original_planilha not in df_final.columns:
                if "SOLICITACAO" in nome_original_planilha.upper() or "SC" in nome_original_planilha.upper():
                    col_real = next((c for c in df_final.columns if "SCM" in c.upper() or "SC" in c.upper()), nome_original_planilha)

            if col_real in df_final.columns:
                valores_originais = df_final[col_real]
                
                if tipo_campo == "data":
                    datas_limpas = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    datas_limpas = datas_limpas.replace(['nan', 'NONE', '', '0'], '')
                    df_painel[nome_exibicao_tela] = pd.to_datetime(datas_limpas, errors='coerce', format='mixed').dt.strftime('%d/%m/%y').fillna('')
                
                elif tipo_campo == "pedido":
                    df_painel[nome_exibicao_tela] = valores_originais.apply(formatar_codigo_10_digitos)
                
                else:
                    df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '').str.strip()
            else:
                # Garante que a coluna Nº Solicitação na tela receba o dado da busca caso venha da SCM
                if nome_exibicao_tela == "Nº Solicitação (SC)":
                    df_painel[nome_exibicao_tela] = busca.zfill(6) if busca.isdigit() else busca
                else:
                    df_painel[nome_exibicao_tela] = ""

        # Remove linhas redundantes
        df_painel = df_painel.dropna(how='all')

        st.markdown(f'<div class="status-box">🟢 {origem}</div>', unsafe_allow_html=True)
        st.write("")
        
        # Arquivo de Download
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: 
            df_painel.to_excel(wr, index=False)
        
        st.download_button(
            label="📥 DESCARREGAR RELATÓRIO",
            data=out.getvalue(),
            file_name="Portal_Compras_Parente.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Mostra os dados estruturados na tela
        st.dataframe(df_painel, use_container_width=True, hide_index=True)
    else:
        st.warning(f"⚠️ Nenhuma informação localizada para a SC: '{busca}' nas guias PC ou SC.")
else:
    st.info("💡 Insira o número da SC. O sistema buscará primeiro o histórico em 'Protheus PC' e, caso não encontre, trará os dados da 'Protheus SC'.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
