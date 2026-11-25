"""Funil de Follow Up - quadro Kanban dos Pedidos por Status (Portal Gestão de Compras).

Lê a mesma aba "Pedidos" do painel principal. Todos visualizam; só o perfil
Almoxarifado move cartões, e mover grava o Status na planilha (o painel SGC
mostra a mudança na próxima leitura). Regras em follow_up.py."""

import html as html_lib
import importlib
import os
from datetime import date

import streamlit as st

import comum as _comum
import follow_up as _follow_up

for _modulo in (_comum, _follow_up):
    if getattr(_modulo, "_MTIME_AO_IMPORTAR", None) not in (None, os.path.getmtime(_modulo.__file__)):
        importlib.reload(_modulo)

from comum import (
    FILE_ID,
    _ler_aba_como_df,
    aplicar_estilos,
    formatar_moeda_br,
    inicializar_sessao_login,
    obter_client_gspread,
    renderizar_cabecalho,
    renderizar_popup_login,
    renderizar_rodape,
)
import follow_up as fu

st.set_page_config(
    page_title="Funil de Follow Up | Parente Andrade",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)
aplicar_estilos()
inicializar_sessao_login()
renderizar_cabecalho("Funil de Follow Up")
renderizar_popup_login()

LIMITE_INICIAL_POR_COLUNA = 8
TODOS = "Todos os fornecedores"

st.markdown("""
<style>
.st-key-board_funil [data-testid="stHorizontalBlock"] { overflow-x: auto; flex-wrap: nowrap !important; gap: 14px; padding-bottom: 12px; align-items: flex-start; }
.st-key-board_funil [data-testid="stColumn"] { min-width: 290px; flex: 1 0 290px !important; }
.fu-colhead { text-align: center; padding: 10px 4px 8px; border-bottom: 4px solid var(--c); margin-bottom: 4px; }
.fu-colhead b { display: block; font-weight: 800; font-size: 13px; letter-spacing: .16em; text-transform: uppercase; color: var(--pa-ink); }
.fu-colhead span { font-size: 12px; color: var(--pa-slate-soft); }
.fu-card { display: grid; grid-template-columns: 38px 1fr; column-gap: 10px; row-gap: 2px; }
.fu-av { grid-row: 1 / span 3; width: 38px; height: 38px; border-radius: 50%; display: grid; place-items: center; font-weight: 800; font-size: 12px; color: #fff; }
.fu-top { display: flex; justify-content: space-between; gap: 8px; font-size: 12px; color: var(--pa-slate-soft); }
.fu-top b { color: var(--pa-ink); font-weight: 600; font-size: 13px; }
.fu-forn { font-size: 15px; font-weight: 600; line-height: 1.25; color: var(--pa-verde); overflow-wrap: anywhere; }
.fu-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: 12px; color: var(--pa-slate); }
.fu-tag { border: 1px solid var(--pa-mist); border-radius: 3px; padding: 0 6px; }
.fu-prazo { grid-column: 2; justify-self: end; font-size: 13px; font-weight: 600; display: flex; align-items: center; gap: 5px; }
.fu-prazo::after { content: ""; width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.fu-late { color: #e0457b; } .fu-soon { color: #d9a31a; } .fu-ok { color: #19a37b; } .fu-done, .fu-none { color: var(--pa-slate-soft); }
.fu-resumo { display: flex; flex-wrap: wrap; gap: 6px 22px; font-size: 14px; color: var(--pa-slate); }
.fu-resumo b { color: var(--pa-ink); }
</style>
""", unsafe_allow_html=True)

CORES_AVATAR = ["#e0457b", "#7a5af8", "#14808f", "#d9822b", "#2f6df6", "#19a37b", "#b14fc5", "#c4572f"]


@st.cache_data(ttl=60, show_spinner=False)
def carregar_pedidos():
    client, _ = obter_client_gspread()
    return _ler_aba_como_df(client.open_by_key(FILE_ID), "Pedidos")


