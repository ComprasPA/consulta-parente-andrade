"""Testes das regras do Funil de Follow Up (follow_up.py) e da geração do HTML (funil_tela.py)."""

import re
from datetime import date

import pandas as pd
import pytest

import follow_up as fu
import funil_tela

HOJE = date(2026, 11, 25)  # quarta-feira
CAB = ["STATUS", "PEDIDO", "FORNECEDOR", "SOLICITAÇÃO", "VALOR TOTAL", "PREVISÃO DE ENTREGA", "ENTREGA", "CONDIÇÃO PAGAMENTO",
       "QTD", "PREÇO UNITÁRIO", "CENTRO DE CUSTO", "DATA PEDIDO", "LOGISTICA", "PREV LOG", "CRITICIDADE", "DATA SC", "DESCRICAO"]


def df_de(linhas):
    return pd.DataFrame(linhas, columns=CAB, dtype=str)


def linha(status="ENVIADO AO FORNECEDOR", pedido="100", forn="ACME LTDA", sc="1", valor="R$ 100,00", prev="20/11/2026",
          entrega="", cond="30 DDL", qtd="1", preco="100", cc="1238", dped="10/11/2026", log="", plog="", crit="", dsc="", desc="Item"):
    return [status, pedido, forn, sc, valor, prev, entrega, cond, qtd, preco, cc, dped, log, plog, crit, dsc, desc]


def cartoes(linhas, **kw):
    return fu.montar_cards(df_de(linhas), HOJE, **kw) if kw else fu.montar_cards(df_de(linhas), HOJE)


class TestAlmoxarifado:
    def test_agrupa_itens_do_pedido_e_soma_valor(self):
        cs = cartoes([linha(valor="R$ 100,00"), linha(valor="R$ 50,50", sc="2")])
        assert len(cs) == 1 and cs[0]["valor"] == 150.50 and cs[0]["itens"] == 2 and cs[0]["scs"] == ["1", "2"]
        assert cs[0]["bloco"] == "Almoxarifado" and cs[0]["col"] == "ENVIADO AO FORNECEDOR"

    def test_status_diferentes_do_mesmo_pedido_viram_dois_cartoes(self):
        assert len(cartoes([linha(status="ENVIADO AO FINANCEIRO"), linha(status="ENTREGA PARCIAL")])) == 2

    def test_ignora_status_fora_do_funil(self):
        assert cartoes([linha(status="REJEITADO"), linha(status="EXCLUÍDO DO TOTVS"), linha(status="CONTRATO"), linha(status="COMPRA DIRETA")]) == []

    def test_condicao_pago_sem_entrega_e_valor_zerado_ficam_fora(self):
        assert cartoes([linha(cond="PAGO")]) == []
        assert cartoes([linha(preco="0,00")]) == []
        assert cartoes([linha(qtd="0")]) == []
        assert len(cartoes([linha(preco="")])) == 1

    def test_atendido_so_ultimos_30_dias(self):
        cs = cartoes([linha(status="ATENDIDO", pedido="1", entrega="10/11/2026"), linha(status="ATENDIDO", pedido="2", entrega="01/09/2026"),
                      linha(status="ATENDIDO", pedido="3", entrega="")])
        assert [c["pedido"] for c in cs] == ["1"]

    @pytest.mark.parametrize("prev,classe,texto,atrasado", [
        ("20/11/2026", "late", "Atrasado 5d", True),
        ("25/11/2026", "soon", "Vence hoje", False),
        ("27/11/2026", "soon", "Em 2d", False),
        ("10/12/2026", "ok", "No prazo", False),
        ("", "none", "Sem previsão", False),
    ])
    def test_prazo_pela_previsao_de_entrega(self, prev, classe, texto, atrasado):
        c = cartoes([linha(prev=prev)])[0]
        assert (c["pz_cls"], c["pz_txt"], c["atrasado"]) == (classe, texto, atrasado)

    def test_atendido_nunca_e_atrasado(self):
        c = cartoes([linha(status="ATENDIDO", prev="01/11/2026", entrega="20/11/2026")])[0]
        assert not c["atrasado"] and c["pz_txt"] == "Entregue 20/11"

    def test_ordena_pelo_mais_atrasado(self):
        cs = cartoes([linha(pedido="1", prev="30/11/2026"), linha(pedido="2", prev="10/11/2026"), linha(pedido="3", prev="")])
        assert [c["pedido"] for c in cs] == ["2", "1", "3"]

    def test_pedido_com_ponto_zero(self):
        assert cartoes([linha(pedido="190101.0")])[0]["pedido"] == "190101"


