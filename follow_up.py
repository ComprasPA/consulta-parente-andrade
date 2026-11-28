"""Regras do Funil de Follow Up (quadro Kanban abaixo da tabela do portal SGC).

O funil só ESPELHA o portal: recebe o mesmo DataFrame já filtrado que alimenta a
tabela (mesmos filtros de Pedido, SC, Centro de Custo, Status, Data, CNPJ) e monta os
cartões. Nada aqui grava na planilha: o status é alterado no próprio portal e o cartão
muda de coluna na leitura seguinte.

Três blocos:
  Compras      Aguardando cotação, Em cotação (solicitações) e Pedido gerado
               (pedidos sem aprovação ou aprovados e ainda não enviados).
  Almoxarifado Enviado ao fornecedor, Enviado ao financeiro, Entrega parcial e
               Atendido (últimos 30 dias).
  Logística    situação da coluna LOGISTICA do pedido (4 etapas).

Regras de atraso (decisão do usuário):
  Compras       solicitação EMERGENCIAL: 3 dias úteis; ROTINEIRA: 15 dias corridos.
  Almoxarifado  Previsão de Entrega anterior a hoje e pedido ainda não recebido.
  Logística     Prev Log (ou, sem ela, a Previsão de Entrega) anterior a hoje e ainda não
                entregue na obra.

Sem dependência do Streamlit - só regra, pra poder testar.
"""

import os
import unicodedata
from datetime import date, timedelta

import pandas as pd

from comum import converter_para_numerico, formatar_para_dd_mm_aaaa, parse_data_br

# Data do arquivo ao importar: o portal recarrega o módulo se mudou (o Streamlit Cloud só relê o main.py).
_MTIME_AO_IMPORTAR = os.path.getmtime(__file__)

BLOCO_COMPRAS = "Compras"
BLOCO_ALMOX = "Almoxarifado"
BLOCO_LOGISTICA = "Logística"
BLOCOS = [BLOCO_COMPRAS, BLOCO_ALMOX, BLOCO_LOGISTICA]

# (bloco, status como gravado na planilha, rótulo da coluna)
COLUNAS = [
    (BLOCO_COMPRAS, "AGUARDANDO COTAÇÃO", "Aguardando cotação"),
    (BLOCO_COMPRAS, "EM COTAÇÃO", "Em cotação"),
    (BLOCO_COMPRAS, "PEDIDO GERADO", "Pedido gerado"),
    (BLOCO_ALMOX, "ENVIADO AO FORNECEDOR", "Enviado ao fornecedor"),
    (BLOCO_ALMOX, "ENVIADO AO FINANCEIRO", "Enviado ao financeiro"),
    (BLOCO_ALMOX, "ENTREGA PARCIAL", "Entrega parcial"),
    (BLOCO_ALMOX, "ATENDIDO", "Atendido (30 dias)"),
    (BLOCO_LOGISTICA, "RETIRADO DO ALMOXARIFADO SEDE", "Retirado do almoxarifado sede"),
    (BLOCO_LOGISTICA, "ENTREGUE NO PEA", "Entregue no PEA"),
    (BLOCO_LOGISTICA, "A CAMINHO DA OBRA", "A caminho da obra"),
    (BLOCO_LOGISTICA, "ENTREGUE NA OBRA", "Entregue na obra"),
]

DIAS_ATENDIDO_VISIVEL = 30
DIAS_AVISO_VENCIMENTO = 3          # Almoxarifado/Logística: "Em Nd" até 3 dias antes da previsão
DIAS_UTEIS_EMERGENCIAL = 3
DIAS_CORRIDOS_ROTINEIRA = 15

# Status que tiram o pedido do funil mesmo com a coluna LOGISTICA preenchida
_STATUS_FORA = {"EXCLUIDO DO TOTVS", "REJEITADO", "REJEITADO PELO APROVADOR", "CANCELADO", "CANCELADO PELO SOLICITANTE", "ESTORNADO"}
_CONCLUIDOS = {"ATENDIDO", "ENTREGUE NA OBRA"}


def _chave(texto):
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn")
    return sem_acento.upper().strip()


_ID_POR_CHAVE = {_chave(sid): sid for _, sid, _ in COLUNAS}
_BLOCO_POR_ID = {sid: bloco for bloco, sid, _ in COLUNAS}
ROTULOS = {sid: rotulo for _, sid, rotulo in COLUNAS}
_STATUS_ALMOX = {sid for bloco, sid, _ in COLUNAS if bloco == BLOCO_ALMOX}
_ETAPAS_LOGISTICA = {sid for bloco, sid, _ in COLUNAS if bloco == BLOCO_LOGISTICA}


