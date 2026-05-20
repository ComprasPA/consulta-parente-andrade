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

# Inteligência de formatação para garantir os 10 dígitos do padrão Protheus
def formatar_codigo_10_digitos(valor):
    val_limpo = str(valor).split('.')[0].strip() # Remove pontuações ou .0 do Excel
    if val_limpo and val_limpo.lower() != 'nan' and val_limpo != '0':
        return val_limpo.zfill(10)
    return val_limpo

@st.cache_data(ttl=60)
def carregar_dados_seguros():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # Carrega a primeira aba (Pedidos / PC)
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]
        
        # Carrega a segunda aba (Solicitações / SC)
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [str(c).strip() for c in df_sc.columns]
        
        return df_pc, df_sc
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_dados_seguros()


# ==========================================
# 6. LÓGICA DE PROCV COM PRIORIDADE DE GUIA (PC -> SC)
# ==========================================
if busca:
    t = busca.lower().strip()
    
    # Tratamento para casar o termo digitado com os formatos de salvamento (com ou sem zeros à esquerda)
    t_10 = t.zfill(10) if t.isdigit() else t
    
    df_final = pd.DataFrame()
    origem = ""
    
    # ---- 1º PASSO: PROCV NA PLANILHA DE PEDIDOS (PC) ----
    # Procura o termo inserido especificamente dentro da coluna "Nº Solicitação (SC)"
    if not df_pc.empty and "Nº Solicitação (SC)" in df_pc.columns:
        col_sc_pc = df_pc["Nº Solicitação (SC)"].astype(str).str.lower().str.strip()
        res_pc = df_pc[(col_sc_pc == t) | (col_sc_pc == t_10)]
        
        if not res_pc.empty:
            df_final = res_pc.copy()
            origem = "Planilha de Pedidos (PC) - Registro Localizado"

    # ---- 2º PASSO: SE NÃO HOUVER DADOS NA PC, BUSCA NA PLANILHA DE SOLICITAÇÕES (SC) ----
    if df_final.empty and not df_sc.empty:
        # Tenta mapear o termo pela coluna padrão ou pela variação "SCM" se existir na tabela de SC
        col_busca_sc = "Nº Solicitação (SC)" if "Nº Solicitação (SC)" in df_sc.columns else (next((c for c in df_sc.columns if "SCM" in c.upper()), None))
        
        if col_busca_sc:
            col_sc_real = df_sc[col_busca_sc].astype(str).str.lower().str.strip()
            res_sc = df_sc[(col_sc_real == t) | (col_sc_real == t_10)]
            
            if not res_sc.empty:
                df_final = res_sc.copy()
                origem = "Planilha de Solicitações (SC) - Registro Localizado"

    # ---- MONTAGEM DA LISTA TRATADA PARA EXIBIÇÃO ----
    if not df_final.empty:
        df_painel = pd.DataFrame(index=df_final.index)
        
        for col_config in DICIONARIO_COLUNAS_EXATAS:
            nome_original_planilha = col_config["planilha"]
            nome_exibicao_tela = col_config["tela"]
            tipo_campo = col_config["tipo"]
            
            # Tratamento flexível de cabeçalho para unificar a visualização de "Nº Solicitação (SC)" e "SCM"
            col_real = nome_original_planilha
            if nome_original_planilha not in df_final.columns:
                if "SOLICITACAO" in nome_original_planilha.upper() or "SC" in nome_original_planilha.upper():
                    col_real = next((c for c in df_final.columns if "SCM" in c.upper() or "SC" in c.upper()), nome_original_planilha)

            if col_real in df_final.columns:
                valores_originais = df_final[col_real]
                
                if tipo_campo == "data":
                    # Limpeza e padronização para o formato brasileiro (DD/MM/AA)
                    datas_limpas = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    datas_limpas = datas_limpas.replace(['nan', 'NONE', '', '0'], '')
                    df_painel[nome_exibicao_tela] = pd.to_datetime(datas_limpas, errors='coerce', format='mixed').dt.strftime('%d/%m/%y').fillna('')
                
                elif tipo_campo == "pedido":
                    # Aplica o preenchimento de zeros à esquerda se faltar caracteres
                    df_painel[nome_exibicao_tela] = valores_originais.apply(formatar_codigo_10_digitos)
                
                else:
                    df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '').str.strip()
            else:
                # Se cair no fallback da SC (que não tem informações de fechamento), preenche com vazio ordenadamente
                if nome_exibicao_tela == "Nº Solicitação (SC)":
                    df_painel[nome_exibicao_tela] = busca.strip()
                else:
                    df_painel[nome_exibicao_tela] = ""

        # Força o status correto se a informação vier de uma requisição que ainda não virou pedido
        if origem.startswith("Planilha de Solicitações") and "STATUS" in df_painel.columns:
            df_painel["STATUS"] = df_painel["STATUS"].replace('', 'SC ABERTA')

        # Elimina linhas totalmente em branco
        df_painel = df_painel.dropna(how='all')

        st.markdown(f'<div class="status-box">🟢 {origem}</div>', unsafe_allow_html=True)
        st.write("")
        
        # Preparação do arquivo final para extração local
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: 
            df_painel.to_excel(wr, index=False)
        
        st.download_button(
            label="📥 DESCARREGAR RELATÓRIO",
            data=out.getvalue(),
            file_name="Portal_Compras_Parente.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Plota os dados organizados na tela
        st.dataframe(df_painel, use_container_width=True, hide_index=True)
    else:
        st.warning(f"⚠️ Nenhuma informação localizada para a SC: '{busca}' nas planilhas do sistema.")
else:
    st.info("💡 Digite o número da SC para iniciar. O motor buscará o histórico completo em Pedidos (PC) antes de recorrer às Solicitações (SC).")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
