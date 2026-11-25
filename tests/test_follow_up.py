"""Testes das regras do Funil de Follow Up (follow_up.py)."""

from datetime import date

import gspread
import pandas as pd
import pytest

import follow_up as fu

HOJE = date(2026, 11, 25)
CAB = ["STATUS", "PEDIDO", "FORNECEDOR", "SOLICITAÇÃO", "VALOR TOTAL", "PREVISÃO DE ENTREGA",
       "ENTREGA", "CONDIÇÃO PAGAMENTO", "QTD", "PREÇO UNITÁRIO"]


def df_de(linhas):
    return pd.DataFrame(linhas, columns=CAB, dtype=str)


def linha(status="ENVIADO AO FORNECEDOR", pedido="100", forn="ACME LTDA", sc="1", valor="R$ 100,00",
          prev="20/11/2026", entrega="", cond="30 DDL", qtd="1", preco="100"):
    return [status, pedido, forn, sc, valor, prev, entrega, cond, qtd, preco]


class TestMontarCards:
    def test_agrupa_itens_do_mesmo_pedido_e_soma_valor(self):
        df = df_de([linha(valor="R$ 100,00"), linha(valor="R$ 50,50", sc="2")])
        cards = fu.montar_cards(df, HOJE)
        assert len(cards) == 1
        assert cards[0]["valor"] == 150.50 and cards[0]["itens"] == 2 and cards[0]["scs"] == ["1", "2"]

    def test_linhas_fisicas_seguem_o_index_original(self):
        df = df_de([linha(pedido="1"), linha(pedido="2")])
        df.index = [5, 9]
        cards = {c["pedido"]: c for c in fu.montar_cards(df, HOJE)}
        assert cards["1"]["linhas"] == [7] and cards["2"]["linhas"] == [11]

    def test_status_diferentes_do_mesmo_pedido_viram_dois_cartoes(self):
        df = df_de([linha(status="APROVADO"), linha(status="ENVIADO AO FORNECEDOR")])
        assert len(fu.montar_cards(df, HOJE)) == 2

    def test_ignora_status_fora_do_funil(self):
        df = df_de([linha(status="REJEITADO"), linha(status="EXCLUÍDO DO TOTVS"), linha(status="CONTRATO")])
        assert fu.montar_cards(df, HOJE) == []

    def test_status_com_acento_diferente_e_reconhecido(self):
        df = df_de([linha(status="Correcao de processo")])
        assert fu.montar_cards(df, HOJE)[0]["status"] == "CORREÇÃO DE PROCESSO"

    def test_condicao_pago_sem_entrega_e_compra_direta_fora_do_funil(self):
        assert fu.montar_cards(df_de([linha(cond="PAGO")]), HOJE) == []

    def test_valor_zerado_sem_entrega_e_erro_fora_do_funil(self):
        assert fu.montar_cards(df_de([linha(preco="0,00")]), HOJE) == []
        assert fu.montar_cards(df_de([linha(qtd="0")]), HOJE) == []

    def test_preco_em_branco_nao_e_zero(self):
        assert len(fu.montar_cards(df_de([linha(preco="")]), HOJE)) == 1

    def test_atendido_so_ultimos_30_dias(self):
        df = df_de([
            linha(status="ATENDIDO", pedido="1", entrega="10/11/2026"),
            linha(status="ATENDIDO", pedido="2", entrega="01/09/2026"),
            linha(status="ATENDIDO", pedido="3", entrega=""),
        ])
        assert [c["pedido"] for c in fu.montar_cards(df, HOJE)] == ["1"]

    def test_pedido_com_ponto_zero_e_normalizado(self):
        assert fu.montar_cards(df_de([linha(pedido="190101.0")]), HOJE)[0]["pedido"] == "190101"

    def test_ordena_por_atraso_dentro_da_coluna(self):
        df = df_de([linha(pedido="1", prev="30/11/2026"), linha(pedido="2", prev="10/11/2026"), linha(pedido="3", prev="")])
        assert [c["pedido"] for c in fu.montar_cards(df, HOJE)] == ["2", "1", "3"]


class TestPrazo:
    def card(self, previsao, status="ENVIADO AO FORNECEDOR"):
        return fu.montar_cards(df_de([linha(status=status, prev=previsao)]), HOJE)[0]

    @pytest.mark.parametrize("prev,classe,texto", [
        ("20/11/2026", "late", "Atrasado 5d"),
        ("25/11/2026", "soon", "Vence hoje"),
        ("27/11/2026", "soon", "Em 2d"),
        ("10/12/2026", "ok", "No prazo"),
        ("", "none", "Sem previsão"),
    ])
    def test_classes(self, prev, classe, texto):
        assert fu.prazo(self.card(prev)) == (classe, texto)

    def test_atendido_mostra_data_de_entrega(self):
        df = df_de([linha(status="ATENDIDO", entrega="20/11/2026")])
        assert fu.prazo(fu.montar_cards(df, HOJE)[0]) == ("done", "Entregue 20/11")