def _numero(valor):
    txt = str(valor).strip()
    return txt[:-2] if txt.endswith(".0") else txt


def _data(valor):
    txt = str(valor).strip()
    if not txt or txt.upper() in ("N/A", "NAN", "NONE", "NAT", "------"):
        return None
    return parse_data_br(formatar_para_dd_mm_aaaa(txt))


def _zero_explicito(valor):
    txt = str(valor).strip()
    return txt != "" and any(ch.isdigit() for ch in txt) and converter_para_numerico(txt) == 0


# ---------------------------------------------------------------- prazos de Compras

def _eh_util(d):
    return d.weekday() < 5


def somar_dias_uteis(inicio, n):
    """Soma n dias úteis (segunda a sexta; feriados não são considerados)."""
    d = inicio
    while n > 0:
        d += timedelta(days=1)
        if _eh_util(d):
            n -= 1
    return d


def dias_uteis_entre(inicio, fim):
    """Quantidade de dias úteis depois de `inicio` até `fim` (inclui o fim)."""
    n, d = 0, inicio
    while d < fim:
        d += timedelta(days=1)
        if _eh_util(d):
            n += 1
    return n


def limite_compras(inicio, criticidade):
    """Data limite de Compras: EMERGENCIAL = 3 dias úteis, ROTINEIRA = 15 dias corridos.
    Outras criticidades (COMPRA DIRETA, CORREÇÃO DE PROCESSO, em branco) não têm prazo definido."""
    c = _chave(criticidade)
    if inicio is None:
        return None
    if c == "EMERGENCIAL":
        return somar_dias_uteis(inicio, DIAS_UTEIS_EMERGENCIAL)
    if c == "ROTINEIRA":
        return inicio + timedelta(days=DIAS_CORRIDOS_ROTINEIRA)
    return None


def prazo_compras(inicio, criticidade, hoje):
    """(classe, texto, folga em dias, atrasado) para solicitações e pedidos ainda não enviados."""
    if inicio is None:
        return "none", "Sem data da SC", None, False
    limite = limite_compras(inicio, criticidade)
    if limite is None:
        return "none", "Sem prazo definido", None, False
    emerg = _chave(criticidade) == "EMERGENCIAL"
    folga = (limite - hoje).days
    if hoje > limite:
        n = dias_uteis_entre(limite, hoje) if emerg else (hoje - limite).days
        unidade = (" dia útil" if n == 1 else " dias úteis") if emerg else "d"
        return "late", f"Atrasada {n}{unidade}", folga, True
    if hoje == limite:
        return "soon", "Vence hoje", folga, False
    resta = dias_uteis_entre(hoje, limite) if emerg else folga
    if resta <= (1 if emerg else DIAS_AVISO_VENCIMENTO):
        unidade = (" dia útil" if resta == 1 else " dias úteis") if emerg else "d"
        return "soon", f"Resta {resta}{unidade}", folga, False
    return "ok", "No prazo", folga, False


def texto_pendente_aprovacao(inicio, hoje):
    """"Pendente há N dias úteis": tempo que o pedido está esperando aprovação (seg-sex, sem feriados)."""
    n = dias_uteis_entre(inicio, hoje) if hoje > inicio else 0
    if n == 0:
        return "Pendente desde hoje"
    return f"Pendente há {n} dia útil" if n == 1 else f"Pendente há {n} dias úteis"


def prazo_entrega(previsao, hoje):
    """(classe, texto, folga, atrasado) pela data de previsão (Almoxarifado e Logística)."""
    if previsao is None:
        return "none", "Sem previsão", None, False
    dias = (previsao - hoje).days
    if dias < 0:
        return "late", f"Atrasado {abs(dias)}d", dias, True
    if dias == 0:
        return "soon", "Vence hoje", dias, False
    if dias <= DIAS_AVISO_VENCIMENTO:
        return "soon", f"Em {dias}d", dias, False
    return "ok", "No prazo", dias, False


# ---------------------------------------------------------------- montagem dos cartões