def _iniciais(nome):
    partes = [p for p in "".join(ch if ch.isalpha() or ch == " " else "" for ch in nome).split() if p]
    if not partes:
        return "?"
    return (partes[0][0] + (partes[1][0] if len(partes) > 1 else "")).upper()


def _cor_avatar(nome):
    return CORES_AVATAR[sum(ord(c) for c in nome) % len(CORES_AVATAR)]


def mover_cartao(chave_widget, card):
    destino = st.session_state.get(chave_widget)
    st.session_state[chave_widget] = None
    if not destino:
        return
    departamento = st.session_state.departamento_ativo if st.session_state.autenticado else ""
    try:
        client, _ = obter_client_gspread()
        ws = client.open_by_key(FILE_ID).worksheet("Pedidos")
        ok, msg = fu.gravar_status(ws, card, destino, departamento)
    except Exception as e:
        ok, msg = False, f"Erro ao gravar: {e}"
    if ok:
        st.cache_data.clear()
        # o painel principal guarda a leitura na sessão; força reler quando voltar a ele
        st.session_state.pop("dados_globais", None)
    st.session_state.msg_funil = ("ok" if ok else "erro", msg)


def mostrar_mais(status):
    st.session_state[f"fu_lim_{status}"] = st.session_state.get(f"fu_lim_{status}", LIMITE_INICIAL_POR_COLUNA) + LIMITE_INICIAL_POR_COLUNA


# ---------- carga ----------
try:
    df = carregar_pedidos()
except Exception as e:
    st.error(f"❌ Não consegui ler a planilha de Pedidos: {e}")
    st.stop()

hoje = date.today()
todos_cards = fu.montar_cards(df, hoje)
departamento = st.session_state.departamento_ativo if st.session_state.autenticado else ""
pode_editar = departamento == fu.DEPARTAMENTO_QUE_MOVE

# ---------- barra de ações ----------
a1, a2, a3 = st.columns([6, 1.3, 1.3])
with a1:
    if pode_editar:
        st.caption("Perfil **Almoxarifado**: use \"Mover para\" em cada cartão para mudar o status do pedido (grava na planilha).")
    elif st.session_state.autenticado:
        st.caption(f"Perfil **{departamento}**: somente visualização. Só o Almoxarifado move cartões.")
    else:
        st.caption("Somente visualização. Entre como **Almoxarifado** para mover cartões.")
