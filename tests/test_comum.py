"""Testes dos formatadores/parsers compartilhados em comum.py (usados pelo
painel principal e pelo Painel do Comprador)."""

from datetime import date

import pandas as pd
import pytest

import comum


class TestConverterParaNumerico:
    @pytest.mark.parametrize("valor,esperado", [
        ("R$ 1.234,56", 1234.56),
        ("1234,56", 1234.56),
        ("1234.56", 1234.56),
        ("", 0.0),
        (None, 0.0),
        ("nan", 0.0),
        ("abc", 0.0),
    ])
    def test_conversoes(self, valor, esperado):
        assert comum.converter_para_numerico(valor) == esperado


class TestFormatarMoedaBr:
    def test_formata_com_separador_de_milhar_e_virgula_decimal(self):
        assert comum.formatar_moeda_br(1234.5) == "R$ 1.234,50"

    def test_zero(self):
        assert comum.formatar_moeda_br("") == "R$ 0,00"


class TestValidarFormatoData:
    @pytest.mark.parametrize("txt", ["", "N/A", "n/a", "0", "05/09/2026"])
    def test_formatos_validos(self, txt):
        assert comum.validar_formato_data(txt) is True

    @pytest.mark.parametrize("txt", ["2026-09-05", "05-09-2026", "32/13/2026", "abc"])
    def test_formatos_invalidos(self, txt):
        assert comum.validar_formato_data(txt) is False


class TestFormatarParaDdMmAaaa:
    def test_string_br_mantida(self):
        # Caminho real de producao: o valor chega como string "DD/MM/AAAA"
        # (e assim que a base fica salva no Google Sheets) - sem ambiguidade.
        assert comum.formatar_para_dd_mm_aaaa("05/09/2026") == "05/09/2026"

    def test_bug_conhecido_timestamp_vira_string_iso_e_inverte_dia_mes(self):
        """Bug latente (nao corrigido aqui - fora do escopo desta tarefa de
        testes): a funcao faz str(valor) ANTES de reparsear, entao um
        pd.Timestamp real (ex: vindo direto de um pd.read_excel, sem passar
        pelo Google Sheets como string) vira "2026-09-05 00:00:00" e cai na
        mesma ambiguidade de dayfirst=True que fmt_data_import - trocando
        dia e mes sempre que os dois forem <=12. Hoje isso so nao aparece
        porque, no fluxo real, a data ja chega como string DD/MM/AAAA (lida
        de volta do Sheets) antes de passar por aqui - mas qualquer chamada
        futura com um valor de data "cru" (Timestamp/datetime) esbarra nisso."""
        assert comum.formatar_para_dd_mm_aaaa(pd.Timestamp("2026-09-05")) == "09/05/2026"

    def test_numero_serial_excel(self):
        # 45900 = serial do Excel (base 30/12/1899) - so garante que nao
        # quebra e devolve uma data plausivel no formato br.
        resultado = comum.formatar_para_dd_mm_aaaa("45900")
        assert resultado.count("/") == 2

    def test_vazio_mantem_vazio(self):
        assert comum.formatar_para_dd_mm_aaaa("") == ""

    def test_nao_data_mantem_original(self):
        assert comum.formatar_para_dd_mm_aaaa("texto qualquer") == "texto qualquer"


class TestParseDataBr:
    def test_data_valida(self):
        assert comum.parse_data_br("05/09/2026") == date(2026, 9, 5)

    @pytest.mark.parametrize("valor", ["", "N/A", "nan", "None", "2026-09-05"])
    def test_valores_invalidos_retornam_none(self, valor):
        assert comum.parse_data_br(valor) is None


class TestGerarBytesExcel:
    def test_gera_bytes_xlsx_validos(self):
        df = pd.DataFrame({"Pedido": ["100", "101"], "Fornecedor": ["A", "B"]})
        conteudo = comum.gerar_bytes_excel(df)
        assert isinstance(conteudo, (bytes, bytearray))
        assert len(conteudo) > 0
        # Um xlsx e um zip - assinatura PK no inicio do arquivo.
        assert conteudo[:2] == b"PK"
