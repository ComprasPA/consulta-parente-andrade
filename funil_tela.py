"""Tela do Funil de Follow Up: gera o HTML do quadro (funil_template.html) com os cartões de
follow_up.py e mostra abaixo da tabela do portal. O quadro roda num iframe (precisa de JS pra
as barras de rolagem próprias); as cores vêm do tema ativo do portal."""

import json
import os
from datetime import date

import streamlit as st
import streamlit.components.v1 as components

import follow_up as fu
from comum import TEMAS

_MTIME_AO_IMPORTAR = os.path.getmtime(__file__)
_CAMINHO_TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "funil_template.html")
ALTURA_INICIAL = 760  # px; o próprio quadro ajusta o iframe ao conteúdo (ver ajustarIframe no template)

_COR_COLUNA = {
    "AGUARDANDO COTAÇÃO": "var(--c1)", "EM COTAÇÃO": "var(--c2)", "PEDIDO GERADO": "var(--c5)",
    "ENVIADO AO FORNECEDOR": "var(--c2)", "ENVIADO AO FINANCEIRO": "var(--c3)", "ENTREGA PARCIAL": "var(--c5)", "ATENDIDO": "var(--c8)",
    "RETIRADO DO ALMOXARIFADO SEDE": "var(--c4)", "ENTREGUE NO PEA": "var(--c6)", "A CAMINHO DA OBRA": "var(--c1)", "ENTREGUE NA OBRA": "var(--c3)",
}
_SEMANTICAS = {
    "claro": {"late": "#D8383D", "soon": "#C98A0B", "ok": "#3E8E41"},
    "escuro": {"late": "#FF6B6B", "soon": "#F0BB3C", "ok": "#4FA653"},
}


def _tokens_css(tema):
    p = TEMAS.get(tema, TEMAS["claro"])
    sem = _SEMANTICAS.get(tema, _SEMANTICAS["claro"])
    return (
        ":root {"
        f" --page: {p['page-bg']}; --bg: {p['input-bg']}; --surface: {p['card']}; --line: {p['mist']};"
        f" --ink: {p['ink']}; --muted: {p['slate']}; --link: {p['verde']}; --accent: {p['verde']};"
        f" --late: {sem['late']}; --soon: {sem['soon']}; --ok: {sem['ok']}; --done: {p['slate-soft']};"
        f" color-scheme: {'dark' if tema == 'escuro' else 'light'}; }}"
    )


def _json_seguro(obj):
    # vai dentro de <script>: "</" e os separadores de linha unicode poderiam fechar/quebrar o script
    texto = json.dumps(obj, ensure_ascii=False)
    for perigoso, seguro in (("</", "<" + chr(92) + "/"), (chr(0x2028), chr(92) + "u2028"), (chr(0x2029), chr(92) + "u2029")):
        texto = texto.replace(perigoso, seguro)
    return texto


def montar_html(cards, tema="claro"):
    with open(_CAMINHO_TEMPLATE, encoding="utf-8") as f:
        html = f.read()
    colunas = [{"id": sid, "nome": rotulo, "bloco": bloco, "cor": _COR_COLUNA.get(sid, "var(--c8)")} for bloco, sid, rotulo in fu.COLUNAS]
    return (html.replace("__TOKENS__", _tokens_css(tema))
                .replace("__COLUNAS__", _json_seguro(colunas))
                .replace("__DADOS__", _json_seguro(cards)))


def renderizar_funil(df, hoje=None):
    """Mostra o funil para o DataFrame recebido (o mesmo, já filtrado, da tabela do portal).
    Qualquer erro aqui vira um aviso: o funil nunca derruba o portal."""
    try:
        cards = fu.montar_cards(df, hoje or date.today())
        tema = st.session_state.get("tema", "claro")
        components.html(montar_html(cards, tema), height=ALTURA_INICIAL, scrolling=False)
    except Exception as e:  # noqa: BLE001
        st.warning(f"⚠️ Funil de Follow Up indisponível no momento: {e}")
