"""Visual "PA" (Parente Andrade) do Portal Gestão de Compras.

Camada só de aparência, aplicada DEPOIS de comum.aplicar_estilos(): redefine
as variáveis CSS --pa-* (mesmos nomes que o comum.py já usa, então todo o CSS
existente passa a usar a paleta nova) e acrescenta os ajustes visuais - faixa
de topo verde escura com filete laranja, cartões arredondados, botões
primários verdes, secundários com borda laranja, campos com foco verde.

Tema: preserva o mecanismo que o app já tem - botão claro/escuro no desktop
(st.session_state.tema) e, no celular (<=640px), o tema claro/escuro do
SISTEMA via prefers-color-scheme. Nenhuma base é forçada.
"""

import os

import streamlit as st

# Mesmo padrão do comum.py: o main.py recarrega o módulo se o arquivo mudou.
_MTIME_AO_IMPORTAR = os.path.getmtime(__file__)

PALETAS = {
    "claro": {
        "verde": "#619935", "verde-deep": "#4C7D27", "verde-soft": "#E3EFD4",
        "laranja": "#E8A838", "laranja-deep": "#A8700A", "laranja-soft": "#FBEBC8",
        "ink": "#1E2B19", "paper": "#F1F7EA", "card": "#FFFFFF",
        "input-bg": "#FFFFFF", "mist": "#D5E4C6", "slate": "#5B6A52", "slate-soft": "#68785E",
        "error-bg": "#FCEAEA", "error-text": "#B3282D", "error-border": "#D8383D",
        "sombra": "rgba(34, 56, 24, 0.10)",
    },
    "escuro": {
        "verde": "#7DB84A", "verde-deep": "#619935", "verde-soft": "#243320",
        "laranja": "#F0B445", "laranja-deep": "#D99A2B", "laranja-soft": "#3A2E14",
        "ink": "#EDF3E6", "paper": "#10150D", "card": "#1A2116",
        "input-bg": "#222B1D", "mist": "#2C3827", "slate": "#9DB091", "slate-soft": "#8A9C7E",
        "error-bg": "#3A1F1F", "error-text": "#F5A3A3", "error-border": "#C0392B",
        "sombra": "rgba(0, 0, 0, 0.45)",
    },
}

_HERO_GRADIENTE = "linear-gradient(120deg, #162610 0%, #2A4A1A 55%, #3F6E26 100%)"
_HERO_SUB = "#CFE3BE"


def _vars(paleta):
    return "\n".join(f"--pa-{chave}: {valor};" for chave, valor in paleta.items())


def _css_vars_tema():
    tema = st.session_state.get("tema", "claro")
    if tema not in PALETAS:
        tema = "claro"
    # Mesma lógica do comum._css_variaveis_tema: desktop = tema do botão;
    # celular (<=640px) = tema do sistema (o Python não enxerga isso, então as
    # duas paletas saem e o navegador escolhe via prefers-color-scheme).
    return f"""
    :root {{ {_vars(PALETAS[tema])} --pa-hero: {_HERO_GRADIENTE}; --pa-hero-sub: {_HERO_SUB}; }}
    @media (max-width: 640px) {{
        :root {{ {_vars(PALETAS["claro"])} }}
    }}
    @media (max-width: 640px) and (prefers-color-scheme: dark) {{
        :root {{ {_vars(PALETAS["escuro"])} }}
    }}
    """


_IMPORT_FONTE = "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');"