def montar_cards(df, hoje=None):
    """DataFrame da aba Pedidos (já filtrado, com as linhas "Em Cotação" das solicitações) ->
    lista de cartões (dict serializável), ordenados por urgência dentro de cada coluna."""
    hoje = hoje or date.today()
    if df is None or df.empty:
        return []
    por_nome = {_chave(c): c for c in df.columns}
    c_status = por_nome.get("STATUS")
    if not c_status:
        return []

    def col(nome):
        return por_nome.get(nome)

    c_pedido, c_forn, c_sc = col("PEDIDO"), col("FORNECEDOR"), col("SOLICITACAO")
    c_valor, c_prev, c_entrega = col("VALOR TOTAL"), col("PREVISAO DE ENTREGA"), col("ENTREGA")
    c_cond, c_qtd, c_preco = col("CONDICAO PAGAMENTO"), col("QTD"), col("PRECO UNITARIO")
    c_cc, c_dped, c_log = col("CENTRO DE CUSTO"), col("DATA PEDIDO"), col("LOGISTICA")
    c_plog, c_crit, c_dsc, c_desc = col("PREV LOG"), col("CRITICIDADE"), col("DATA SC"), col("DESCRICAO")

    status_k = df[c_status].map(_chave)
    log_k = df[c_log].map(_chave) if c_log else pd.Series("", index=df.index)
    logistica_valida = log_k.isin(_ETAPAS_LOGISTICA) & ~status_k.isin(_STATUS_FORA)
    relevante = status_k.isin(_ID_POR_CHAVE) | status_k.isin({"PENDENTE DE APROVACAO", "APROVADO"}) | logistica_valida
    if not relevante.any():
        return []
    sub = df[relevante]
    status_k, log_k, logistica_valida = status_k[relevante], log_k[relevante], logistica_valida[relevante]
    limite_atendido = hoje - timedelta(days=DIAS_ATENDIDO_VISIVEL)

    grupos = {}
    for (idx, linha), st_k, lg_k, eh_log in zip(sub.iterrows(), status_k, log_k, logistica_valida):
        pedido = _numero(linha[c_pedido]) if c_pedido else ""
        sc = _numero(linha[c_sc]) if c_sc else ""
        entrega_txt = str(linha[c_entrega]).strip() if c_entrega else ""
        sem_entrega = entrega_txt == ""

        # Mesmas regras de exibição do portal: PAGO sem entrega = COMPRA DIRETA; qtd/preço zerados
        # sem entrega = ERRO. Nenhum dos dois entra no funil.
        if sem_entrega and st_k not in ("CONTRATO", "COMPRA DIRETA", "ERRO"):
            if c_cond and _chave(linha[c_cond]) == "PAGO":
                continue
            if (c_qtd and _zero_explicito(linha[c_qtd])) or (c_preco and _zero_explicito(linha[c_preco])):
                continue

        if eh_log:
            col_id = _ID_POR_CHAVE[lg_k]
            chave_grupo, extra = (pedido or sc, col_id), {"st_orig": _ID_POR_CHAVE.get(st_k, str(linha[c_status]).strip())}
        elif st_k in ("AGUARDANDO COTACAO", "EM COTACAO"):
            if not sc:
                continue
            col_id = _ID_POR_CHAVE[st_k]
            chave_grupo, extra = (sc, col_id), {}
        elif st_k in ("PENDENTE DE APROVACAO", "APROVADO"):
            if not pedido:
                continue
            col_id = "PEDIDO GERADO"
            chave_grupo = (pedido, col_id)
            extra = {"sub": "Sem aprovação" if st_k == "PENDENTE DE APROVACAO" else "Aprovado, não enviado"}
        elif _ID_POR_CHAVE.get(st_k) in _STATUS_ALMOX:
            if not pedido:
                continue
            col_id = _ID_POR_CHAVE[st_k]
            if col_id == "ATENDIDO":
                d_ent = _data(entrega_txt)
                if d_ent is None or d_ent < limite_atendido:
                    continue
            chave_grupo, extra = (pedido, col_id), {}
        else:
            continue

        g = grupos.get(chave_grupo)
        if g is None:
            g = grupos[chave_grupo] = {
                "col": col_id, "bloco": _BLOCO_POR_ID[col_id], "pedido": pedido, "scs": [], "fornecedor": "", "descricao": "",
                "valor": 0.0, "itens": 0, "cc": "", "crit": "", "previsoes": [], "entregas": [], "prev_log": [],
                "datas_pedido": [], "datas_sc": [], **extra,
            }
        g["itens"] += 1
        if sc and sc not in g["scs"]:
            g["scs"].append(sc)
        if c_forn and not g["fornecedor"]:
            g["fornecedor"] = str(linha[c_forn]).strip()
        if c_desc and not g["descricao"]:
            g["descricao"] = str(linha[c_desc]).strip()
        if c_valor:
            g["valor"] += converter_para_numerico(linha[c_valor])
        if c_cc and not g["cc"]:
            g["cc"] = str(linha[c_cc]).strip()
        if c_crit and not g["crit"]:
            g["crit"] = str(linha[c_crit]).strip()
        for lista, coluna in ((g["previsoes"], c_prev), (g["prev_log"], c_plog), (g["datas_pedido"], c_dped), (g["datas_sc"], c_dsc)):
            if coluna:
                d = _data(linha[coluna])
                if d:
                    lista.append(d)
        d_ent = _data(entrega_txt) if entrega_txt else None
        if d_ent:
            g["entregas"].append(d_ent)

    cards = []
    for g in grupos.values():
        cards.append(_finalizar(g, hoje))
    ordem = {sid: i for i, (_, sid, _) in enumerate(COLUNAS)}
    cards.sort(key=lambda c: (ordem[c["col"]], c["folga"] is None, c["folga"] if c["folga"] is not None else 0, c["pedido"], c["scs"][:1]))
    return cards