class TestCompras:
    def sc(self, status="EM COTAÇÃO", crit="ROTINEIRA", dsc="20/11/2026", sc="777", desc="Cabo 4 mm"):
        # linha sintética de solicitação: sem pedido, sem fornecedor
        return linha(status=status, pedido="", forn="", sc=sc, valor="", prev="", dped="", crit=crit, dsc=dsc, desc=desc)

    def test_solicitacao_vira_cartao_por_sc_com_a_descricao_como_titulo(self):
        cs = cartoes([self.sc(), self.sc()])
        assert len(cs) == 1 and cs[0]["itens"] == 2 and cs[0]["titulo"] == "Cabo 4 mm"
        assert cs[0]["bloco"] == "Compras" and cs[0]["col"] == "EM COTAÇÃO"

    def test_aguardando_cotacao_sem_acento(self):
        assert cartoes([self.sc(status="Aguardando Cotacao")])[0]["col"] == "AGUARDANDO COTAÇÃO"

    def test_emergencial_3_dias_uteis(self):
        # SC aprovada na segunda 23/11: 3 dias úteis => quinta 26/11. Hoje é quarta 25/11 => resta 1 dia útil
        c = cartoes([self.sc(crit="EMERGENCIAL", dsc="23/11/2026")])[0]
        assert (c["pz_cls"], c["pz_txt"], c["atrasado"]) == ("soon", "Resta 1 dia útil", False)

    def test_emergencial_atrasada_pula_fim_de_semana(self):
        # aprovada na sexta 13/11: 3 dias úteis => quarta 18/11; hoje 25/11 => 5 dias úteis de atraso
        c = cartoes([self.sc(crit="EMERGENCIAL", dsc="13/11/2026")])[0]
        assert c["atrasado"] and c["pz_txt"] == "Atrasada 5 dias úteis"

    def test_rotineira_15_dias_corridos(self):
        c = cartoes([self.sc(crit="ROTINEIRA", dsc="05/11/2026")])[0]  # limite 20/11 => atrasada 5d
        assert c["atrasado"] and c["pz_txt"] == "Atrasada 5d"
        c = cartoes([self.sc(crit="ROTINEIRA", dsc="24/11/2026")])[0]  # limite 09/12 => no prazo
        assert (c["pz_cls"], c["atrasado"]) == ("ok", False)

    def test_vence_hoje_rotineira(self):
        c = cartoes([self.sc(crit="ROTINEIRA", dsc="10/11/2026")])[0]  # limite 25/11
        assert (c["pz_cls"], c["pz_txt"]) == ("soon", "Vence hoje")

    @pytest.mark.parametrize("crit", ["COMPRA DIRETA", "CORREÇÃO DE PROCESSO", ""])
    def test_outras_criticidades_nao_tem_prazo_nem_atraso(self, crit):
        c = cartoes([self.sc(crit=crit, dsc="01/09/2026")])[0]
        assert not c["atrasado"] and c["pz_cls"] == "none"

    def test_sem_data_da_sc(self):
        c = cartoes([self.sc(dsc="")])[0]
        assert not c["atrasado"] and c["pz_txt"] == "Sem data da SC"

    def test_pedido_gerado_sem_aprovacao_e_aprovado_nao_enviado(self):
        cs = cartoes([linha(status="PENDENTE DE APROVAÇÃO", pedido="10", crit="EMERGENCIAL", dped="23/11/2026"),
                      linha(status="APROVADO", pedido="11", crit="ROTINEIRA", dped="01/11/2026")])
        por_pedido = {c["pedido"]: c for c in cs}
        assert por_pedido["10"]["col"] == por_pedido["11"]["col"] == "PEDIDO GERADO"
        assert por_pedido["10"]["sub"] == "Sem aprovação" and por_pedido["11"]["sub"] == "Aprovado, não enviado"
        assert por_pedido["11"]["atrasado"]  # rotineira há 24 dias


    def test_pendente_de_aprovacao_conta_dias_corridos(self):
        # pedido de 16/11 ainda sem aprovação; hoje 25/11 => 9 dias corridos; rotineira, limite 01/12 => no prazo
        c = cartoes([linha(status="PENDENTE DE APROVAÇÃO", pedido="10", crit="ROTINEIRA", dped="16/11/2026")])[0]
        assert c["pz_txt"] == "Pendente há 9 dias" and c["sub"] == "Sem aprovação"
        assert (c["pz_cls"], c["atrasado"]) == ("ok", False)

    def test_pendente_de_aprovacao_emergencial_conta_dias_uteis(self):
        c = cartoes([linha(status="PENDENTE DE APROVAÇÃO", pedido="10", crit="EMERGENCIAL", dped="13/11/2026")])[0]
        assert c["pz_txt"] == "Pendente há 8 dias úteis" and c["atrasado"] and c["pz_cls"] == "late"

    def test_pendente_outras_criticidades_dias_corridos(self):
        c = cartoes([linha(status="PENDENTE DE APROVAÇÃO", pedido="10", crit="COMPRA DIRETA", dped="13/11/2026")])[0]
        assert c["pz_txt"] == "Pendente há 12 dias" and not c["atrasado"]

    def test_pendente_singular_e_hoje(self):
        um = cartoes([linha(status="PENDENTE DE APROVAÇÃO", pedido="1", crit="ROTINEIRA", dped="24/11/2026")])[0]
        hoje = cartoes([linha(status="PENDENTE DE APROVAÇÃO", pedido="2", crit="ROTINEIRA", dped="25/11/2026")])[0]
        emerg = cartoes([linha(status="PENDENTE DE APROVAÇÃO", pedido="3", crit="EMERGENCIAL", dped="24/11/2026")])[0]
        assert um["pz_txt"] == "Pendente há 1 dia" and hoje["pz_txt"] == "Pendente desde hoje"
        assert emerg["pz_txt"] == "Pendente há 1 dia útil"

    def test_aprovado_nao_enviado_mantem_o_texto_de_prazo(self):
        c = cartoes([linha(status="APROVADO", pedido="10", crit="EMERGENCIAL", dped="13/11/2026")])[0]
        assert c["pz_txt"].startswith("Atrasada")


