"""Testes da logica pura de importacao (Protheus -> Google Sheets).

Cobre normalizacao/formatacao de valores, deteccao de tipo de arquivo (PC/SC),
o motor de dedup/atualizacao (`processar_linhas_import`) e a deteccao de
pedidos excluidos no Totvs. Nao cobre I/O real com Google Sheets (gspread) -
essas funcoes recebem um worksheet/spreadsheet fake (stub simples) em vez de
uma conexao de verdade.
"""

from io import BytesIO

import pandas as pd
import pytest

import importador_protheus as ip


# ---------------------------------------------------------------------------
# Normalizadores e limpadores basicos
# ---------------------------------------------------------------------------

class TestNormalizarNome:
    def test_upper_strip(self):
        assert ip.normalizar_nome_import("  produto  ") == "PRODUTO"

    def test_remove_i_e_a_acentuados(self):
        # A funcao so troca Í->I e Ã->A - Ç fica como esta (nao e um bug
        # coberto por esse teste, so o comportamento real e documentado).
        assert ip.normalizar_nome_import("SOLICITAÇÃO") == "SOLICITAÇAO"


class TestNormalizarStatus:
    def test_remove_todos_acentos_via_nfkd(self):
        assert ip.normalizar_status_import("Aprovação") == "APROVACAO"

    def test_vazio_ou_none(self):
        assert ip.normalizar_status_import(None) == ""
        assert ip.normalizar_status_import("") == ""

    def test_strip_e_upper(self):
        assert ip.normalizar_status_import("  pendente  ") == "PENDENTE"


class TestLimparNumeroTexto:
    @pytest.mark.parametrize("valor", ["nan", "None", "NaT", "", "  "])
    def test_valores_vazios_viram_string_vazia(self, valor):
        assert ip.limpar_numero_texto_import(valor) == ""

    def test_remove_sufixo_ponto_zero(self):
        assert ip.limpar_numero_texto_import("179785.0") == "179785"

    def test_mantem_valor_sem_sufixo(self):
        assert ip.limpar_numero_texto_import("179785") == "179785"


class TestValorEZeroOuVazio:
    @pytest.mark.parametrize("valor", ["", "0", "000", None])
    def test_considerado_vazio(self, valor):
        assert ip.valor_e_zero_ou_vazio_import(valor) is True

    @pytest.mark.parametrize("valor", ["007", "10", "abc"])
    def test_nao_considerado_vazio(self, valor):
        assert ip.valor_e_zero_ou_vazio_import(valor) is False


# ---------------------------------------------------------------------------
# Formatadores (FORMATADORES_IMPORT)
# ---------------------------------------------------------------------------

class TestFormatadores:
    def test_fmt_inteiro(self):
        assert ip.fmt_inteiro_import(10.0) == "10"
        assert ip.fmt_inteiro_import("") == ""
        assert ip.fmt_inteiro_import(float("nan")) == ""

    def test_fmt_texto(self):
        assert ip.fmt_texto_import("  Fornecedor X  ") == "Fornecedor X"
        assert ip.fmt_texto_import(float("nan")) == ""

    def test_fmt_produto_zfill_10(self):
        assert ip.fmt_produto_import("123") == "0000000123"
        assert ip.fmt_produto_import("") == ""

    def test_fmt_solicitacao_zfill_6(self):
        assert ip.fmt_solicitacao_import("3419") == "003419"
        assert ip.fmt_solicitacao_import(3419) == "003419"

    def test_fmt_centro_custo_sem_zfill(self):
        # So limpa o ".0" - nao derruba zero a esquerda de verdade.
        assert ip.fmt_centro_custo_import("1223.0") == "1223"
        assert ip.fmt_centro_custo_import("0045") == "0045"

    def test_fmt_numero_inteiro_vs_decimal(self):
        assert ip.fmt_numero_import(5.0) == "5"
        assert ip.fmt_numero_import(5.5) == "5.5"

    def test_fmt_decimal_duas_casas(self):
        assert ip.fmt_decimal_import("10") == "10.00"
        assert ip.fmt_decimal_import(10.5) == "10.50"

    def test_fmt_data_formata_dd_mm_aaaa(self):
        # Entrada real e sempre um valor de data ja tipado (pd.Timestamp),
        # como o pandas devolve ao ler uma celula de data do Excel via
        # pd.read_excel - nao uma string ISO (ver nota de bug em
        # test_ambiguidade_dayfirst_em_string_iso abaixo).
        assert ip.fmt_data_import(pd.Timestamp("2026-09-05")) == "05/09/2026"
        assert ip.fmt_data_import("") == ""

    def test_ambiguidade_dayfirst_em_string_iso(self):
        """Bug latente conhecido (nao corrigido aqui - fora do escopo desta
        tarefa de testes): fmt_data_import usa pd.to_datetime(..., dayfirst=
        True), que forca leitura dia-primeiro mesmo numa string ISO
        (AAAA-MM-DD) ja inequivoca, trocando dia/mes quando ambos sao <=12.
        Esse teste documenta o comportamento ATUAL (nao o desejado) - se
        virar um problema real (fonte de dados passar a entregar string ISO
        em vez de Timestamp/serial do Excel), a correcao é usar
        dayfirst=False quando o formato já é claramente ISO."""
        assert ip.fmt_data_import("2026-09-05") == "09/05/2026"

    def test_fmt_pagamento_calc(self):
        assert ip.fmt_pagamento_calc_import("A VISTA") == ""
        assert ip.fmt_pagamento_calc_import("PAGO") == ""
        assert ip.fmt_pagamento_calc_import("ENT +2PARC") == "------"
        assert ip.fmt_pagamento_calc_import("") == ""