class TestPermissoes:
    def test_so_almoxarifado_move(self):
        assert fu.pode_mover("almoxarifado", "APROVADO", "ENVIADO AO FORNECEDOR")
        for dep in ("compras", "logistica", "gestor", "", None):
            assert not fu.pode_mover(dep, "APROVADO", "ENVIADO AO FORNECEDOR")

    def test_almoxarifado_nao_vai_para_financeiro_nem_atendido(self):
        assert not fu.pode_mover("almoxarifado", "ENVIADO AO FINANCEIRO", "APROVADO")
        assert not fu.pode_mover("almoxarifado", "ATENDIDO", "APROVADO")

    def test_nao_move_para_a_mesma_coluna(self):
        assert not fu.pode_mover("almoxarifado", "APROVADO", "APROVADO")

    def test_destino_com_acento(self):
        assert fu.pode_mover("almoxarifado", "CORREÇÃO DE PROCESSO", "APROVADO")


class TestFiltros:
    def setup_method(self):
        df = df_de([linha(pedido="1", forn="ACME LTDA", prev="20/11/2026"),
                    linha(pedido="2", forn="BETA SA", prev="10/12/2026", sc="777")])
        self.cards = fu.montar_cards(df, HOJE)

    def test_por_fornecedor(self):
        assert [c["pedido"] for c in fu.filtrar(self.cards, fornecedor="BETA SA")] == ["2"]

    def test_busca_por_pedido_sc_ou_nome_sem_acento(self):
        assert [c["pedido"] for c in fu.filtrar(self.cards, busca="777")] == ["2"]
        assert [c["pedido"] for c in fu.filtrar(self.cards, busca="acme")] == ["1"]

    def test_so_atrasados(self):
        assert [c["pedido"] for c in fu.filtrar(self.cards, so_atrasados=True)] == ["1"]

    def test_resumo_e_contagem(self):
        assert fu.resumo(self.cards) == {"pedidos": 2, "valor": 200.0, "atrasados": 1}
        assert fu.fornecedores_com_contagem(self.cards) == {"ACME LTDA": 1, "BETA SA": 1}


class FakeWS:
    def __init__(self, dados):
        self.dados = [list(l) for l in dados]
        self.escritas = []

    def get_all_values(self):
        return self.dados

    def update_cells(self, celulas, value_input_option=None):
        for c in celulas:
            self.dados[c.row - 1][c.col - 1] = c.value
            self.escritas.append((c.row, c.col, c.value))

    def batch_get(self, ranges):
        saida = []
        for r in ranges:
            row, col = gspread.utils.a1_to_rowcol(r)
            saida.append([[self.dados[row - 1][col - 1]]])
        return saida


class TestGravarStatus:
    def montar(self):
        dados = [CAB, linha(pedido="10"), linha(pedido="10"), linha(pedido="11")]
        ws = FakeWS(dados)
        df = df_de(dados[1:])  # index 0..2 -> linhas físicas 2..4, como a aba real
        card = [c for c in fu.montar_cards(df, HOJE) if c["pedido"] == "10"][0]
        return ws, card

    def test_grava_em_todas_as_linhas_do_pedido(self):
        ws, card = self.montar()
        ok, msg = fu.gravar_status(ws, card, "APROVADO", "almoxarifado")
        assert ok, msg
        assert ws.dados[1][0] == "APROVADO" and ws.dados[2][0] == "APROVADO"
        assert ws.dados[3][0] == "ENVIADO AO FORNECEDOR"  # outro pedido intocado
        assert "Aprovado" in msg

    def test_perfil_sem_permissao_nao_grava(self):
        ws, card = self.montar()
        ok, _ = fu.gravar_status(ws, card, "APROVADO", "compras")
        assert not ok and ws.escritas == []

    def test_planilha_mudou_nao_grava(self):
        ws, card = self.montar()
        ws.dados[2][1] = "999"  # importação mexeu nessa linha depois do quadro carregar
        ok, msg = fu.gravar_status(ws, card, "APROVADO", "almoxarifado")
        assert not ok and "mudou" in msg and ws.escritas == []

    def test_status_de_origem_mudou_nao_grava(self):
        ws, card = self.montar()
        ws.dados[1][0] = "PAGO"
        ok, _ = fu.gravar_status(ws, card, "APROVADO", "almoxarifado")
        assert not ok and ws.escritas == []

    def test_destino_com_acento_grava_o_texto_oficial(self):
        ws, card = self.montar()
        ok, _ = fu.gravar_status(ws, card, "CORREÇÃO DE PROCESSO", "almoxarifado")
        assert ok and ws.dados[1][0] == "CORREÇÃO DE PROCESSO"
