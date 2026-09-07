"""Código compartilhado entre as páginas do Portal Gestão de Compras
(main.py = painel de Pedidos, pages/1_Painel_Comprador.py = painel de
Solicitações) - estilos, cabeçalho, login por departamento, acesso ao
Google Sheets e formatadores de valor usados nos dois painéis."""

import base64
import re
from datetime import datetime, timedelta
from io import BytesIO

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

FILE_ID = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"

SENHAS_DEPARTAMENTO = {
    "compras": "compras@2026",
    "almoxarifado": "almox@2026",
    "logistica": "log@2026",
    "gestor": "gestor@2026",
}


@st.cache_data(ttl=86400)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None


CSS_GLOBAL = """
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
    """


def aplicar_estilos():
    st.markdown(CSS_GLOBAL, unsafe_allow_html=True)


def renderizar_cabecalho(subtitulo="Portal Gestão de Compras"):
    base64_logo = get_base64_logo()
    with st.container(key="header_card"):
        c1, c2, c3 = st.columns([1.5, 6.0, 1.5])
        with c1:
            if base64_logo:
                st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:130px; display:block;">', unsafe_allow_html=True)
        with c2:
            st.markdown(f'''
                <div class="brand-text-block">
                    <span class="brand-eyebrow">Coordenação de Suprimentos</span>
                    <span class="brand-subtitle">{subtitulo}</span>
                </div>
            ''', unsafe_allow_html=True)
        with c3:
            pass


def renderizar_rodape():
    st.markdown("<div class=\"custom-footer-block\"><p style='color:#64748b; font-size:13px; font-weight:600; margin:0;'>Parente Andrade | Coordenação de Suprimentos</p></div>", unsafe_allow_html=True)
    st.markdown('<div class="signature-fixed">Created by SS.</div>', unsafe_allow_html=True)


def inicializar_sessao_login():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "departamento_ativo" not in st.session_state:
        st.session_state.departamento_ativo = ""
    if "mostrar_popup_login" not in st.session_state:
        st.session_state.mostrar_popup_login = False


def renderizar_popup_login():
    """Janela popup discreta de login por departamento - compartilhada entre
    os painéis (o estado de sessão é o mesmo em todas as páginas)."""
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
                    if senha_tentativa == SENHAS_DEPARTAMENTO.get(dep_escolhido):
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


def obter_client_gspread():
    """Autentica no Google Sheets com a service account e devolve
    (client, creds_dict) - creds_dict serve pra recuperar o client_email
    nas mensagens de erro 403."""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client, creds_dict


def _ler_aba_como_df(spreadsheet, nome_aba):
    """Le uma aba inteira e devolve um DataFrame de strings (linhas curtas
    preenchidas com "")."""
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
    except Exception:
        return 0.0


def formatar_moeda_br(valor):
    num = converter_para_numerico(valor)
    return f"R$ {num:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def validar_formato_data(txt):
    txt = str(txt).strip()
    if txt == "" or txt.upper() in ["N/A", "NONE", "NAN", "0"]:
        return True  # Campos vazios ou N/A permitidos
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
    except Exception:
        return txt


def parse_data_br(valor):
    """Converte um texto 'DD/MM/AAAA' pra date. None se vazio/invalido/N/A."""
    txt = str(valor).strip()
    if not txt or txt.upper() in ("N/A", "NAN", "NONE"):
        return None
    try:
        return datetime.strptime(txt, "%d/%m/%Y").date()
    except ValueError:
        return None


def gerar_bytes_excel(df_painel):
    """Gera o .xlsx (bytes) do relatorio a partir de um df_painel ja montado
    (qualquer painel - Pedidos ou Solicitações)."""
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