class TestLogistica:
    def test_logistica_preenchida_vai_so_para_o_bloco_de_logistica(self):
        cs = cartoes([linha(status="ENTREGA PARCIAL", log="A CAMINHO DA OBRA", plog="30/11/2026")])
        assert len(cs) == 1
        c = cs[0]
        assert (c["bloco"], c["col"]) == ("Logística", "A CAMINHO DA OBRA") and c["st_orig"] == "Entrega parcial"

    def test_prazo_usa_prev_log_e_atrasa(self):
        c = cartoes([linha(status="ATENDIDO", entrega="10/11/2026", log="ENTREGUE NO PEA", plog="20/11/2026")])[0]
        assert c["atrasado"] and c["pz_txt"] == "Atrasado 5d"

    def test_cai_na_previsao_sem_prev_log(self):
        c = cartoes([linha(log="RETIRADO DO ALMOXARIFADO SEDE", prev="30/11/2026")])[0]
        assert not c["atrasado"] and c["pz_cls"] == "ok"

    def test_entregue_na_obra_e_concluido(self):
        c = cartoes([linha(status="ATENDIDO", entrega="10/11/2026", log="ENTREGUE NA OBRA", plog="01/11/2026")])[0]
        assert not c["atrasado"] and c["pz_cls"] == "done"

    def test_status_excluido_nao_entra_mesmo_com_logistica(self):
        assert cartoes([linha(status="REJEITADO", log="A CAMINHO DA OBRA")]) == []

    def test_situacao_de_logistica_desconhecida_e_ignorada(self):
        c = cartoes([linha(log="OUTRA COISA")])[0]
        assert c["bloco"] == "Almoxarifado"


class TestDataFrame:
    def test_vazio_e_sem_coluna_status(self):
        assert fu.montar_cards(pd.DataFrame(), HOJE) == []
        assert fu.montar_cards(None, HOJE) == []
        assert fu.montar_cards(pd.DataFrame({"X": ["1"]}), HOJE) == []

    def test_funciona_sem_as_colunas_opcionais(self):
        df = pd.DataFrame({"STATUS": ["ENVIADO AO FORNECEDOR"], "PEDIDO": ["5"], "FORNECEDOR": ["X"]})
        c = fu.montar_cards(df, HOJE)[0]
        assert c["pedido"] == "5" and c["pz_cls"] == "none"

    def test_resumo(self):
        cs = cartoes([linha(pedido="1", prev="20/11/2026"), linha(pedido="2", prev="10/12/2026")])
        assert fu.resumo(cs) == {"cartoes": 2, "valor": 200.0, "atrasados": 1}


class TestDiasUteis:
    def test_somar_dias_uteis(self):
        assert fu.somar_dias_uteis(date(2026, 11, 13), 3) == date(2026, 11, 18)   # sexta -> quarta
        assert fu.somar_dias_uteis(date(2026, 11, 23), 3) == date(2026, 11, 26)   # segunda -> quinta

    def test_dias_uteis_entre(self):
        assert fu.dias_uteis_entre(date(2026, 11, 18), date(2026, 11, 25)) == 5   # 19,20,23,24,25
        assert fu.dias_uteis_entre(date(2026, 11, 25), date(2026, 11, 25)) == 0


class TestHtml:
    def card(self, titulo="X"):
        return {"bloco": "Compras", "col": "EM COTAÇÃO", "pedido": "", "scs": ["1"], "titulo": titulo, "valor": 0, "itens": 1, "cc": "1238",
                "crit": "", "sub": "", "st_orig": "", "data": "", "pz_cls": "none", "pz_txt": "x", "folga": None, "atrasado": False}

    def test_dados_embutidos_e_sem_placeholders(self):
        html = funil_tela.montar_html([self.card("Cabo 4 mm")], "claro")
        assert "Cabo 4 mm" in html
        assert not any(t in html for t in ("__TOKENS__", "__COLUNAS__", "__DADOS__"))

    def test_texto_com_script_nao_fecha_a_tag(self):
        html = funil_tela.montar_html([self.card("</script><b>x")], "escuro")
        assert html.count("</script>") == 1

    def test_tema_escuro_usa_a_paleta_do_portal(self):
        assert "#0F1311" in funil_tela.montar_html([], "escuro")
        assert "color-scheme: light" in funil_tela.montar_html([], "claro")

    def test_json_dos_dados_e_valido(self):
        html = funil_tela.montar_html([self.card("A & B")], "claro")
        import json
        dados = json.loads(re.search(r"var DADOS = (.*?);\s*// cartões", html, re.S).group(1))
        assert dados[0]["titulo"] == "A & B"