class TestValorStatusOrigem:
    def test_pendente_vira_texto_completo(self):
        linha = {"Status Aprov": "Pendente"}
        assert ip.valor_status_origem_import(linha) == "PENDENTE DE APROVAÇÃO".upper()

    def test_sem_controle_aprovacao_vira_aprovado(self):
        linha = {"Status Aprov": "Não possui controle de Aprovação"}
        assert ip.valor_status_origem_import(linha) == "APROVADO"

    def test_status_desconhecido_mantem_bruto_em_maiusculo(self):
        linha = {"Status Aprov": "Liberado"}
        assert ip.valor_status_origem_import(linha) == "LIBERADO"


# ---------------------------------------------------------------------------
# Resolucao de coluna / lookup
# ---------------------------------------------------------------------------

class TestResolverColuna:
    def test_encontra_por_alias(self):
        cabecalho = ["SOLICITACAO", "PEDIDO"]
        aliases = {"SOLICITAÇÃO": ["SOLICITAÇÃO", "SOLICITACAO"]}
        assert ip.resolver_coluna_real_import(cabecalho, "SOLICITAÇÃO", aliases) == "SOLICITACAO"

    def test_none_quando_nao_encontra(self):
        assert ip.resolver_coluna_real_import(["PEDIDO"], "FORNECEDOR", {}) is None

    def test_construir_lookup_campo(self):
        aliases = {"SOLICITAÇÃO": ["SOLICITACAO"]}
        lookup = ip.construir_lookup_campo_import(["SOLICITAÇÃO", "PEDIDO"], aliases)
        assert lookup[ip.normalizar_nome_import("SOLICITACAO")] == "SOLICITAÇÃO"
        assert lookup[ip.normalizar_nome_import("PEDIDO")] == "PEDIDO"


# ---------------------------------------------------------------------------
# detectar_tipo_arquivo_import - le a assinatura (cabecalho na 2a linha)
# ---------------------------------------------------------------------------

def _montar_xlsx(colunas_cabecalho, linha_titulo="Relatorio Totvs"):
    """Monta um xlsx em memoria no mesmo formato do export do TOTVS: uma
    linha de titulo (ignorada), depois o cabecalho real, depois os dados."""
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame([colunas_cabecalho]).to_excel(
            writer, index=False, header=False, startrow=1
        )
        pd.DataFrame([[linha_titulo] + [""] * (len(colunas_cabecalho) - 1)]).to_excel(
            writer, index=False, header=False, startrow=0
        )
    buf.seek(0)
    return buf