with a2:
    if st.button("🔄 Atualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with a3:
    if not st.session_state.autenticado:
        if st.button("🔐 Operador", use_container_width=True):
            st.session_state.mostrar_popup_login = not st.session_state.mostrar_popup_login
            st.rerun()
    else:
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.departamento_ativo = ""
            st.session_state.mostrar_popup_login = False
            st.rerun()

msg = st.session_state.pop("msg_funil", None)
if msg:
    (st.success if msg[0] == "ok" else st.error)(msg[1])

# ---------- filtros ----------
contagem = fu.fornecedores_com_contagem(todos_cards)
nomes = sorted(contagem, key=lambda n: n.upper())
f1, f2, f3 = st.columns([4, 3, 1.6])
with f1:
    escolhido = st.selectbox(
        "Fornecedor", [TODOS] + nomes, key="fu_fornecedor",
        format_func=lambda n: n if n == TODOS else f"{n}  ({contagem[n]} em aberto)",
    )
with f2:
    busca = st.text_input("Buscar pedido, SC ou fornecedor", key="fu_busca", placeholder="Ex.: 190101")
with f3:
    st.write("")
    so_atrasados = st.toggle("Só atrasados", key="fu_atrasados")

fornecedor = None if escolhido == TODOS else escolhido
cards = fu.filtrar(todos_cards, fornecedor, busca, so_atrasados)
r = fu.resumo(cards)
if fornecedor:
    abertos = [c for c in cards if c["status"] not in (fu.STATUS_ATENDIDO, "PAGO")]
    ra = fu.resumo(abertos)
    st.markdown(
        f'<div class="fu-resumo"><span>Fornecedor: <b>{html_lib.escape(fornecedor)}</b></span>'
        f'<span><b>{ra["pedidos"]}</b> pedidos em aberto</span><span><b>{formatar_moeda_br(ra["valor"])}</b> em aberto</span>'
        f'<span><b>{ra["atrasados"]}</b> atrasados</span></div>', unsafe_allow_html=True)
else:
    st.markdown(
        f'<div class="fu-resumo"><span><b>{r["pedidos"]}</b> pedidos no quadro</span>'
        f'<span><b>{formatar_moeda_br(r["valor"])}</b></span><span><b>{r["atrasados"]}</b> atrasados</span></div>',
        unsafe_allow_html=True)

# ---------- quadro ----------
filtrando = bool(fornecedor or busca.strip() or so_atrasados)
with st.container(key="board_funil"):
    colunas = st.columns(len(fu.COLUNAS_FUNIL))
    for col_idx, (coluna, (sid, rotulo, cor)) in enumerate(zip(colunas, fu.COLUNAS_FUNIL)):
        itens = [c for c in cards if c["status"] == sid]
        soma = sum(c["valor"] for c in itens)
        limite = 10_000 if filtrando else st.session_state.get(f"fu_lim_{sid}", LIMITE_INICIAL_POR_COLUNA)
        with coluna:
            st.markdown(
                f'<div class="fu-colhead" style="--c:{cor}"><b>{html_lib.escape(rotulo)}</b>'
                f'<span>{len(itens)} pedidos · {formatar_moeda_br(soma)}</span></div>',
                unsafe_allow_html=True)
            if not itens:
                st.caption("Nenhum pedido nesta etapa.")
            for card in itens[:limite]:
                classe, texto = fu.prazo(card)
                forn = html_lib.escape(card["fornecedor"])
                tags = [f'{card["itens"]} {"item" if card["itens"] == 1 else "itens"}']
                if card["scs"]:
                    tags.append("SC " + ", ".join(card["scs"][:2]) + ("…" if len(card["scs"]) > 2 else ""))
                tags_html = "".join(f'<span class="fu-tag">{html_lib.escape(t)}</span>' for t in tags)
                previsao = card["previsao"].strftime("%d/%m/%Y") if card["previsao"] else "—"
                with st.container(border=True, key=f"fu_card_{col_idx}_{card['pedido']}"):
                    st.markdown(
                        f'<div class="fu-card"><div class="fu-av" style="background:{_cor_avatar(card["fornecedor"])}">{_iniciais(card["fornecedor"])}</div>'
                        f'<div class="fu-top"><b>Pedido {html_lib.escape(card["pedido"])}</b><span>Prev. {previsao}</span></div>'
                        f'<div class="fu-forn">{forn}</div>'
                        f'<div class="fu-meta"><span>{formatar_moeda_br(card["valor"])}</span>{tags_html}</div>'
                        f'<div class="fu-prazo fu-{classe}">{html_lib.escape(texto)}</div></div>',
                        unsafe_allow_html=True)
                    if pode_editar:
                        destinos = [d for d in fu.DESTINOS_ALMOXARIFADO if d != sid]
                        chave = f"fu_mv_{col_idx}_{card['pedido']}"
                        st.selectbox(
                            "Mover para", destinos, index=None, key=chave,
                            placeholder="Mover para…", label_visibility="collapsed",
                            format_func=lambda d: fu.ROTULOS.get(d, d),
                            on_change=mover_cartao, args=(chave, card),
                        )
            restantes = len(itens) - limite
            if restantes > 0:
                st.button(f"Mostrar mais {restantes}", key=f"fu_mais_{sid}", on_click=mostrar_mais, args=(sid,), use_container_width=True)

st.caption(
    "Cada cartão é um Pedido. Um pedido cujos itens estão em status diferentes aparece em mais de uma coluna. "
    "Atendido mostra só os últimos 30 dias. ATENDIDO e ENVIADO AO FINANCEIRO não podem ser escolhidos pelo Almoxarifado."
)
renderizar_rodape()
