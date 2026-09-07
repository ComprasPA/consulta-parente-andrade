import streamlit as st
import pandas as pd
import base64
import re
import unicodedata
from datetime import datetime, timedelta
from io import BytesIO
import urllib.request
import gspread
from google.oauth2.service_account import Credentials

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

# 3. CSS MODERNIZADO
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Public+Sans:wght@400;500;600;700&family=Space+Mono:wght@400;700&display=swap');
    :root {
        --pa-verde: #3E8E41;
        --pa-verde-deep: #2E6B31;
        --pa-verde-soft: #E7F3E6;
        --pa-laranja: #F2861D;
        --pa-laranja-deep: #CE6E10;
        --pa-laranja-soft: #FDECD9;
        --pa-ink: #1C2420;
        --pa-paper: #FFFFFF;
        --pa-input-bg: #F1F2EE;
        --pa-mist: #E4E7E0;
        --pa-slate: #5B6459;
        --pa-slate-soft: #8B9186;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    div[data-testid="stElementToolbar"] { display: none !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }
    html, body, .stApp, [class*="css"] { font-family: 'Public Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important; }
    .stApp { background-color: var(--pa-paper); }
    div.st-key-header_card { background: #ffffff; padding: 16px 28px; border-radius: 14px; margin-top: 0px !important; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(28,36,32,.04), 0 10px 28px -14px rgba(28,36,32,.14); position: relative; overflow: hidden; }
    div.st-key-header_card::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 6px; background: linear-gradient(180deg, var(--pa-verde), var(--pa-laranja)); }
    div.st-key-header_card > div { align-items: center; }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    .center-title-container { width: 100%; text-align: center; display: flex; justify-content: center; align-items: center; }
    .portal-title { font-family: 'Sora', sans-serif !important; color: var(--pa-ink) !important; font-size: 26px !important; font-weight: 700 !important; margin: 0 auto !important; letter-spacing: -0.01em; line-height: 1; white-space: nowrap; }
    .brand-text-block { display: flex; flex-direction: column; align-items: center; line-height: 1.35; }
    .brand-eyebrow { font-family: 'Public Sans', sans-serif; font-weight: 700; font-size: 15.75px; letter-spacing: .12em; text-transform: uppercase; color: var(--pa-laranja-deep); margin: 0; display: block; white-space: nowrap; }
    .brand-subtitle { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 22.5px; color: var(--pa-slate); display: block; white-space: nowrap; }
    div[data-testid="stVerticalBlock"] > div:has(input), div[data-testid="stVerticalBlock"] > div:has(select), div[data-testid="stVerticalBlock"] > div:has(button) { background-color: transparent; padding: 2px 0 !important; border: none !important; box-shadow: none !important; width: 100%; }
    div[data-testid="stTextInput"] input, div[data-testid="stDateInput"] [role="group"], div[data-testid="stSelectbox"] [role="group"], div[data-baseweb="select"] > div, div[data-baseweb="base-input"] { background-color: var(--pa-input-bg) !important; border: none !important; border-radius: 9px !important; box-shadow: none !important; transition: background-color 0.2s; }
    div[data-testid="stTextInput"] input:focus, div[data-testid="stDateInput"] [role="group"]:focus-within, div[data-testid="stSelectbox"] [role="group"]:focus-within, div[data-baseweb="select"] > div:focus-within, div[data-baseweb="base-input"]:focus-within { background-color: var(--pa-verde-soft) !important; }
    div[data-testid="stDateInput"] input, div[data-testid="stSelectbox"] input { background-color: transparent !important; }
    div[data-testid="stExpander"] { background-color: #ffffff !important; border: 1px solid var(--pa-mist) !important; border-radius: 16px !important; box-shadow: 0 1px 2px rgba(28,36,32,.04), 0 10px 28px -14px rgba(28,36,32,.14) !important; margin-bottom: 16px; }
    div[data-testid="stExpander"] > div, div[data-testid="stExpander"][data-open="true"], div[data-testid="stExpander"][data-open="false"], .stElementContainer:has(div[data-testid="stExpander"]) { background-color: transparent !important; border: none !important; border-width: 0px !important; box-shadow: none !important; outline: none !important; }
    div[data-testid="stExpander"] summary { padding: 14px 22px !important; }
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] { padding: 0 22px 22px !important; }
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] > div[data-testid="stVerticalBlock"] { gap: 0.35rem !important; }
    div[data-testid="stExpander"] summary, div[data-testid="stExpander"] [role="button"], .streamlit-expanderHeader { background-color: transparent !important; border: none !important; border-width: 0px !important; box-shadow: none !important; display: inline-flex !important; justify-content: flex-end !important; flex-direction: row !important; float: right !important; text-align: right !important; gap: 8px !important; width: auto !important; }
    div[data-testid="stExpander"] summary svg { transition: transform 0.2s ease-in-out !important; margin: 0 !important; padding: 0 !important; }
    div[data-testid="stExpander"] summary p, div[data-testid="stExpander"] [data-open="true"] summary p, .streamlit-expanderHeader p, .streamlit-expanderHeader:focus p { font-family: 'Sora', sans-serif !important; color: var(--pa-ink) !important; font-weight: 700 !important; font-size: 15px !important; margin: 0 !important; }
    div[data-testid="stExpander"] summary:hover p { color: var(--pa-verde) !important; }
    div[data-testid="stDateInput"] { width: 100%; }
    div[data-testid="stForm"] { border: none !important; padding: 0px !important; box-shadow: none !important; background-color: transparent !important; }

    div.stFormSubmitButton > button { width: 100% !important; min-height: 27px !important; max-height: 27px !important; font-size: 10px !important; font-weight: 600 !important; padding: 0px 6px !important; border-radius: 7px !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: clip !important; }
    div.stFormSubmitButton > button p { white-space: nowrap !important; }
    div.stFormSubmitButton > button[kind="primary"] { background-color: var(--pa-verde) !important; border-color: var(--pa-verde) !important; color: #fff !important; }
    div.stFormSubmitButton > button[kind="primary"]:hover { background-color: var(--pa-verde-deep) !important; border-color: var(--pa-verde-deep) !important; }
    div.stFormSubmitButton > button[kind="secondary"] { background-color: #ffffff !important; border-color: var(--pa-mist) !important; color: var(--pa-ink) !important; }
    div.stFormSubmitButton > button[kind="secondary"]:hover { border-color: var(--pa-slate-soft) !important; }

    div.stButton > button, div.stDownloadButton > button { border-radius: 7px !important; font-weight: 600 !important; min-height: 27px !important; font-size: 10px !important; padding: 0px 10px !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: clip !important; }
    div.stButton > button p, div.stDownloadButton > button p { white-space: nowrap !important; }
    div.stButton > button[kind="primary"], div.stDownloadButton > button[kind="primary"] { background-color: var(--pa-verde) !important; border-color: var(--pa-verde) !important; color: #fff !important; }
    div.stButton > button[kind="primary"]:hover, div.stDownloadButton > button[kind="primary"]:hover { background-color: var(--pa-verde-deep) !important; border-color: var(--pa-verde-deep) !important; }
    div.stButton > button[kind="secondary"], div.stDownloadButton > button[kind="secondary"] { background-color: #ffffff !important; border-color: var(--pa-mist) !important; color: var(--pa-ink) !important; }
    div.stButton > button[kind="secondary"]:hover, div.stDownloadButton > button[kind="secondary"]:hover { border-color: var(--pa-slate-soft) !important; }
    div.st-key-btn_sair button { background-color: #ffffff !important; border-color: #f3c6c6 !important; color: #c53030 !important; }
    div.st-key-btn_sair button:hover { background-color: #fceaea !important; border-color: #c53030 !important; }
    div.st-key-acoes_painel_wrap { flex-direction: row !important; align-items: center !important; justify-content: flex-start !important; gap: 12px !important; width: fit-content !important; margin-bottom: 10px; }
    div.st-key-acoes_painel_wrap div.stDownloadButton, div.st-key-acoes_painel_wrap div.stButton { width: fit-content !important; flex: 0 0 auto !important; }
    div.st-key-acoes_painel_wrap div.stDownloadButton > button, div.st-key-acoes_painel_wrap div.stButton > button { width: auto !important; }

    .status-card { background: #ffffff; color: var(--pa-ink); padding: 16px 24px; border-radius: 10px; font-weight: 600; font-size: 15px; border-left: 5px solid var(--pa-verde); box-shadow: 0 1px 3px rgba(28,36,32,.05); margin-bottom: 16px; width: 100%; }
    .custom-error-red { background-color: #fceaea !important; color: #b3282d !important; padding: 16px 24px; border-radius: 10px; font-weight: 600; font-size: 15px; box-shadow: 0 4px 6px -1px rgba(28,36,32,.05); margin-bottom: 16px; width: 100%; border-left: 5px solid #d8383d; }
    .custom-welcome-salutation, .custom-empty-state { background-color: #ffffff; color: var(--pa-ink); padding: 32px 24px; border-radius: 14px; font-weight: 600; font-size: 19px; text-align: center; border: 1px solid var(--pa-mist); box-shadow: 0 4px 6px -1px rgba(28,36,32,.02); margin-top: 20px; min-height: calc(100vh - 220px); display: flex; align-items: center; justify-content: center; box-sizing: border-box; }
    .custom-empty-state.custom-error-red { background-color: #fceaea !important; color: #b3282d !important; border: none; border-left: 5px solid #d8383d; box-shadow: 0 4px 6px -1px rgba(28,36,32,.05); }

    div[data-testid="stDataFrame"] { background: #ffffff; padding: 16px; border-radius: 14px; box-shadow: 0 1px 2px rgba(28,36,32,.04), 0 10px 28px -14px rgba(28,36,32,.14); }
    div[data-testid="stDataFrame"] table th { font-family: 'Public Sans', sans-serif !important; font-weight: 700 !important; letter-spacing: .04em; text-transform: uppercase; font-size: 11px !important; color: var(--pa-slate-soft) !important; white-space: nowrap !important; min-width: max-content !important; background: var(--pa-paper) !important; }
    div[data-testid="stDataFrame"] table td { font-family: 'Public Sans', sans-serif !important; }

    /* Cabecalho da tabela e area de filtros fixos; so a grade de dados rola */
    div[data-testid="stDataFrame"] { max-height: calc(100vh - 220px) !important; overflow: auto !important; }

    /* ESTILIZAÇÃO DO DROPDOWN / LISTA SUSPENSA */
    div[data-baseweb="menu"], ul[data-baseweb="menu"], div[role="listbox"] {
        background-color: #ffffff !important;
        color: var(--pa-ink) !important;
        border: 1px solid var(--pa-mist) !important;
        box-shadow: 0 10px 15px -3px rgba(28,36,32,.1) !important;
        width: max-content !important;
        min-width: 100% !important;
    }
    div[data-baseweb="menu"] li, ul[data-baseweb="menu"] li, div[role="option"] {
        background-color: #ffffff !important;
        color: var(--pa-ink) !important;
        white-space: nowrap !important;
        width: auto !important;
        padding-right: 24px !important;
    }
    div[data-baseweb="menu"] li:hover, ul[data-baseweb="menu"] li:hover, div[role="option"]:hover {
        background-color: var(--pa-verde-soft) !important;
        color: var(--pa-verde-deep) !important;
    }

    .custom-footer-block { text-align: center !important; margin-top: 60px !important; border-top: 1px solid var(--pa-mist) !important; padding-top: 24px !important; padding-bottom: 24px !important; position: static !important; clear: both !important; width: 100% !important; display: block !important; }
    .signature-fixed { position: fixed; bottom: 12px; left: 20px; color: var(--pa-slate-soft); font-size: 11px; font-weight: 700; letter-spacing: 0.5px; z-index: 999999; pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

FILE_ID = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"

# Sentinela de _row_idx pras linhas sinteticas "Em Cotação" (Solicitação sem
# Pedido ainda) - bem acima de qualquer linha real possivel na aba Pedidos,
# usado pra bloquear salvamento nelas (ver "SALVAMENTO PROCV" mais abaixo).
SENTINELA_ROW_IDX_EM_COTACAO = 10_000_000


def _ler_aba_como_df(spreadsheet, nome_aba):
    """Le uma aba inteira e devolve um DataFrame de strings, mesma logica de
    normalizacao (linhas curtas preenchidas com "") usada pra 'Pedidos'."""
    try:
        worksheet = spreadsheet.worksheet(nome_aba)
    except Exception:
        return pd.DataFrame()

    dados = worksheet.get_all_values()
    if not dados:
        return pd.DataFrame()

    cabecalho = [str(c).strip() for c in dados[0]]
    linhas_normalizadas = []
    for linha in dados[1:]:
        linha = list(linha)
        while len(linha) < len(cabecalho):
            linha.append("")
        linhas_normalizadas.append(linha[:len(cabecalho)])

    return pd.DataFrame(linhas_normalizadas, columns=cabecalho, dtype=str).fillna('')


def montar_linhas_em_cotacao(df_pc, df_sc):
    """Solicitações sem PEDIDO proprio preenchido E sem nenhuma linha
    correspondente (mesma Solicitação+Produto) na aba Pedidos - ainda não
    viraram pedido. Devolve um DataFrame com as MESMAS colunas de df_pc,
    STATUS="Em Cotação" e so os campos que fazem sentido pra uma Solicitação
    preenchidos (Centro de Custo, Solicitação, Produto, Descrição, Um, Qtd);
    o resto (Pedido, Fornecedor, datas, valores...) fica em branco. Some do
    resultado sozinha assim que a importação do PC correspondente criar a
    linha real na aba Pedidos - nao precisa de nenhum passo de "substituição"
    manual, e so essa mesma verificação rodando de novo."""
    colunas_normalizadas_pc = {c.upper().strip().replace('Í', 'I').replace('Ã', 'A').replace('Ç', 'C'): c for c in df_pc.columns}
    col_solic_pc = colunas_normalizadas_pc.get("SOLICITAÇÃO") or colunas_normalizadas_pc.get("SOLICITACAO")
    col_produto_pc = colunas_normalizadas_pc.get("PRODUTO")
    col_status_pc = colunas_normalizadas_pc.get("STATUS")

    if df_sc.empty or not col_solic_pc or not col_produto_pc:
        return pd.DataFrame(columns=df_pc.columns)

    chaves_com_pedido = set(zip(
        df_pc[col_solic_pc].astype(str).str.strip(),
        df_pc[col_produto_pc].astype(str).str.strip(),
    ))

    colunas_normalizadas_sc = {c.upper().strip().replace('Í', 'I').replace('Ã', 'A').replace('Ç', 'C'): c for c in df_sc.columns}
    col_solic_sc = colunas_normalizadas_sc.get("SOLICITAÇÃO") or colunas_normalizadas_sc.get("SOLICITACAO")
    col_pedido_sc = colunas_normalizadas_sc.get("PEDIDO")
    col_produto_sc = colunas_normalizadas_sc.get("PRODUTO")

    if not (col_solic_sc and col_pedido_sc and col_produto_sc):
        return pd.DataFrame(columns=df_pc.columns)

    sem_pedido = df_sc[df_sc[col_pedido_sc].astype(str).str.strip() == ""]
    if sem_pedido.empty:
        return pd.DataFrame(columns=df_pc.columns)

    chaves_sc = list(zip(
        sem_pedido[col_solic_sc].astype(str).str.strip(),
        sem_pedido[col_produto_sc].astype(str).str.strip(),
    ))
    candidatas = sem_pedido[[chave not in chaves_com_pedido for chave in chaves_sc]]
    if candidatas.empty:
        return pd.DataFrame(columns=df_pc.columns)

    linhas_cotacao = pd.DataFrame("", index=range(len(candidatas)), columns=df_pc.columns)
    if col_status_pc:
        linhas_cotacao[col_status_pc] = "EM COTAÇÃO"

    mapa_sc_para_pc = {
        "SOLICITACAO": col_solic_sc,
        "PRODUTO": col_produto_sc,
        "DESCRICAO": colunas_normalizadas_sc.get("DESCRICAO"),
        "UM": colunas_normalizadas_sc.get("UM"),
        "QTD": colunas_normalizadas_sc.get("QTD"),
        "CENTRO DE CUSTO": colunas_normalizadas_sc.get("CENTRO DE CUSTO"),
    }
    for campo_pc, col_real_sc in mapa_sc_para_pc.items():
        col_destino = colunas_normalizadas_pc.get(campo_pc)
        if col_destino and col_real_sc:
            linhas_cotacao[col_destino] = candidatas[col_real_sc].values

    linhas_cotacao.index = range(SENTINELA_ROW_IDX_EM_COTACAO, SENTINELA_ROW_IDX_EM_COTACAO + len(linhas_cotacao))
    return linhas_cotacao


# 4. CARREGAMENTO SEGURO DIRETO DA ABA "Pedidos" (+ Solicitações sem pedido, como "Em Cotação")
@st.cache_data(ttl=60)
def carregar_dados_seguros():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)

        spreadsheet = client.open_by_key(FILE_ID)
        try:
            worksheet = spreadsheet.worksheet("Pedidos")
        except:
            worksheet = spreadsheet.get_worksheet(0)

        dados = worksheet.get_all_values()
        if not dados:
            return pd.DataFrame()

        cabecalho = [str(c).strip() for c in dados[0]]
        linhas = dados[1:]

        linhas_normalizadas = []
        for linha in linhas:
            while len(linha) < len(cabecalho):
                linha.append("")
            linhas_normalizadas.append(linha[:len(cabecalho)])

        df = pd.DataFrame(linhas_normalizadas, columns=cabecalho, dtype=str).fillna('')

        try:
            df_sc = _ler_aba_como_df(spreadsheet, "Solicitacoes")
            linhas_cotacao = montar_linhas_em_cotacao(df, df_sc)
            if not linhas_cotacao.empty:
                df = pd.concat([df, linhas_cotacao])
        except Exception:
            pass  # "Em Cotação" e um extra - se der erro, so segue com os Pedidos normais

        return df
    except Exception as e:
        st.session_state.erro_tecnico = f"Erro Gspread: {str(e)}"
        return pd.DataFrame()

if 'dados_globais' not in st.session_state or st.session_state.dados_globais.empty:
    st.session_state.dados_globais = carregar_dados_seguros()

df_pc = st.session_state.dados_globais

# Estados de sessão
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "departamento_ativo" not in st.session_state:
    st.session_state.departamento_ativo = ""
if "mostrar_popup_login" not in st.session_state:
    st.session_state.mostrar_popup_login = False
if "mostrar_popup_importar" not in st.session_state:
    st.session_state.mostrar_popup_importar = False
if "gaveta_aberta" not in st.session_state:
    st.session_state.gaveta_aberta = True

# 5. CABEÇALHO INTEGRADO
with st.container(key="header_card"):
    c1, c2, c3 = st.columns([1.5, 6.0, 1.5])
    with c1:
        if base64_logo:
            st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:130px; display:block;">', unsafe_allow_html=True)
    with c2:
        st.markdown('''
            <div class="brand-text-block">
                <span class="brand-eyebrow">Coordenação de Suprimentos</span>
                <span class="brand-subtitle">Portal Gestão de Compras</span>
            </div>
        ''', unsafe_allow_html=True)
    with c3:
        pass

# 6. JANELA POPUP DISCRETA DE LOGIN
if st.session_state.mostrar_popup_login and not st.session_state.autenticado:
    with st.container():
        st.markdown("""
            <div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border: 2px solid #478c3b; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h3 style="color: #1e293b; margin-top: 0; font-size: 18px;">🔐 Autenticação de Operador</h3>
            </div>
        """, unsafe_allow_html=True)
        
        pop_c1, pop_c2, pop_c3, pop_c4 = st.columns([2.5, 2.5, 2.0, 1.5])
        with pop_c1:
            dep_escolhido = st.selectbox("Departamento:", ["compras", "almoxarifado", "logistica", "gestor"], key="pop_dep")
        with pop_c2:
            senha_tentativa = st.text_input("Senha:", type="password", placeholder="Digite a senha...", key="pop_senha")
        with pop_c3:
            st.write("")
            st.write("")
            btn_confirmar = st.button("Confirmar Acesso", use_container_width=True, type="primary")
            if btn_confirmar:
                senhas = {
                    "compras": "compras@2026",
                    "almoxarifado": "almox@2026",
                    "logistica": "log@2026",
                    "gestor": "gestor@2026"
                }
                if senha_tentativa == senhas.get(dep_escolhido):
                    st.session_state.autenticado = True
                    st.session_state.departamento_ativo = dep_escolhido
                    st.session_state.mostrar_popup_login = False
                    st.success("Autenticado com sucesso!")
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
        with pop_c4:
            st.write("")
            st.write("")
            if st.button("✖ Fechar", use_container_width=True):
                st.session_state.mostrar_popup_login = False
                st.rerun()
        st.divider()

# 8. DICIONÁRIO MAPEADO RIGOROSAMENTE COM AS SUAS COLUNAS EXATAS
DICIONARIO_COLUNAS_EXATAS = [
    {"planilha": ["STATUS"], "tela": "Status", "tipo": "texto"},
    {"planilha": ["CENTRO DE CUSTO"], "tela": "Centro De Custo", "tipo": "texto"},
    {"planilha": ["SOLICITAÇÃO", "SOLICITACAO"], "tela": "Solicitação", "tipo": "texto"},
    {"planilha": ["PEDIDO"], "tela": "Pedido", "tipo": "pedido"},   
    {"planilha": ["CONDIÇÃO PAGAMENTO"], "tela": "Condição Pagamento", "tipo": "texto"},
    {"planilha": ["DATA PEDIDO"], "tela": "Emissão Pc", "tipo": "data"},
    {"planilha": ["DATA LIBERAÇÃO", "DATA LIBERACAO"], "tela": "Aprovação Pc", "tipo": "data"},
    {"planilha": ["ENVIO"], "tela": "Envio Pc", "tipo": "data"},
    {"planilha": ["PAGAMENTO"], "tela": "Pagamento Pc", "tipo": "texto"}, 
    {"planilha": ["PREVISÃO DE ENTREGA"], "tela": "Previsão De Entrega", "tipo": "data"},
    {"planilha": ["ENTREGA"], "tela": "Entrega", "tipo": "data"},
    {"planilha": ["FORNECEDOR"], "tela": "Fornecedor", "tipo": "texto"},
    {"planilha": ["GRUPO"], "tela": "Grupo", "tipo": "texto"},
    {"planilha": ["PRODUTO"], "tela": "Produto", "tipo": "produto"},                 
    {"planilha": ["DESCRICAO"], "tela": "Descrição", "tipo": "texto"},
    {"planilha": ["UM"], "tela": "Um", "tipo": "texto"},
    {"planilha": ["QTD"], "tela": "Qtd", "tipo": "numero"},
    {"planilha": ["PREÇO UNITÁRIO", "PRECO UNITARIO"], "tela": "Preço Unitário", "tipo": "moeda"},
    {"planilha": ["VALOR TOTAL"], "tela": "Valor Total", "tipo": "moeda"},
    {"planilha": ["NF REMESSA"], "tela": "NF Remessa", "tipo": "texto"},
    {"planilha": ["LOGISTICA"], "tela": "Logística", "tipo": "logistica"}
]

def converter_para_numerico(valor):
    if not valor or str(valor).lower() == 'nan' or str(valor).strip() == '':
        return 0.0
    dado = str(valor).strip().replace('R$', '').replace('$', '').replace(' ', '')
    try:
        if ',' in dado and '.' in dado:
            dado = dado.replace('.', '').replace(',', '.')
        elif ',' in dado:
            dado = dado.replace(',', '.')
        val_float = float(dado)
        return round(val_float, 2)
    except:
        return 0.0

def formatar_moeda_br(valor):
    num = converter_para_numerico(valor)
    return f"R$ {num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def validar_formato_data(txt):
    txt = str(txt).strip()
    if txt == "" or txt.upper() in ["N/A", "NONE", "NAN", "0"]:
        return True # Campos vazios ou N/A permitidos
    # Valida rigorosamente o formato DD/MM/AAAA
    padrao_data = r"^\d{2}/\d{2}/\d{4}$"
    if not re.match(padrao_data, txt):
        return False
    try:
        datetime.strptime(txt, '%d/%m/%Y')
        return True
    except ValueError:
        return False

def formatar_para_dd_mm_aaaa(valor):
    txt = str(valor).strip()
    if txt == "" or txt.lower() in ["nan", "none", "0", "n/a"]:
        return txt
    try:
        if re.match(r'^\d{5}$', txt):
            dt = datetime(1899, 12, 30) + timedelta(days=int(txt))
            return dt.strftime('%d/%m/%Y')
        
        dt = pd.to_datetime(txt, errors='coerce', format='mixed', dayfirst=True)
        if pd.isna(dt):
            return txt
        return dt.strftime('%d/%m/%Y')
    except:
        return txt



def aplicar_filtros(df_pc):
    """Aplica os filtros ativos (lidos do session_state) e devolve (df_final, colunas_normalizadas)."""
    df_final = df_pc.copy()
    colunas_normalizadas = {c.upper().strip().replace('Í', 'I').replace('Ã', 'A'): c for c in df_final.columns}

    if st.session_state.filtro_pc_val:
        pc_termo = str(st.session_state.filtro_pc_val).strip()
        col_pc = colunas_normalizadas.get("PEDIDO")
        if col_pc:
            df_final = df_final[df_final[col_pc].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.contains(pc_termo, na=False)]

    if st.session_state.filtro_sc_val:
        sc_termo = str(st.session_state.filtro_sc_val).strip()
        col_sc = colunas_normalizadas.get("SOLICITAÇÃO") or colunas_normalizadas.get("SOLICITACAO")
        if col_sc:
            df_final = df_final[df_final[col_sc].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.contains(sc_termo, na=False)]

    if st.session_state.filtro_cc_val:
        cc_termo = st.session_state.filtro_cc_val.strip().lower()
        col_cc = colunas_normalizadas.get("CENTRO DE CUSTO")
        if col_cc:
            df_final = df_final[df_final[col_cc].astype(str).str.lower().str.contains(cc_termo, na=False)]

    col_status_verificacao = colunas_normalizadas.get("STATUS")
    if st.session_state.filtro_status_val != "Todos" and col_status_verificacao:
        df_final = df_final[df_final[col_status_verificacao].astype(str).str.strip() == st.session_state.filtro_status_val]

    if st.session_state.filtro_data_val and len(st.session_state.filtro_data_val) == 2:
        if st.session_state.filtro_data_val[0] is not None and st.session_state.filtro_data_val[1] is not None:
            col_emissao_original = colunas_normalizadas.get("DATA PEDIDO")
            if col_emissao_original:
                datas_convertidas = pd.to_datetime(df_final[col_emissao_original], errors='coerce', format='mixed', dayfirst=True).dt.date
                df_final = df_final[(datas_convertidas >= st.session_state.filtro_data_val[0]) & (datas_convertidas <= st.session_state.filtro_data_val[1])]

    return df_final, colunas_normalizadas


def montar_df_painel(df_final, colunas_normalizadas):
    """Recebe o df ja filtrado e monta o df_painel (colunas da tela), aplicando as mesmas regras de N/A."""
    df_painel = pd.DataFrame(index=df_final.index)

    for col_config in DICIONARIO_COLUNAS_EXATAS:
        nome_exibicao_tela = col_config["tela"]
        tipo_campo = col_config["tipo"]

        col_real = None
        for alt in col_config["planilha"]:
            alt_clean = alt.upper().strip().replace('Í', 'I').replace('Ã', 'A')
            for c_up in colunas_normalizadas:
                c_up_clean = c_up.replace('Í', 'I').replace('Ã', 'A')
                if c_up_clean == alt_clean:
                    col_real = colunas_normalizadas[c_up]
                    break
            if col_real:
                break

        if col_real:
            valores_originais = df_final[col_real]
            if tipo_campo == "data":
                df_painel[nome_exibicao_tela] = valores_originais.apply(formatar_para_dd_mm_aaaa)
            elif tipo_campo == "pedido":
                df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            elif tipo_campo == "produto":
                df_painel[nome_exibicao_tela] = valores_originais.apply(lambda val: str(val).split('.')[0].strip().zfill(10) if str(val).strip() and str(val).lower() != 'nan' else "")
            elif tipo_campo == "moeda":
                df_painel[nome_exibicao_tela] = valores_originais.apply(formatar_moeda_br)
            elif tipo_campo == "numero":
                df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            else:
                df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '').str.strip()
        else:
            df_painel[nome_exibicao_tela] = ""

    # Associa a linha física exata da planilha
    df_painel["_row_idx"] = [idx + 2 for idx in df_final.index]

    col_status_tela = colunas_normalizadas.get("STATUS")
    if col_status_tela:
        termos_excecao = ["SERVIÇO", "CANCELADO PELO SOLICITANTE", "REJEITADO PELO APROVADOR", "COMPRA DIRETA"]
        mask_status = df_painel["Status"].astype(str).str.upper().apply(
            lambda s: any(t in s for t in termos_excecao)
        )
        for col_nome in ["Previsão De Entrega", "Entrega"]:
            if col_nome in df_painel.columns:
                df_painel.loc[mask_status, col_nome] = "N/A"

    if "Previsão De Entrega" in df_painel.columns and "Entrega" in df_painel.columns:
        mascara_vazia = (df_painel["Previsão De Entrega"] == "") | (df_painel["Previsão De Entrega"].isna())
        df_painel.loc[mascara_vazia, "Previsão De Entrega"] = df_painel.loc[mascara_vazia, "Entrega"]

    if "Pagamento Pc" in df_painel.columns and "Condição Pagamento" in df_painel.columns:
        condicao_normalizada = df_painel["Condição Pagamento"].astype(str).str.upper().str.strip()
        mascara_na = (
            (~condicao_normalizada.str.contains("A VISTA", na=False)) &
            (~condicao_normalizada.str.contains("ENT", na=False)) &
            (~condicao_normalizada.str.contains("VENCIDO", na=False)) &
            (~condicao_normalizada.str.contains("PAGO", na=False))
        )
        df_painel.loc[mascara_na, "Pagamento Pc"] = "N/A"

    colunas_para_formatar = ["Envio Pc", "Pagamento Pc", "Previsão De Entrega", "Entrega", "Emissão Pc", "Aprovação Pc"]
    for col_data in colunas_para_formatar:
        if col_data in df_painel.columns:
            df_painel[col_data] = df_painel[col_data].apply(
                lambda x: x if str(x).upper() == "N/A" else formatar_para_dd_mm_aaaa(x)
            )

    # Todo texto do painel em caixa alta
    for col in df_painel.columns:
        if col == "_row_idx":
            continue
        df_painel[col] = df_painel[col].astype(str).str.upper()

    return df_painel.dropna(how='all')


def parse_data_br(valor):
    """Converte um texto 'DD/MM/AAAA' (formato ja usado no painel) pra date. None se vazio/invalido/N/A."""
    txt = str(valor).strip()
    if not txt or txt.upper() in ("N/A", "NAN", "NONE"):
        return None
    try:
        return datetime.strptime(txt, "%d/%m/%Y").date()
    except ValueError:
        return None


def calcular_colunas_sla(df_painel):
    """Calcula as colunas Sla Pagamento e Sla Entrega (dias corridos),
    portadas diretamente das formulas reais da planilha de follow up:

    Sla Pagamento (Excel):
      =SEERRO(SE(OU([@STATUS]="rejeitado pelo aprovador";[@STATUS]="Cancelado";D="------");
        ""; SE(C="";""; SE(D="";SE(H="";HOJE()-C;H-C);D-C))); "")
      (C=Envio Pc, D=Pagamento Pc, H=Entrega)

    Sla Entrega: atrelado a Envio Pc - conta todo dia (HOJE-Envio) e congela
    em (Entrega-Envio) assim que a Entrega for inserida, seja manualmente
    pelo almoxarifado ou via importação. Não depende do texto exato do
    Status nem da Previsão De Entrega (o formulário original da planilha de
    follow up usava status="recebido"/Previsão De Entrega, mas isso não
    bate com os dados reais do painel - aqui o Status nunca é literalmente
    "recebido" e a Previsão De Entrega quase sempre já vem preenchida via
    o preenchimento automático a partir da Entrega, então a única regra que
    realmente funciona é: Entrega preenchida -> congela; senão -> conta).
    """
    hoje = datetime.now().date()

    sla_pagamento = []
    sla_entrega = []
    for _, linha in df_painel.iterrows():
        status_upper = str(linha.get("Status", "")).strip().upper()
        pagamento_raw = str(linha.get("Pagamento Pc", "")).strip()

        data_envio = parse_data_br(linha.get("Envio Pc", ""))
        data_pagamento = parse_data_br(pagamento_raw)
        data_entrega = parse_data_br(linha.get("Entrega", ""))

        # --- Sla Pagamento ---
        if status_upper in ("REJEITADO PELO APROVADOR", "CANCELADO") or pagamento_raw.upper() in ("------", "N/A"):
            sla_pagamento.append("")
        elif not data_envio:
            sla_pagamento.append("")
        elif not data_pagamento:
            if not data_entrega:
                sla_pagamento.append((hoje - data_envio).days)
            else:
                sla_pagamento.append((data_entrega - data_envio).days)
        else:
            sla_pagamento.append((data_pagamento - data_envio).days)

        # --- Sla Entrega ---
        if not data_envio:
            sla_entrega.append("")
        elif status_upper == "REJEITADO PELO APROVADOR":
            sla_entrega.append("")
        elif data_entrega:
            sla_entrega.append((data_entrega - data_envio).days)
        else:
            sla_entrega.append((hoje - data_envio).days)

    df_painel["Sla Pagamento"] = sla_pagamento
    df_painel["Sla Entrega"] = sla_entrega

    # Reordena pra bater com a planilha de follow up: ... Pagamento Pc, Sla
    # Pagamento, Previsão De Entrega, Sla Entrega, Entrega, ...
    cols = [c for c in df_painel.columns if c not in ("Sla Pagamento", "Sla Entrega")]
    pos_pagamento = cols.index("Pagamento Pc") + 1 if "Pagamento Pc" in cols else len(cols)
    cols.insert(pos_pagamento, "Sla Pagamento")
    pos_previsao = cols.index("Previsão De Entrega") + 1 if "Previsão De Entrega" in cols else len(cols)
    cols.insert(pos_previsao, "Sla Entrega")
    return df_painel[cols]


def gerar_bytes_excel(df_painel):
    """Gera o .xlsx (bytes) do relatorio a partir do df_painel ja montado."""
    out = BytesIO()
    df_excel_export = df_painel.drop(columns=["_row_idx"], errors="ignore")
    df_excel_export = df_excel_export.rename(columns=lambda c: c.replace(" Pc", " PC"))
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_excel_export.to_excel(wr, index=False, sheet_name="Relatório")
        worksheet = wr.sheets["Relatório"]
        for idx, col_name in enumerate(df_excel_export.columns):
            serie_coluna = df_excel_export[col_name].astype(str)
            max_len = max(serie_coluna.map(len).max(), len(col_name)) + 3
            worksheet.set_column(idx, idx, max(max_len, 12))
    return out.getvalue()


# 6.5 IMPORTADOR PROTHEUS (upload direto no painel, mesma logica do agente local)
# Fica hospedado aqui pra rodar 24h no Streamlit Cloud, sem depender do PC do
# operador ligado. Mesmas regras do agente_importador.py: dedup por chave,
# so preenche campo em branco (nunca sobrescreve o que ja tem valor), status
# so muda quando esta "em espera" (branco/Em aprovação/Pendente).
ABA_PEDIDOS_IMPORT = "Pedidos"
ABA_SOLICITACOES_IMPORT = "Solicitacoes"
COLUNAS_ASSINATURA_PC = "Dt. Dig.Nota"
COLUNAS_ASSINATURA_SC = "Cod SC. SCM"

MAPA_PEDIDOS_IMPORT = {
    "SOLICITAÇÃO":        {"origem": "Numero da SC",   "tipo": "inteiro"},
    "PEDIDO":             {"origem": "Numero",          "tipo": "inteiro"},
    "CONDIÇÃO PAGAMENTO": {"origem": "Descricao",       "tipo": "texto"},
    "PAGAMENTO":          {"origem": "Descricao",       "tipo": "pagamento_calc"},
    "DATA PEDIDO":        {"origem": "Data Emissao",    "tipo": "data"},
    "DATA LIBERAÇÃO":     {"origem": "Dt Lib. PC",      "tipo": "data"},
    "PREVISÃO DE ENTREGA":{"origem": "Dt. Entrega",     "tipo": "data"},
    "ENTREGA":            {"origem": "DT Baixa",        "tipo": "data"},
    "NF REMESSA":         {"origem": "Num da Nota",     "tipo": "texto"},
    "FORNECEDOR":         {"origem": "Nome Fornece",    "tipo": "texto"},
    "GRUPO":              {"origem": "Grupo",           "tipo": "texto"},
    "CENTRO DE CUSTO":    {"origem": "Centro Custo",    "tipo": "texto"},
    "PRODUTO":            {"origem": "Produto",         "tipo": "produto"},
    "DESCRICAO":          {"origem": "Descricao.1",     "tipo": "texto"},
    "UM":                 {"origem": "Unidade",         "tipo": "texto"},
    "QTD":                {"origem": "Quantidade",      "tipo": "numero"},
    "PREÇO UNITÁRIO":     {"origem": "Prc Unitario",    "tipo": "decimal"},
    "VALOR TOTAL":        {"origem": "Vlr.Total",       "tipo": "decimal"},
}
ALIASES_PEDIDOS_IMPORT = {
    "SOLICITAÇÃO": ["SOLICITAÇÃO", "SOLICITACAO"],
    "DATA LIBERAÇÃO": ["DATA LIBERAÇÃO", "DATA LIBERACAO"],
    "PREÇO UNITÁRIO": ["PREÇO UNITÁRIO", "PRECO UNITARIO"],
}
CAMPOS_MANUAIS_PEDIDOS_IMPORT = ["STATUS", "ENVIO", "LOGISTICA"]
CHAVE_PEDIDOS_IMPORT = ("PEDIDO", "PRODUTO")

CABECALHO_SOLICITACOES_IMPORT = [
    "SOLICITAÇÃO", "ITEM SC", "COTAÇÃO", "PEDIDO", "PRODUTO", "DESCRICAO",
    "QTD", "UM", "CENTRO DE CUSTO", "DESC CENTRO DE CUSTO",
    "DATA EMISSAO", "DATA APROVACAO", "FILIAL", "QTD EM PEDIDO",
]
MAPA_SOLICITACOES_IMPORT = {
    "SOLICITAÇÃO":          {"origem": "Numero da SC", "tipo": "inteiro"},
    "ITEM SC":              {"origem": "Item da SC",   "tipo": "texto"},
    "COTAÇÃO":              {"origem": "Num. Cotacao", "tipo": "texto"},
    "PEDIDO":               {"origem": "Num. Pedido",  "tipo": "inteiro"},
    "PRODUTO":              {"origem": "Produto",      "tipo": "produto"},
    "DESCRICAO":            {"origem": "Descricao",    "tipo": "texto"},
    "QTD":                  {"origem": "Quantidade",   "tipo": "numero"},
    "UM":                   {"origem": "Unid Medida",  "tipo": "texto"},
    "CENTRO DE CUSTO":      {"origem": "C Custo",      "tipo": "texto"},
    "DESC CENTRO DE CUSTO": {"origem": "Desc C.C.",    "tipo": "texto"},
    "DATA EMISSAO":         {"origem": "DT Emissao",   "tipo": "data"},
    "DATA APROVACAO":       {"origem": "Dt Aprovacao", "tipo": "data"},
    "FILIAL":               {"origem": "Filial",       "tipo": "texto"},
    "QTD EM PEDIDO":        {"origem": "Quant.em Ped", "tipo": "numero"},
}
CHAVE_SOLICITACOES_IMPORT = ("SOLICITAÇÃO", "ITEM SC")


def normalizar_nome_import(nome) -> str:
    return str(nome).upper().strip().replace("Í", "I").replace("Ã", "A")


def normalizar_status_import(texto) -> str:
    texto = str(texto or "").strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def limpar_numero_texto_import(valor) -> str:
    txt = str(valor).strip()
    if txt.lower() in ("nan", "none", "nat", ""):
        return ""
    return re.sub(r"\.0$", "", txt)


def valor_e_zero_ou_vazio_import(valor) -> bool:
    txt = str(valor or "").strip()
    return txt == "" or txt.lstrip("0") == ""


def fmt_inteiro_import(valor) -> str:
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    try:
        return str(int(float(valor)))
    except (ValueError, TypeError):
        return limpar_numero_texto_import(valor)


def fmt_texto_import(valor) -> str:
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def fmt_produto_import(valor) -> str:
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    return limpar_numero_texto_import(valor).strip().zfill(10)


def fmt_numero_import(valor) -> str:
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    try:
        num = float(valor)
        return str(int(num)) if num.is_integer() else str(num)
    except (ValueError, TypeError):
        return limpar_numero_texto_import(valor)


def fmt_decimal_import(valor) -> str:
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    try:
        return f"{float(valor):.2f}"
    except (ValueError, TypeError):
        return limpar_numero_texto_import(valor)


def fmt_data_import(valor) -> str:
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    dt = pd.to_datetime(valor, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return ""
    return dt.strftime("%d/%m/%Y")


CONDICOES_PAGAMENTO_SEM_MARCADOR_IMPORT = {
    "A VISTA", "ENT +1PARC", "ENT+3PARC", "ENTR + 1 PARC", "PAGO", "VENCIDO",
}


def fmt_pagamento_calc_import(valor) -> str:
    condicao = fmt_texto_import(valor).upper()
    if condicao == "":
        return ""
    if condicao in CONDICOES_PAGAMENTO_SEM_MARCADOR_IMPORT:
        return ""
    return "------"


FORMATADORES_IMPORT = {
    "inteiro": fmt_inteiro_import,
    "texto": fmt_texto_import,
    "produto": fmt_produto_import,
    "numero": fmt_numero_import,
    "decimal": fmt_decimal_import,
    "data": fmt_data_import,
    "pagamento_calc": fmt_pagamento_calc_import,
}

TEXTO_PENDENTE_APROVACAO_IMPORT = "Pendente de Aprovação"

STATUS_GATILHO_SUBSTITUICAO_IMPORT = {
    normalizar_status_import(""),
    normalizar_status_import("Em aprovação"),
    normalizar_status_import("Pendente"),
    normalizar_status_import(TEXTO_PENDENTE_APROVACAO_IMPORT),
}

MAPA_STATUS_APROV_TEXTO_IMPORT = {
    normalizar_status_import("Pendente"): TEXTO_PENDENTE_APROVACAO_IMPORT,
    normalizar_status_import("Não possui controle de Aprovação"): "Aprovado",
}


def valor_status_origem_import(linha_origem) -> str:
    bruto = fmt_texto_import(linha_origem.get("Status Aprov", ""))
    valor = MAPA_STATUS_APROV_TEXTO_IMPORT.get(normalizar_status_import(bruto), bruto)
    return valor.upper()


def construir_lookup_campo_import(campos: list, aliases: dict) -> dict:
    lookup = {}
    for campo in campos:
        for alt in [campo] + aliases.get(campo, []):
            lookup[normalizar_nome_import(alt)] = campo
    return lookup


def resolver_coluna_real_import(cabecalho_real: list, campo: str, aliases: dict):
    normalizado = {normalizar_nome_import(c): c for c in cabecalho_real}
    for alt in [campo] + aliases.get(campo, []):
        achado = normalizado.get(normalizar_nome_import(alt))
        if achado:
            return achado
    return None


def carregar_indice_existentes_import(worksheet, campos_chave, aliases):
    valores = worksheet.get_all_values()
    if not valores:
        return {}, []
    cabecalho_real = valores[0]
    indices = {}
    for campo in campos_chave:
        col_real = resolver_coluna_real_import(cabecalho_real, campo, aliases)
        if not col_real:
            return {}, cabecalho_real
        indices[campo] = cabecalho_real.index(col_real)

    n_cols = len(cabecalho_real)
    indice = {}
    for i, linha in enumerate(valores[1:], start=2):
        linha_pad = linha + [""] * (n_cols - len(linha))
        partes = []
        for campo in campos_chave:
            valor = linha_pad[indices[campo]]
            partes.append(limpar_numero_texto_import(valor).zfill(10) if campo == "PRODUTO" and valor.strip() else limpar_numero_texto_import(valor))
        chave = tuple(partes)
        if not all(chave):
            continue
        indice[chave] = {"row_num": i, "valores": dict(zip(cabecalho_real, linha_pad))}
    return indice, cabecalho_real


def detectar_tipo_arquivo_import(arquivo):
    arquivo.seek(0)
    try:
        amostra = pd.read_excel(arquivo, header=1, nrows=1)
    except Exception:
        return None
    finally:
        arquivo.seek(0)
    colunas = set(amostra.columns.astype(str))
    if COLUNAS_ASSINATURA_PC in colunas:
        return "PC"
    if COLUNAS_ASSINATURA_SC in colunas:
        return "SC"
    return None


def processar_linhas_import(df_origem, mapa, cabecalho_destino, aliases, campos_manuais,
                             campos_chave, indice_existentes, campo_status=None,
                             calcular_status=None, gatilho_status=None, campos_obrigatorios=()):
    lookup_campo = construir_lookup_campo_import(list(mapa.keys()) + campos_manuais, aliases)
    col_status = resolver_coluna_real_import(cabecalho_destino, campo_status, {}) if campo_status else None

    novas_linhas = []
    atualizacoes = []
    chaves_deste_arquivo = set()
    duplicadas = 0
    linhas_atualizadas = 0

    for _, linha_origem in df_origem.iterrows():
        valores_por_campo = {
            campo_tela: FORMATADORES_IMPORT[config["tipo"]](linha_origem.get(config["origem"], ""))
            for campo_tela, config in mapa.items()
        }

        if any(valor_e_zero_ou_vazio_import(valores_por_campo.get(c, "")) for c in campos_obrigatorios):
            duplicadas += 1
            continue

        chave = tuple(valores_por_campo.get(c, "") for c in campos_chave)
        if not all(chave) or chave in chaves_deste_arquivo:
            duplicadas += 1
            continue

        if chave in indice_existentes:
            chaves_deste_arquivo.add(chave)
            info = indice_existentes[chave]
            valores_atuais = info["valores"]
            alterou = False

            for campo_tela in mapa:
                col_real = resolver_coluna_real_import(cabecalho_destino, campo_tela, aliases)
                if not col_real or valores_atuais.get(col_real, "").strip():
                    continue
                novo_valor = valores_por_campo.get(campo_tela, "")
                if novo_valor:
                    atualizacoes.append((info["row_num"], cabecalho_destino.index(col_real) + 1, novo_valor))
                    alterou = True

            if col_status and calcular_status:
                atual_status = normalizar_status_import(valores_atuais.get(col_status, ""))
                if atual_status in gatilho_status:
                    novo_status = calcular_status(linha_origem)
                    if novo_status and normalizar_status_import(novo_status) != atual_status:
                        atualizacoes.append((info["row_num"], cabecalho_destino.index(col_status) + 1, novo_status))
                        alterou = True

            if alterou:
                linhas_atualizadas += 1
            else:
                duplicadas += 1
            continue

        chaves_deste_arquivo.add(chave)
        linha_final = [valores_por_campo.get(lookup_campo.get(normalizar_nome_import(c)), "") for c in cabecalho_destino]
        if col_status and calcular_status:
            novo_status = calcular_status(linha_origem)
            if novo_status:
                linha_final[cabecalho_destino.index(col_status)] = novo_status
        novas_linhas.append(linha_final)

    return novas_linhas, atualizacoes, duplicadas, linhas_atualizadas


def aplicar_no_google_sheets_import(worksheet, novas_linhas, atualizacoes):
    if novas_linhas:
        worksheet.append_rows(novas_linhas, value_input_option="RAW")
    if atualizacoes:
        celulas = [gspread.Cell(row, col, valor) for row, col, valor in atualizacoes]
        worksheet.update_cells(celulas, value_input_option="RAW")


def obter_ou_criar_aba_import(spreadsheet, nome_aba, cabecalho_padrao=None):
    try:
        return spreadsheet.worksheet(nome_aba)
    except gspread.WorksheetNotFound:
        aba = spreadsheet.add_worksheet(title=nome_aba, rows=1000, cols=max(20, len(cabecalho_padrao or [])))
        if cabecalho_padrao:
            aba.update([cabecalho_padrao], "A1")
        return aba


def processar_arquivo_pc_import(arquivo, spreadsheet):
    worksheet = obter_ou_criar_aba_import(spreadsheet, ABA_PEDIDOS_IMPORT)
    indice_existentes, cabecalho_real = carregar_indice_existentes_import(worksheet, CHAVE_PEDIDOS_IMPORT, ALIASES_PEDIDOS_IMPORT)
    if not cabecalho_real:
        raise RuntimeError(f"Aba '{ABA_PEDIDOS_IMPORT}' está vazia (sem cabeçalho). Configure o cabeçalho antes de importar.")

    arquivo.seek(0)
    df = pd.read_excel(arquivo, header=1)
    novas_linhas, atualizacoes, duplicadas, atualizadas = processar_linhas_import(
        df, MAPA_PEDIDOS_IMPORT, cabecalho_real, ALIASES_PEDIDOS_IMPORT, CAMPOS_MANUAIS_PEDIDOS_IMPORT,
        CHAVE_PEDIDOS_IMPORT, indice_existentes,
        campo_status="STATUS", calcular_status=valor_status_origem_import, gatilho_status=STATUS_GATILHO_SUBSTITUICAO_IMPORT,
        campos_obrigatorios=("SOLICITAÇÃO",),
    )
    aplicar_no_google_sheets_import(worksheet, novas_linhas, atualizacoes)
    return len(novas_linhas), duplicadas, atualizadas


def processar_arquivo_sc_import(arquivo, spreadsheet):
    worksheet = obter_ou_criar_aba_import(spreadsheet, ABA_SOLICITACOES_IMPORT, CABECALHO_SOLICITACOES_IMPORT)
    indice_existentes, cabecalho_real = carregar_indice_existentes_import(worksheet, CHAVE_SOLICITACOES_IMPORT, {})
    if not cabecalho_real:
        cabecalho_real = CABECALHO_SOLICITACOES_IMPORT

    arquivo.seek(0)
    df = pd.read_excel(arquivo, header=1)
    novas_linhas, atualizacoes, duplicadas, atualizadas = processar_linhas_import(
        df, MAPA_SOLICITACOES_IMPORT, cabecalho_real, {}, [], CHAVE_SOLICITACOES_IMPORT, indice_existentes,
    )
    aplicar_no_google_sheets_import(worksheet, novas_linhas, atualizacoes)
    return len(novas_linhas), duplicadas, atualizadas


def processar_upload_protheus(arquivo):
    """Recebe um arquivo enviado via st.file_uploader, descobre se e PC ou SC
    e aplica a mesma logica do agente local direto no Google Sheets. Devolve
    (ok: bool, mensagem: str)."""
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(FILE_ID)
    except Exception as e:
        return False, f"❌ Erro ao conectar no Google Sheets: {e}"

    try:
        tipo = detectar_tipo_arquivo_import(arquivo)
        if tipo == "PC":
            novos, dup, atualizadas = processar_arquivo_pc_import(arquivo, spreadsheet)
            return True, f"✅ Pedidos: {novos} linha(s) nova(s), {atualizadas} atualizada(s) (campos em branco/status), {dup} sem nenhuma alteração."
        elif tipo == "SC":
            novos, dup, atualizadas = processar_arquivo_sc_import(arquivo, spreadsheet)
            return True, f"✅ Solicitações: {novos} linha(s) nova(s), {atualizadas} atualizada(s), {dup} sem nenhuma alteração."
        else:
            return False, "❌ Layout do arquivo não reconhecido (não parece Listagem de Pedidos nem de Solicitações do Protheus)."
    except Exception as e:
        return False, f"❌ Erro ao processar o arquivo: {e}"


# 7. FILTROS E LÓGICA DE GAVETA
if "filtro_pc_val" not in st.session_state:
    st.session_state.filtro_pc_val = ""
if "filtro_sc_val" not in st.session_state:
    st.session_state.filtro_sc_val = ""
if "filtro_cc_val" not in st.session_state:
    st.session_state.filtro_cc_val = ""
if "filtro_status_val" not in st.session_state:
    st.session_state.filtro_status_val = "Todos"
if "filtro_data_val" not in st.session_state:
    st.session_state.filtro_data_val = ()

# Pré-cálculo do relatório (pra habilitar o botão Baixar Relatório dentro dos Filtros Avançados,
# com o resultado da busca mais recente - sem isso o botão mostraria dado de uma busca anterior)
tem_busca_ativa = st.session_state.filtro_pc_val or st.session_state.filtro_sc_val or st.session_state.filtro_cc_val or st.session_state.filtro_status_val != "Todos" or bool(st.session_state.filtro_data_val)

relatorio_bytes = None
if tem_busca_ativa and not df_pc.empty:
    try:
        _df_final_preview, _colunas_preview = aplicar_filtros(df_pc)
        if not _df_final_preview.empty:
            _df_painel_preview = montar_df_painel(_df_final_preview, _colunas_preview)
            if not _df_painel_preview.empty:
                if st.session_state.autenticado and st.session_state.departamento_ativo in ("almoxarifado", "gestor"):
                    _df_painel_preview = calcular_colunas_sla(_df_painel_preview)
                relatorio_bytes = gerar_bytes_excel(_df_painel_preview)
    except Exception:
        relatorio_bytes = None

rotulo_seta = "Filtros Avançados ▲" if st.session_state.gaveta_aberta else "Filtros Avançados ▼"

with st.expander(rotulo_seta, expanded=st.session_state.gaveta_aberta):
    with st.form("form_filtros", clear_on_submit=False):
        f1, f2, f3, f4, f5 = st.columns(5)
        
        with f1:
            filtro_pc = st.text_input("Pedido (PC):", value=st.session_state.filtro_pc_val, placeholder="Nº do PC...")
        with f2:
            filtro_sc = st.text_input("Solicitação (SC):", value=st.session_state.filtro_sc_val, placeholder="Nº da SC...")
        with f3:
            filtro_cc = st.text_input("Centro de Custo:", value=st.session_state.filtro_cc_val, placeholder="Centro de custo...")
        with f4:
            col_status_verificacao = next((c for c in df_pc.columns if "STATUS" in c.upper()), None) if not df_pc.empty else None
            if col_status_verificacao:
                lista_status_Filtro = ["Todos"] + sorted([str(x).strip() for x in df_pc[col_status_verificacao].unique() if str(x).strip() != ""])
            else:
                lista_status_Filtro = ["Todos"]
            idx_padrao = lista_status_Filtro.index(st.session_state.filtro_status_val) if st.session_state.filtro_status_val in lista_status_Filtro else 0
            filtro_status = st.selectbox("Status:", options=lista_status_Filtro, index=idx_padrao)
        with f5:
            filtro_data = st.date_input("Data de Emissão:", value=st.session_state.filtro_data_val, format="DD/MM/YYYY")

        st.write("") 
        
        esp0, espb, b1, b2, b3, b4 = st.columns([1.6, 1, 1, 1, 1, 1])
        with esp0:
            st.markdown("&nbsp;", unsafe_allow_html=True)
        with espb:
            st.markdown("&nbsp;", unsafe_allow_html=True)
        with b1:
            btn_pesquisar = st.form_submit_button("🔍 Pesquisar", use_container_width=True, type="primary")
            if btn_pesquisar:
                st.session_state.filtro_pc_val = filtro_pc
                st.session_state.filtro_sc_val = filtro_sc
                st.session_state.filtro_cc_val = filtro_cc
                st.session_state.filtro_status_val = filtro_status
                st.session_state.filtro_data_val = filtro_data
                st.session_state.gaveta_aberta = False  
                st.rerun()

        with b2:
            btn_limpar = st.form_submit_button("❌ Limpar", use_container_width=True)
            if btn_limpar:
                st.session_state.filtro_pc_val = ""
                st.session_state.filtro_sc_val = ""
                st.session_state.filtro_cc_val = ""
                st.session_state.filtro_status_val = "Todos"
                st.session_state.filtro_data_val = ()
                st.session_state.gaveta_aberta = True  
                st.rerun()
                
        with b3:
            btn_atualizar = st.form_submit_button("🔄 Atualizar Banco", use_container_width=True)
            if btn_atualizar:
                st.session_state.dados_globais = carregar_dados_seguros()
                st.session_state.gaveta_aberta = True
                st.rerun()

        with b4:
            if not st.session_state.autenticado:
                if st.form_submit_button("🔐 Operador", use_container_width=True):
                    st.session_state.mostrar_popup_login = not st.session_state.mostrar_popup_login
                    st.rerun()
            else:
                if st.form_submit_button("🚪 Sair", use_container_width=True, key="btn_sair"):
                    st.session_state.autenticado = False
                    st.session_state.departamento_ativo = ""
                    st.session_state.mostrar_popup_login = False
                    st.rerun()

# 8.5 AÇÕES DO PAINEL (Importar Arquivo / Baixar Relatório / Salvar Alterações)
# Unificadas numa linha so, no mesmo nivel (logo apos os Filtros Avançados),
# pra sobrar mais espaço vertical pra tabela de amostra abaixo.
with st.container(key="acoes_painel_wrap"):
    if st.session_state.autenticado and st.session_state.departamento_ativo in ("compras", "gestor"):
        if st.button("📤 Importar Arquivo", key="btn_abrir_importar"):
            st.session_state.mostrar_popup_importar = not st.session_state.mostrar_popup_importar
            st.rerun()

    if relatorio_bytes:
        st.download_button(
            label="📥 Baixar Relatório",
            data=relatorio_bytes,
            file_name="Relatorio_Compras_Filtro.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_baixar_relatorio",
        )

    if st.session_state.autenticado:
        btn_salvar_dados = st.button("💾 Salvar Alterações", type="primary")
    else:
        btn_salvar_dados = False

if st.session_state.autenticado and st.session_state.departamento_ativo in ("compras", "gestor"):
    if st.session_state.mostrar_popup_importar:
        with st.container():
            st.markdown("""
                <div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border: 2px solid #478c3b; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <h3 style="color: #1e293b; margin-top: 0; font-size: 18px;">📤 Importar Arquivo do Protheus (PC/SC)</h3>
                </div>
            """, unsafe_allow_html=True)

            pop_imp_c1, pop_imp_c2 = st.columns([5, 1])
            with pop_imp_c1:
                arquivo_importar = st.file_uploader(
                    "Selecione o arquivo exportado do Protheus (Listagem de Pedidos ou de Solicitações):",
                    type=["xlsx", "xls"],
                    key="uploader_protheus",
                )
            with pop_imp_c2:
                st.write("")
                st.write("")
                if st.button("✖ Fechar", use_container_width=True, key="btn_fechar_importar"):
                    st.session_state.mostrar_popup_importar = False
                    st.rerun()

            if arquivo_importar is not None:
                if st.button("Processar Arquivo", type="primary", key="btn_processar_importacao"):
                    with st.spinner("Processando arquivo e gravando na planilha..."):
                        ok, mensagem = processar_upload_protheus(arquivo_importar)
                    if ok:
                        st.toast(mensagem)
                        st.cache_data.clear()
                        st.session_state.dados_globais = carregar_dados_seguros()
                        st.session_state.mostrar_popup_importar = False
                        st.rerun()
                    else:
                        st.error(mensagem)
            st.divider()

# 9. MOTOR DE BUSCA CASCATA
# tem_busca_ativa e o relatorio ja foram calculados antes dos Filtros Avançados
# (usados aqui embaixo, na contagem de registros).

if tem_busca_ativa:
    if df_pc.empty:
        st.markdown('<div class="custom-error-red custom-empty-state">⚠️ Base de dados vazia. Clique em "🔄 Atualizar Banco" nos Filtros Avançados.</div>', unsafe_allow_html=True)
    else:
        df_final, colunas_normalizadas = aplicar_filtros(df_pc)
        col_status_verificacao = colunas_normalizadas.get("STATUS")

        try:
            if not df_final.empty:
                df_painel = montar_df_painel(df_final, colunas_normalizadas)

                if not df_painel.empty:
                    txt_status = f"🔍 Registros Localizados ({len(df_painel)} itens)"
                    st.markdown(f'<div class="status-card">{txt_status}</div>', unsafe_allow_html=True)
                    # Baixar Relatório / Salvar Alterações renderizados la em cima,
                    # na linha unificada de ações (ver seção 8.5) - btn_salvar_dados
                    # ja foi calculado por la.

                    # SLA (Pagamento/Entrega) - visivel so pro almoxarifado e o gestor
                    mostrar_sla = st.session_state.autenticado and st.session_state.departamento_ativo in ("almoxarifado", "gestor")
                    if mostrar_sla:
                        df_painel = calcular_colunas_sla(df_painel)

                    configuracao_colunas_tela = {}
                    
                    status_existentes = [str(x).strip() for x in df_pc[col_status_verificacao].unique() if str(x).strip() not in ("", "EM COTAÇÃO")] if col_status_verificacao else []
                    status_oficiais = [
                        "ENVIADO AO FORNECEDOR",
                        "ENVIADO AO FINANCEIRO",
                        "PAGO",
                        "FORNECEDOR DECLINOU",
                        "RECEBIDO NA OBRA",
                        "SERVIÇO",
                        "COMPRA DIRETA",
                        "CORREÇÃO DE PROCESSO",
                        "ATENDIDO",
                        "ATENDIDO PARCIALMENTE",
                        "REJEITADO",
                        "APROVADO",
                        "BLOQUEADO",
                        "PENDENTE DE APROVAÇÃO"
                    ]
                    lista_historico_status = sorted(list(set(status_existentes + status_oficiais)))

                    opcoes_logistica = [
                        "RETIRADO DO ALMOXARIFADO SEDE",
                        "ENTREGUE NO PEA",
                        "A CAMINHO DA OBRA",
                        "ENTREGUE NA OBRA"
                    ]

                    # Autosize: calcula a largura (px) de cada coluna a partir do
                    # conteudo REAL da busca atual (nao do heuristico do grid, que
                    # so olha o cabecalho e pode ficar "grudado" numa largura
                    # antiga entre reruns) - roda de novo a cada busca/edicao.
                    larguras_colunas = {}
                    for col_config in DICIONARIO_COLUNAS_EXATAS:
                        nome_tela = col_config["tela"]
                        if nome_tela not in df_painel.columns:
                            continue
                        serie_txt = df_painel[nome_tela].astype(str)
                        maior_valor = serie_txt.map(len).max() if not serie_txt.empty else 0
                        maior_len = max(int(maior_valor or 0), len(nome_tela))
                        larguras_colunas[nome_tela] = max(70, min(int(maior_len * 7.5) + 40, 380))
                    larguras_colunas["Logística"] = max(larguras_colunas.get("Logística", 0), max(len(o) for o in opcoes_logistica) * 7.5 + 40)
                    larguras_colunas["Status"] = max(larguras_colunas.get("Status", 0), max(len(o) for o in lista_historico_status) * 7.5 + 40) if lista_historico_status else larguras_colunas.get("Status", 120)
                    if mostrar_sla:
                        for nome_sla in ("Sla Pagamento", "Sla Entrega"):
                            serie_txt = df_painel[nome_sla].astype(str)
                            maior_len = max(int(serie_txt.map(len).max() or 0), len(nome_sla))
                            larguras_colunas[nome_sla] = max(70, min(int(maior_len * 7.5) + 40, 380))

                    for col_config in DICIONARIO_COLUNAS_EXATAS:
                        nome_tela = col_config["tela"]
                        tipo_campo = col_config["tipo"]
                        largura_px = int(larguras_colunas.get(nome_tela, 120))
                        rotulo_tela = nome_tela.replace(" Pc", " PC")

                        if st.session_state.autenticado:
                            dep = st.session_state.departamento_ativo
                            if dep == "logistica":
                                if nome_tela == "Logística":
                                    configuracao_colunas_tela[nome_tela] = st.column_config.SelectboxColumn(
                                        rotulo_tela, options=opcoes_logistica, required=False, width=largura_px
                                    )
                                else:
                                    configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, disabled=True, width=largura_px)
                            elif dep == "gestor":
                                # Gestor visualiza e edita tudo, sem restrição de campo
                                if nome_tela == "Status":
                                    configuracao_colunas_tela[nome_tela] = st.column_config.SelectboxColumn(
                                        rotulo_tela, options=lista_historico_status, required=True, width=largura_px
                                    )
                                elif nome_tela == "Logística":
                                    configuracao_colunas_tela[nome_tela] = st.column_config.SelectboxColumn(
                                        rotulo_tela, options=opcoes_logistica, required=False, width=largura_px
                                    )
                                else:
                                    configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, disabled=False, width=largura_px)
                            else:
                                campos_permitidos_compras = ["Status", "Envio Pc", "Pagamento Pc", "Previsão De Entrega", "Entrega", "NF Remessa"]
                                if nome_tela in campos_permitidos_compras:
                                    if nome_tela == "Status":
                                        configuracao_colunas_tela[nome_tela] = st.column_config.SelectboxColumn(
                                            rotulo_tela, options=lista_historico_status, required=True, width=largura_px
                                        )
                                    else:
                                        configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, disabled=False, width=largura_px)
                                else:
                                    configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, disabled=True, width=largura_px)
                        else:
                            if nome_tela == "Status":
                                configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, alignment="center", width=largura_px)
                            else:
                                configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, disabled=True, width=largura_px)

                    configuracao_colunas_tela["_row_idx"] = None

                    if mostrar_sla:
                        for nome_sla in ("Sla Pagamento", "Sla Entrega"):
                            configuracao_colunas_tela[nome_sla] = st.column_config.Column(
                                nome_sla, disabled=True, width=int(larguras_colunas.get(nome_sla, 90)),
                                help="Dias corridos - calculado automaticamente"
                            )

                    if st.session_state.autenticado:
                        if "df_original_cache" not in st.session_state or st.session_state.get("atualizar_cache_editor", True):
                            st.session_state.df_original_cache = df_painel.copy()
                            st.session_state.atualizar_cache_editor = False

                        edited_df = st.data_editor(
                            df_painel, 
                            use_container_width=True, 
                            hide_index=True, 
                            column_config=configuracao_colunas_tela,
                            key="editor_painel_compras"
                        )
                        
                        # SALVAMENTO PROCV COM VALIDAÇÃO RÍGIDA DE DATAS (DD/MM/AAAA)
                        if btn_salvar_dados:
                            if "df_original_cache" in st.session_state:
                                df_orig = st.session_state.df_original_cache
                                alteracoes_detectadas = 0
                                data_invalida_encontrada = False
                                
                                # Verifica se alguma data alterada está fora do formato DD/MM/AAAA
                                colunas_de_data_tela = ["Emissão Pc", "Aprovação Pc", "Envio Pc", "Previsão De Entrega", "Entrega"]
                                for idx in edited_df.index:
                                    for col_dt in colunas_de_data_tela:
                                        if col_dt in edited_df.columns:
                                            val_novo_dt = str(edited_df.loc[idx, col_dt])
                                            if not validar_formato_data(val_novo_dt):
                                                data_invalida_encontrada = True
                                                break
                                    if data_invalida_encontrada:
                                        break

                                if data_invalida_encontrada:
                                    st.markdown('<div class="custom-error-red">⚠️ Erro: Há campos de data preenchidos fora do formato obrigatório <b>DD/MM/AAAA</b>. Nenhuma alteração foi salva. Por favor, corrija antes de salvar.</div>', unsafe_allow_html=True)
                                else:
                                    try:
                                        scope = [
                                            "https://www.googleapis.com/auth/spreadsheets",
                                            "https://www.googleapis.com/auth/drive"
                                        ]
                                        creds_dict = dict(st.secrets["gcp_service_account"])
                                        email_servico = creds_dict.get("client_email", "desconhecido")
                                        
                                        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                                        client = gspread.authorize(creds)
                                        
                                        spreadsheet = client.open_by_key(FILE_ID)
                                        try:
                                            worksheet = spreadsheet.worksheet("Pedidos")
                                        except:
                                            worksheet = spreadsheet.get_worksheet(0)
                                        
                                        dados_planilha = worksheet.get_all_values()
                                        cabecalho_bruto = dados_planilha[0]
                                        cabecalho_map = {c.upper().strip().replace('Í', 'I').replace('Ã', 'A'): i + 1 for i, c in enumerate(cabecalho_bruto)}
                                        
                                        for idx in edited_df.index:
                                            linha_planilha = int(edited_df.loc[idx, "_row_idx"])
                                            if linha_planilha >= SENTINELA_ROW_IDX_EM_COTACAO:
                                                # Linha sintetica "Em Cotação" (Solicitação sem
                                                # Pedido ainda) - nao existe na aba Pedidos, nunca salva.
                                                continue
                                            for col in edited_df.columns:
                                                if col == "_row_idx":
                                                    continue
                                                
                                                valor_antigo = str(df_orig.loc[idx, col])
                                                valor_novo = str(edited_df.loc[idx, col])
                                                
                                                if valor_antigo != valor_novo:
                                                    col_config_item = next((item for item in DICIONARIO_COLUNAS_EXATAS if item["tela"] == col), None)
                                                    if col_config_item:
                                                        col_index = None
                                                        for alt in col_config_item["planilha"]:
                                                            alt_clean = alt.upper().strip().replace('Í', 'I').replace('Ã', 'A')
                                                            col_index = cabecalho_map.get(alt_clean)
                                                            if col_index:
                                                                break
                                                        
                                                        if col_index:
                                                            worksheet.update_cell(linha_planilha, col_index, valor_novo)
                                                            alteracoes_detectadas += 1
                                                            
                                        if alteracoes_detectadas > 0:
                                            st.success(f"✅ {alteracoes_detectadas} alteração(ões) gravada(s) com sucesso na planilha!")
                                            st.session_state.df_original_cache = edited_df.copy()
                                            st.cache_data.clear()
                                            st.rerun()
                                        else:
                                            st.info("ℹ️ Nenhuma alteração foi realizada para salvar.")
                                            
                                    except Exception as e:
                                        erro_str = str(e)
                                        if "403" in erro_str or "permission" in erro_str.lower():
                                            st.error(f"❌ Erro 403 (Permissão Negada). Verifique se o e-mail da conta de serviço **{email_servico}** está adicionado como **Editor** na planilha.")
                                        else:
                                            st.error(f"❌ Erro ao gravar: {e}")
                    else:
                        st.dataframe(
                            df_painel.drop(columns=["_row_idx"], errors="ignore"), 
                            use_container_width=True, 
                            hide_index=True, 
                            column_config=configuracao_colunas_tela
                        )
                else:
                    st.markdown('<div class="custom-error-red custom-empty-state">⚠️ Nenhum registro correspondente encontrado com os filtros informados.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="custom-error-red custom-empty-state">⚠️ Nenhum registro correspondente encontrado.</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="custom-error-red">⚠️ Erro ao processar os dados da busca: {e}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="custom-welcome-salutation">👋 Olá! Seja bem-vindo ao Portal de Gestão de Compras. Utilize os Filtros Avançados acima para pesquisar.</div>', unsafe_allow_html=True)

# 10. RODAPÉ INSTITUCIONAL
st.markdown("<div class=\"custom-footer-block\"><p style='color:#64748b; font-size:13px; font-weight:600; margin:0;'>Parente Andrade | Coordenação de Suprimentos</p></div>", unsafe_allow_html=True)

# 11. MARCA D'ÁGUA FIXA EXCLUSIVA DA AUTORIA
st.markdown('<div class="signature-fixed">Created by SS.</div>', unsafe_allow_html=True)