class TestDetectarTipoArquivo:
    def test_reconhece_pedidos(self):
        arquivo = _montar_xlsx(["Numero", "Dt. Dig.Nota", "Nome Fornece"])
        assert ip.detectar_tipo_arquivo_import(arquivo) == "PC"

    def test_reconhece_solicitacoes(self):
        arquivo = _montar_xlsx(["Numero da SC", "Cod SC. SCM", "Produto"])
        assert ip.detectar_tipo_arquivo_import(arquivo) == "SC"

    def test_layout_desconhecido(self):
        arquivo = _montar_xlsx(["Coluna A", "Coluna B"])
        assert ip.detectar_tipo_arquivo_import(arquivo) is None

    def test_reposiciona_cursor_no_inicio_do_arquivo(self):
        """A funcao deve deixar o arquivo pronto pra ser lido de novo depois
        (processar_arquivo_pc_import faz outro read_excel em seguida)."""
        arquivo = _montar_xlsx(["Numero", "Dt. Dig.Nota"])
        ip.detectar_tipo_arquivo_import(arquivo)
        assert arquivo.tell() == 0


# ---------------------------------------------------------------------------
# processar_linhas_import - motor de dedup/atualizacao
# ---------------------------------------------------------------------------

MAPA_SIMPLES = {
    "PEDIDO": {"origem": "Numero", "tipo": "inteiro"},
    "PRODUTO": {"origem": "Produto", "tipo": "produto"},
    "ENTREGA": {"origem": "Dt. Dig.Nota", "tipo": "data"},
    "PREVISÃO DE ENTREGA": {"origem": "Dt. Entrega", "tipo": "data"},
}
CABECALHO_DESTINO = ["PEDIDO", "PRODUTO", "ENTREGA", "PREVISÃO DE ENTREGA", "STATUS"]
CHAVE = ("PEDIDO", "PRODUTO")


def _df_origem(linhas):
    return pd.DataFrame(linhas)


class TestProcessarLinhasImportLinhaNova:
    def test_linha_nova_sem_indice_existente(self):
        df = _df_origem([{"Numero": 100, "Produto": "5", "Dt. Dig.Nota": "", "Dt. Entrega": pd.Timestamp("2026-09-10")}])
        novas, atualizacoes, dup, atualizadas, chaves = ip.processar_linhas_import(
            df, MAPA_SIMPLES, CABECALHO_DESTINO, {}, [], CHAVE, indice_existentes={},
        )
        assert dup == 0
        assert atualizadas == 0
        assert len(novas) == 1
        linha = novas[0]
        assert linha[CABECALHO_DESTINO.index("PEDIDO")] == "100"
        assert linha[CABECALHO_DESTINO.index("PRODUTO")] == "0000000005"
        assert linha[CABECALHO_DESTINO.index("PREVISÃO DE ENTREGA")] == "10/09/2026"

    def test_linha_sem_chave_completa_e_duplicada(self):
        df = _df_origem([{"Numero": "", "Produto": "5", "Dt. Dig.Nota": "", "Dt. Entrega": ""}])
        novas, atualizacoes, dup, atualizadas, chaves = ip.processar_linhas_import(
            df, MAPA_SIMPLES, CABECALHO_DESTINO, {}, [], CHAVE, indice_existentes={},
        )
        assert novas == []
        assert dup == 1