CSS_PA = """
    html, body, .stApp, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif !important; }
    button, input, textarea, [class*="st-"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
    .portal-title, .brand-subtitle, .brand-eyebrow,
    div[data-testid="stExpander"] summary p, .streamlit-expanderHeader p,
    div[data-testid="stDataFrame"] table th, div[data-testid="stDataFrame"] table td { font-family: 'Inter', 'Segoe UI', sans-serif !important; }
    hr { border-color: var(--pa-mist) !important; }

    /* faixa de topo: gradiente verde escuro + filete laranja, igual nos dois temas.
       Sobre ela o logo é sempre o de texto claro (logo_escuro) e os textos são claros. */
    div.st-key-header_card {
        background: var(--pa-hero) !important; border-radius: 18px !important;
        border-bottom: 4px solid var(--pa-laranja); box-shadow: 0 8px 24px var(--pa-sombra) !important;
    }
    div.st-key-header_card::before { display: none !important; }
    div.st-key-header_card img.pa-logo-claro { display: none !important; }
    div.st-key-header_card img.pa-logo-escuro { display: block !important; }
    div.st-key-header_card .brand-eyebrow { color: var(--pa-hero-sub) !important; font-weight: 600; }
    div.st-key-header_card .brand-subtitle { color: #FFFFFF !important; font-weight: 800; letter-spacing: -0.3px; }
    div.st-key-header_card .portal-title { color: #FFFFFF !important; }
    div.st-key-header_card label, div.st-key-header_card div[data-testid="stWidgetLabel"] p,
    div.st-key-header_card div[data-testid="stMarkdownContainer"] p { color: #FFFFFF !important; }
    div.st-key-header_card div[data-testid="stTooltipIcon"], div.st-key-header_card div[data-testid="stTooltipIcon"] svg { color: var(--pa-hero-sub) !important; }

    /* títulos de seção: barra laranja à esquerda */
    div[data-testid="stHeading"] h3 {
        font-size: 20px; font-weight: 700; letter-spacing: -0.2px;
        border-left: 5px solid var(--pa-laranja); padding-left: 12px;
    }
    div[data-testid="stDialog"] h1, div[data-testid="stDialog"] h2, div[data-testid="stDialog"] h3 { color: var(--pa-ink) !important; }

    /* cartões */
    div[data-testid="stExpander"] { border: 1px solid var(--pa-mist) !important; border-radius: 16px !important; box-shadow: 0 6px 20px var(--pa-sombra) !important; }
    div[data-testid="stExpander"] summary:hover p { color: var(--pa-verde) !important; }
    div[data-testid="stDataFrame"] { background: var(--pa-card) !important; border: 1px solid var(--pa-mist); border-radius: 14px !important; box-shadow: 0 6px 20px var(--pa-sombra) !important; }
    div[data-testid="stDataFrame"] table th { background: var(--pa-paper) !important; color: var(--pa-slate) !important; }
    .status-card { border-radius: 14px !important; border: 1px solid var(--pa-mist); border-left: 5px solid var(--pa-laranja) !important; box-shadow: 0 6px 20px var(--pa-sombra) !important; }
    .custom-welcome-salutation, .custom-empty-state { border-radius: 16px !important; box-shadow: 0 6px 20px var(--pa-sombra) !important; }
    .custom-empty-state.custom-error-red { border-radius: 16px !important; }
    /* caixas de título dos popups de login/importação (estilo inline) */
    div[style*="border: 2px solid #478c3b"] { border: 1px solid var(--pa-mist) !important; border-left: 5px solid var(--pa-laranja) !important; border-radius: 16px !important; box-shadow: 0 6px 20px var(--pa-sombra) !important; background-color: var(--pa-card) !important; }

    /* diálogos (st.dialog) renderizam fora de .stApp */
    div[data-testid="stDialog"] > div { border-radius: 20px !important; border-top: 5px solid var(--pa-laranja); background-color: var(--pa-card) !important; }
    div[data-testid="stDialog"] div[role="dialog"] { border-radius: 20px !important; background-color: var(--pa-card) !important; }

    /* campos */
    div[data-testid="stTextInputRootElement"], div[data-testid="stDateInputField"],
    div[data-testid="stMultiSelect"] [role="group"], div[data-testid="stSelectbox"] [role="group"] {
        border: 1px solid var(--pa-mist) !important; border-radius: 10px !important;
    }
    div[data-testid="stTextInput"] input::placeholder, div[data-testid="stMultiSelect"] input::placeholder { color: var(--pa-slate) !important; opacity: 0.75 !important; }
    div[data-testid="stTextInputRootElement"]:focus-within, div[data-testid="stDateInputField"]:focus-within,
    div[data-testid="stMultiSelect"] [role="group"]:focus-within, div[data-testid="stSelectbox"] [role="group"]:focus-within,
    div[data-baseweb="select"] > div:focus-within, div[data-baseweb="base-input"]:focus-within {
        background-color: var(--pa-input-bg) !important;
        border-color: var(--pa-verde) !important; box-shadow: 0 0 0 3px color-mix(in srgb, var(--pa-verde) 22%, transparent) !important;
    }
    span[data-baseweb="tag"] { background-color: var(--pa-verde) !important; color: #FFFFFF !important; border-radius: 8px !important; }
    span[data-baseweb="tag"] * { color: #FFFFFF !important; }

    /* botões: seletor descendente (botões com help= ficam dentro de um <span>,
       então "div.stButton > button" não casa com eles) */
    div.stButton button, div.stFormSubmitButton button, div.stDownloadButton button, div.stLinkButton a { transition: all .15s ease; }
    div.stButton button[kind^="primary"], div.stFormSubmitButton button[kind^="primary"], div.stDownloadButton button[kind^="primary"],
    div.stLinkButton a[data-testid="stBaseLinkButton-primary"] {
        background: linear-gradient(135deg, var(--pa-verde), var(--pa-verde-deep)) !important; border: none !important; color: #FFFFFF !important;
        box-shadow: 0 4px 12px color-mix(in srgb, var(--pa-verde) 33%, transparent);
    }
    div.stButton button[kind^="primary"] p, div.stFormSubmitButton button[kind^="primary"] p, div.stDownloadButton button[kind^="primary"] p,
    div.stLinkButton a[data-testid="stBaseLinkButton-primary"] p { color: #FFFFFF !important; }
    div.stButton button[kind^="primary"]:hover, div.stFormSubmitButton button[kind^="primary"]:hover, div.stDownloadButton button[kind^="primary"]:hover,
    div.stLinkButton a[data-testid="stBaseLinkButton-primary"]:hover {
        background: linear-gradient(135deg, var(--pa-verde), var(--pa-verde-deep)) !important; border: none !important;
        transform: translateY(-1px); box-shadow: 0 6px 16px color-mix(in srgb, var(--pa-verde) 47%, transparent);
    }
    div.stButton button[kind^="secondary"], div.stFormSubmitButton button[kind^="secondary"], div.stDownloadButton button[kind^="secondary"],
    div.stLinkButton a:not([data-testid="stBaseLinkButton-primary"]) {
        background-color: var(--pa-card) !important; border: 1.5px solid var(--pa-laranja) !important; color: var(--pa-ink) !important;
    }
    div.stButton button[kind^="secondary"]:hover, div.stFormSubmitButton button[kind^="secondary"]:hover, div.stDownloadButton button[kind^="secondary"]:hover,
    div.stLinkButton a:not([data-testid="stBaseLinkButton-primary"]):hover {
        background-color: var(--pa-laranja) !important; border-color: var(--pa-laranja) !important; color: #20170A !important; transform: translateY(-1px);
    }
    div.stButton button[kind^="secondary"]:hover p, div.stFormSubmitButton button[kind^="secondary"]:hover p, div.stDownloadButton button[kind^="secondary"]:hover p,
    div.stLinkButton a:not([data-testid="stBaseLinkButton-primary"]):hover p { color: #20170A !important; }
    div.stButton button:disabled, div.stFormSubmitButton button:disabled { opacity: 0.5; transform: none; box-shadow: none; }
"""


def aplicar_visual_pa():
    """Injeta o visual PA. Chamar logo depois de comum.aplicar_estilos()."""
    st.markdown(f"<style>{_css_vars_tema()}\n{CSS_PA}</style>", unsafe_allow_html=True)
