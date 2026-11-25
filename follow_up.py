"""Regras do Funil de Follow Up (pages/2_Funil_Follow_Up.py).

Quadro Kanban sobre a MESMA aba "Pedidos" do painel principal: uma coluna por
status, um cartão por Pedido (+ status). Mudar o cartão de coluna grava o novo
Status nas linhas do pedido na planilha, e o painel SGC (que lê a mesma aba)
mostra a mudança na próxima leitura (cache de 60 s).

Sem dependência do Streamlit - só regra, pra poder testar.
"""

import os
import unicodedata
from datetime import date, timedelta

import gspread

from comum import converter_para_numerico, formatar_para_dd_mm_aaaa, parse_data_br

# Data do arquivo ao importar: a página recarrega o módulo se mudou (o Streamlit Cloud só relê o main.py).
_MTIME_AO_IMPORTAR = os.path.getmtime(__file__)

# (status gravado na planilha, rótulo da coluna, cor da faixa)
COLUNAS_FUNIL = [
    ("APROVADO", "Aprovado", "#f3cf3a"),
    ("ENVIADO AO FORNECEDOR", "Enviado ao fornecedor", "#a45ee6"),
    ("ENVIADO AO FINANCEIRO", "Enviado ao financeiro", "#6bd35a"),
    ("PAGO", "Pago", "#2f6df6"),
    ("ENTREGA PARCIAL", "Entrega parcial", "#f08a3c"),
    ("FORNECEDOR DECLINOU", "Fornecedor declinou", "#e0457b"),
    ("CORREÇÃO DE PROCESSO", "Correção de processo", "#14808f"),
    ("ATENDIDO", "Atendido (30 dias)", "#8b95a3"),
]
ROTULOS = {sid: rotulo for sid, rotulo, _ in COLUNAS_FUNIL}
IDS_FUNIL = [sid for sid, _, _ in COLUNAS_FUNIL]

STATUS_ATENDIDO = "ATENDIDO"            # só vem do Totvs (ou perfil gestor): nunca é destino do quadro
STATUS_FINANCEIRO = "ENVIADO AO FINANCEIRO"  # Almoxarifado não escolhe (decisão do usuário, 2026-11-24)
DEPARTAMENTO_QUE_MOVE = "almoxarifado"       # todos veem; só o Almoxarifado muda cartão de lugar
DIAS_ATENDIDO_VISIVEL = 30
DIAS_AVISO_VENCIMENTO = 3

_ID_POR_CHAVE = {}  # preenchido abaixo de _chave: "CORRECAO DE PROCESSO" -> "CORREÇÃO DE PROCESSO"
DESTINOS_ALMOXARIFADO = [sid for sid in IDS_FUNIL if sid not in (STATUS_ATENDIDO, STATUS_FINANCEIRO)]


def _chave(texto):
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn")
    return sem_acento.upper().strip()


_ID_POR_CHAVE.update({_chave(sid): sid for sid in IDS_FUNIL})


def _numero_pedido(valor):
    txt = str(valor).strip()
    if txt.endswith(".0"):
        txt = txt[:-2]
    return txt


def _data(valor):
    return parse_data_br(formatar_para_dd_mm_aaaa(valor))


def _numero_zero_explicito(valor):
    txt = str(valor).strip()
    return txt != "" and converter_para_numerico(txt) == 0 and any(ch.isdigit() for ch in txt)


def pode_mover(departamento, destino, origem=None):
    """Só o Almoxarifado move cartão, só para as colunas permitidas a ele."""
    if str(departamento or "").strip().lower() != DEPARTAMENTO_QUE_MOVE:
        return False
    if origem is not None and _chave(origem) == _chave(destino):
        return False
    return _chave(destino) in {_chave(s) for s in DESTINOS_ALMOXARIFADO}


def montar_cards(df, hoje=None):
    """DataFrame da aba Pedidos (index = linha física - 2, nunca resetar) -> lista de
    cartões (um por Pedido+Status) ordenados por urgência dentro de cada status."""
    hoje = hoje or date.today()
    if df is None or df.empty:
        return []
    por_nome = {_chave(c): c for c in df.columns}
    c_status, c_pedido = por_nome.get("STATUS"), por_nome.get("PEDIDO")
    if not c_status or not c_pedido:
        return []
    c_forn = por_nome.get("FORNECEDOR")
    c_sc = por_nome.get("SOLICITACAO")
    c_valor = por_nome.get("VALOR TOTAL")
    c_prev = por_nome.get("PREVISAO DE ENTREGA")
    c_entrega = por_nome.get("ENTREGA")
    c_cond = por_nome.get("CONDICAO PAGAMENTO")
    c_qtd, c_preco = por_nome.get("QTD"), por_nome.get("PRECO UNITARIO")
    limite_atendido = hoje - timedelta(days=DIAS_ATENDIDO_VISIVEL)

    grupos = {}
    for idx, linha in df.iterrows():
        status = _ID_POR_CHAVE.get(_chave(linha[c_status]))
        if status is None:
            continue
        pedido = _numero_pedido(linha[c_pedido])
        if not pedido:
            continue
        entrega_txt = str(linha[c_entrega]).strip() if c_entrega else ""
        sem_entrega = entrega_txt == ""
        # Mesmas regras de exibição do painel SGC: CONDIÇÃO "PAGO" sem entrega = COMPRA DIRETA;
        # qtd/preço zerados sem entrega = ERRO. Nenhum dos dois entra no funil.
        if sem_entrega and status != "CONTRATO":
            if c_cond and _chave(linha[c_cond]) == "PAGO":
                continue
            if (c_qtd and _numero_zero_explicito(linha[c_qtd])) or (c_preco and _numero_zero_explicito(linha[c_preco])):
                continue
        entrega = _data(entrega_txt) if entrega_txt else None
        if status == STATUS_ATENDIDO and (entrega is None or entrega < limite_atendido):
            continue

        g = grupos.setdefault((pedido, status), {
            "pedido": pedido, "status": status, "fornecedor": "", "scs": [], "valor": 0.0,
            "itens": 0, "linhas": [], "previsoes": [], "entregas": [], "cond": "",
        })
        g["linhas"].append(int(idx) + 2)
        g["itens"] += 1
        if c_forn and not g["fornecedor"]:
            g["fornecedor"] = str(linha[c_forn]).strip()
        if c_sc:
            sc = _numero_pedido(linha[c_sc])
            if sc and sc not in g["scs"]:
                g["scs"].append(sc)
        if c_valor:
            g["valor"] += converter_para_numerico(linha[c_valor])
        if c_prev:
            d = _data(linha[c_prev])
            if d:
                g["previsoes"].append(d)
        if entrega:
            g["entregas"].append(entrega)
        if c_cond and not g["cond"]:
            g["cond"] = str(linha[c_cond]).strip()

    cards = []
    for g in grupos.values():
        previsao = min(g["previsoes"]) if g["previsoes"] else None
        entrega = max(g["entregas"]) if g["entregas"] else None
        g["previsao"] = previsao
        g["entrega"] = entrega
        g["dias"] = (previsao - hoje).days if previsao else None
        g["valor"] = round(g["valor"], 2)
        g["fornecedor"] = g["fornecedor"] or "(sem fornecedor)"
        cards.append(g)
    cards.sort(key=lambda c: (IDS_FUNIL.index(c["status"]), c["dias"] is None, c["dias"] if c["dias"] is not None else 0, c["pedido"]))
    return cards