class TestProcessarLinhasImportAtualizacao:
    def _indice_existente(self, row_num=5, **valores_atuais):
        chave = (valores_atuais.get("PEDIDO", ""), valores_atuais.get("PRODUTO", ""))
        base = {c: "" for c in CABECALHO_DESTINO}
        base.update(valores_atuais)
        return {chave: {"row_num": row_num, "valores": base}}

    def test_entrega_sempre_sobrescreve_mesmo_com_valor_antigo(self):
        indice = self._indice_existente(PEDIDO="100", PRODUTO="0000000005", ENTREGA="01/01/2026")
        df = _df_origem([{"Numero": 100, "Produto": "5", "Dt. Dig.Nota": pd.Timestamp("2026-09-10"), "Dt. Entrega": ""}])
        novas, atualizacoes, dup, atualizadas, chaves = ip.processar_linhas_import(
            df, MAPA_SIMPLES, CABECALHO_DESTINO, {}, [], CHAVE, indice_existentes=indice,
        )
        assert novas == []
        assert atualizadas == 1
        col_entrega = CABECALHO_DESTINO.index("ENTREGA") + 1
        assert (5, col_entrega, "10/09/2026") in atualizacoes

    def test_campo_ja_preenchido_nao_e_sobrescrito(self):
        indice = self._indice_existente(
            PEDIDO="100", PRODUTO="0000000005", **{"PREVISÃO DE ENTREGA": "01/01/2026"}
        )
        df = _df_origem([{"Numero": 100, "Produto": "5", "Dt. Dig.Nota": "", "Dt. Entrega": "2026-09-10"}])
        novas, atualizacoes, dup, atualizadas, chaves = ip.processar_linhas_import(
            df, MAPA_SIMPLES, CABECALHO_DESTINO, {}, [], CHAVE, indice_existentes=indice,
        )
        assert novas == []
        assert atualizadas == 0
        assert dup == 1
        assert atualizacoes == []

    def test_status_forcado_para_atendido_quando_entrega_definida_agora(self):
        indice = self._indice_existente(PEDIDO="100", PRODUTO="0000000005", STATUS="PENDENTE")
        df = _df_origem([{"Numero": 100, "Produto": "5", "Dt. Dig.Nota": pd.Timestamp("2026-09-10"), "Dt. Entrega": ""}])
        novas, atualizacoes, dup, atualizadas, chaves = ip.processar_linhas_import(
            df, MAPA_SIMPLES, CABECALHO_DESTINO, {}, [], CHAVE, indice_existentes=indice,
            campo_status="STATUS",
        )
        col_status = CABECALHO_DESTINO.index("STATUS") + 1
        assert (5, col_status, ip.STATUS_ATENDIDO_IMPORT) in atualizacoes

    def test_campos_obrigatorios_ausentes_conta_como_duplicada(self):
        df = _df_origem([{"Numero": 100, "Produto": "", "Dt. Dig.Nota": "", "Dt. Entrega": ""}])
        novas, atualizacoes, dup, atualizadas, chaves = ip.processar_linhas_import(
            df, MAPA_SIMPLES, CABECALHO_DESTINO, {}, [], CHAVE, indice_existentes={},
            campos_obrigatorios=("PRODUTO",),
        )
        assert novas == []
        assert dup == 1


# ---------------------------------------------------------------------------
# detectar_pedidos_excluidos_import
# ---------------------------------------------------------------------------

class TestDetectarPedidosExcluidos:
    CABECALHO = ["PEDIDO", "PRODUTO", "STATUS", "DATA PEDIDO", "ENTREGA"]

    def _hoje_menos(self, dias):
        from datetime import datetime, timedelta
        return (datetime.now().date() - timedelta(days=dias)).strftime("%d/%m/%Y")

    def test_marca_excluido_quando_some_do_arquivo_e_dentro_da_janela(self):
        indice = {
            ("100", "0000000005"): {
                "row_num": 3,
                "valores": {"PEDIDO": "100", "PRODUTO": "0000000005", "STATUS": "PENDENTE",
                            "DATA PEDIDO": self._hoje_menos(5), "ENTREGA": ""},
            }
        }
        atualizacoes = ip.detectar_pedidos_excluidos_import(indice, chaves_deste_arquivo=set(), cabecalho_real=self.CABECALHO)
        assert len(atualizacoes) == 1
        row_num, col, valor = atualizacoes[0]
        assert row_num == 3
        assert valor == ip.STATUS_EXCLUIDO_TOTVS_IMPORT

    def test_nao_marca_se_veio_no_arquivo_deste_ciclo(self):
        chave = ("100", "0000000005")
        indice = {
            chave: {
                "row_num": 3,
                "valores": {"PEDIDO": "100", "PRODUTO": "0000000005", "STATUS": "PENDENTE",
                            "DATA PEDIDO": self._hoje_menos(5), "ENTREGA": ""},
            }
        }
        atualizacoes = ip.detectar_pedidos_excluidos_import(indice, chaves_deste_arquivo={chave}, cabecalho_real=self.CABECALHO)
        assert atualizacoes == []

    def test_nao_marca_se_ja_tem_entrega(self):
        indice = {
            ("100", "0000000005"): {
                "row_num": 3,
                "valores": {"PEDIDO": "100", "PRODUTO": "0000000005", "STATUS": "PENDENTE",
                            "DATA PEDIDO": self._hoje_menos(5), "ENTREGA": "10/09/2026"},
            }
        }
        atualizacoes = ip.detectar_pedidos_excluidos_import(indice, chaves_deste_arquivo=set(), cabecalho_real=self.CABECALHO)
        assert atualizacoes == []

    def test_nao_marca_se_status_ja_e_terminal(self):
        indice = {
            ("100", "0000000005"): {
                "row_num": 3,
                "valores": {"PEDIDO": "100", "PRODUTO": "0000000005", "STATUS": "CANCELADO",
                            "DATA PEDIDO": self._hoje_menos(5), "ENTREGA": ""},
            }
        }
        atualizacoes = ip.detectar_pedidos_excluidos_import(indice, chaves_deste_arquivo=set(), cabecalho_real=self.CABECALHO)
        assert atualizacoes == []

    def test_nao_marca_fora_da_janela_de_dias(self):
        indice = {
            ("100", "0000000005"): {
                "row_num": 3,
                "valores": {"PEDIDO": "100", "PRODUTO": "0000000005", "STATUS": "PENDENTE",
                            "DATA PEDIDO": self._hoje_menos(60), "ENTREGA": ""},
            }
        }
        atualizacoes = ip.detectar_pedidos_excluidos_import(indice, chaves_deste_arquivo=set(), cabecalho_real=self.CABECALHO)
        assert atualizacoes == []