def _finalizar(g, hoje):
    col_id, bloco = g["col"], g["bloco"]
    previsao = min(g["previsoes"]) if g["previsoes"] else None
    entrega = max(g["entregas"]) if g["entregas"] else None
    emissao = None
    if bloco == BLOCO_COMPRAS:
        if col_id == "PEDIDO GERADO":
            inicio = min(g["datas_pedido"]) if g["datas_pedido"] else None
        else:
            inicio = min(g["datas_sc"]) if g["datas_sc"] else None
        classe, texto, folga, atrasado = prazo_compras(inicio, g["crit"], hoje)
        if col_id == "PEDIDO GERADO" and g.get("sub") == "Sem aprovação" and inicio is not None:
            # pedido pendente de aprovação: o cartão mostra há quantos dias úteis ele espera a aprovação
            # (a cor e o filtro "Só atrasados" continuam pela regra de prazo da criticidade)
            texto = texto_pendente_aprovacao(inicio, hoje)
        emissao = inicio
    elif bloco == BLOCO_ALMOX:
        emissao = min(g["datas_pedido"]) if g["datas_pedido"] else None
        if col_id == "ATENDIDO":
            classe, texto, folga, atrasado = "done", ("Entregue " + entrega.strftime("%d/%m")) if entrega else "Atendido", None, False
        else:
            classe, texto, folga, atrasado = prazo_entrega(previsao, hoje)
    else:  # Logística
        emissao = min(g["datas_pedido"]) if g["datas_pedido"] else None
        if col_id == "ENTREGUE NA OBRA":
            classe, texto, folga, atrasado = "done", "Entregue na obra", None, False
        elif g.get("st_orig") == "ATENDIDO" and col_id != "ENTREGUE NA OBRA":
            # já recebido no almoxarifado e seguindo para a obra: prazo é o da logística
            alvo = min(g["prev_log"]) if g["prev_log"] else previsao
            classe, texto, folga, atrasado = prazo_entrega(alvo, hoje)
        else:
            alvo = min(g["prev_log"]) if g["prev_log"] else previsao
            classe, texto, folga, atrasado = prazo_entrega(alvo, hoje)

    crit = _chave(g["crit"])
    titulo = g["fornecedor"] or g["descricao"] or "(sem descrição)"
    return {
        "bloco": bloco,
        "col": col_id,
        "pedido": g["pedido"],
        "scs": g["scs"],
        "titulo": titulo,
        "valor": round(g["valor"], 2),
        "itens": g["itens"],
        "cc": g["cc"],
        "crit": crit if crit in ("EMERGENCIAL", "ROTINEIRA") else "",
        "sub": g.get("sub", ""),
        "st_orig": ROTULOS.get(g.get("st_orig", ""), g.get("st_orig", "")),
        "data": emissao.strftime("%d/%m") if emissao else "",
        "pz_cls": classe,
        "pz_txt": texto,
        "folga": folga,
        "atrasado": atrasado,
    }


def resumo(cards):
    return {
        "cartoes": len(cards),
        "valor": round(sum(c["valor"] for c in cards), 2),
        "atrasados": sum(1 for c in cards if c["atrasado"]),
    }