def prazo(card):
    """(classe CSS, texto) do indicador de prazo no canto do cartão."""
    if card["status"] == STATUS_ATENDIDO:
        return "done", ("Entregue " + card["entrega"].strftime("%d/%m")) if card.get("entrega") else "Atendido"
    if card["status"] == "PAGO":
        return "done", "Pago"
    dias = card.get("dias")
    if dias is None:
        return "none", "Sem previsão"
    if dias < 0:
        return "late", f"Atrasado {abs(dias)}d"
    if dias == 0:
        return "soon", "Vence hoje"
    if dias <= DIAS_AVISO_VENCIMENTO:
        return "soon", f"Em {dias}d"
    return "ok", "No prazo"


def esta_atrasado(card):
    return prazo(card)[0] == "late"


def filtrar(cards, fornecedor=None, busca="", so_atrasados=False):
    busca = _chave(busca)
    saida = []
    for c in cards:
        if fornecedor and c["fornecedor"] != fornecedor:
            continue
        if busca and busca not in _chave(" ".join([c["fornecedor"], c["pedido"], *c["scs"]])):
            continue
        if so_atrasados and not esta_atrasado(c):
            continue
        saida.append(c)
    return saida


def resumo(cards):
    return {
        "pedidos": len(cards),
        "valor": round(sum(c["valor"] for c in cards), 2),
        "atrasados": sum(1 for c in cards if esta_atrasado(c)),
    }


def fornecedores_com_contagem(cards):
    """{fornecedor: nº de pedidos abertos}, só status ainda em andamento (sem Atendido/Pago)."""
    contagem = {}
    for c in cards:
        if c["status"] in (STATUS_ATENDIDO, "PAGO"):
            continue
        contagem[c["fornecedor"]] = contagem.get(c["fornecedor"], 0) + 1
    return contagem


def gravar_status(worksheet, card, destino, departamento):
    """Grava o novo Status nas linhas do cartão. Confere antes de escrever que cada
    linha ainda é do pedido e ainda está no status de origem (a planilha pode ter
    mudado numa importação depois que o quadro carregou) e confere depois que gravou.
    Devolve (ok, mensagem)."""
    if not pode_mover(departamento, destino, card["status"]):
        return False, "Este perfil não pode mover o pedido para essa coluna."
    dados = worksheet.get_all_values()
    if not dados:
        return False, "Planilha vazia."
    cabecalho = [_chave(c) for c in dados[0]]
    try:
        col_status = cabecalho.index("STATUS") + 1
        col_pedido = cabecalho.index("PEDIDO")
    except ValueError:
        return False, "Colunas STATUS/PEDIDO não encontradas na aba Pedidos."
    for linha in card["linhas"]:
        atual = dados[linha - 1] if linha - 1 < len(dados) else []
        pedido_atual = _numero_pedido(atual[col_pedido]) if len(atual) > col_pedido else ""
        status_atual = _chave(atual[col_status - 1]) if len(atual) >= col_status else ""
        if pedido_atual != card["pedido"] or status_atual != _chave(card["status"]):
            return False, ("A planilha mudou desde que o quadro foi carregado (linha "
                           f"{linha}). Clique em Atualizar e tente de novo. Nada foi gravado.")
    celulas = [gspread.Cell(linha, col_status, destino) for linha in card["linhas"]]
    worksheet.update_cells(celulas, value_input_option="RAW")
    ranges = [gspread.utils.rowcol_to_a1(c.row, c.col) for c in celulas]
    conferido = worksheet.batch_get(ranges)
    for rng, resultado in zip(ranges, conferido):
        valor = resultado[0][0] if resultado and resultado[0] else ""
        if _chave(valor) != _chave(destino):
            return False, f"A gravação não foi confirmada na célula {rng} (a planilha mostra \"{valor}\")."
    return True, f"Pedido {card['pedido']} movido para {ROTULOS.get(_ID_POR_CHAVE.get(_chave(destino), destino), destino)}."