# ---------------------------------------------------------------------------
# Fronteira com Google Sheets (gspread) - usando stubs, sem rede
# ---------------------------------------------------------------------------

class _FakeWorksheet:
    def __init__(self):
        self.append_rows_chamado = None
        self.update_cells_chamado = None

    def append_rows(self, linhas, value_input_option="RAW"):
        self.append_rows_chamado = linhas

    def update_cells(self, celulas, value_input_option="RAW"):
        self.update_cells_chamado = celulas


class TestAplicarNoGoogleSheets:
    def test_so_chama_append_quando_ha_linhas_novas(self):
        ws = _FakeWorksheet()
        ip.aplicar_no_google_sheets_import(ws, [["a", "b"]], [])
        assert ws.append_rows_chamado == [["a", "b"]]
        assert ws.update_cells_chamado is None

    def test_so_chama_update_quando_ha_atualizacoes(self):
        ws = _FakeWorksheet()
        ip.aplicar_no_google_sheets_import(ws, [], [(2, 3, "valor")])
        assert ws.append_rows_chamado is None
        assert len(ws.update_cells_chamado) == 1
        celula = ws.update_cells_chamado[0]
        assert (celula.row, celula.col, celula.value) == (2, 3, "valor")

    def test_nao_chama_nada_quando_vazio(self):
        ws = _FakeWorksheet()
        ip.aplicar_no_google_sheets_import(ws, [], [])
        assert ws.append_rows_chamado is None
        assert ws.update_cells_chamado is None


class TestProcessarUploadProtheus:
    def test_erro_de_conexao_retorna_ok_false(self, monkeypatch):
        def _falha():
            raise RuntimeError("sem credencial")
        monkeypatch.setattr(ip, "obter_client_gspread", _falha)
        ok, mensagem = ip.processar_upload_protheus(BytesIO(b"qualquer coisa"))
        assert ok is False
        assert "Erro ao conectar no Google Sheets" in mensagem

    def test_layout_nao_reconhecido(self, monkeypatch):
        monkeypatch.setattr(ip, "obter_client_gspread", lambda: (object(), {}))
        monkeypatch.setattr(ip, "FILE_ID", "id-fake")
        class _SpreadsheetFake:
            def open_by_key(self, *_a, **_k):
                return self
        client_fake = _SpreadsheetFake()
        monkeypatch.setattr(ip, "obter_client_gspread", lambda: (client_fake, {}))
        arquivo = _montar_xlsx(["Coluna A", "Coluna B"])
        ok, mensagem = ip.processar_upload_protheus(arquivo)
        assert ok is False
        assert "não reconhecido" in mensagem
