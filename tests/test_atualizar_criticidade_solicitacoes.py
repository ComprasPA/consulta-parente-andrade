import pandas as pd
import pytest

import atualizar_criticidade_solicitacoes as acs


# --- carregar_arquivo ---------------------------------------------------------

def _escrever_xls(tmp_path, linhas):
    caminho = tmp_path / "Cotações - teste.xlsx"
    pd.DataFrame(linhas).to_excel(caminho, index=False)
    return caminho


def test_carregar_arquivo_formata_solicitacao_com_6_digitos(tmp_path):
    caminho = _escrever_xls(tmp_path, [
        {"Número Protheus": 141762.0, "Número Solicitação": "SCM119046", "Criticidade": "Emergencial"},
    ])
    df = acs.carregar_arquivo(caminho)
    assert df.iloc[0]["Solicitacao"] == "141762"
    assert df.iloc[0]["Criticidade"] == "EMERGENCIAL"


def test_carregar_arquivo_mantem_codscm_quando_protheus_vazio(tmp_path):
    caminho = _escrever_xls(tmp_path, [
        {"Número Protheus": None, "Número Solicitação": "SCM119067", "Criticidade": "Rotineira"},
    ])
    df = acs.carregar_arquivo(caminho)
    assert df.iloc[0]["Solicitacao"] == ""
    assert df.iloc[0]["CodScmScm"] == "SCM119067"
    assert df.iloc[0]["Criticidade"] == "ROTINEIRA"


def test_carregar_arquivo_descarta_linha_sem_criticidade(tmp_path):
    caminho = _escrever_xls(tmp_path, [
        {"Número Protheus": 141762.0, "Número Solicitação": "SCM119046", "Criticidade": ""},
    ])
    df = acs.carregar_arquivo(caminho)
    assert df.empty


# --- aplicar_criticidade -------------------------------------------------------

class _FakeWorksheet:
    def __init__(self, dados):
        self._dados = dados
        self.update_cells_chamado = None

    def get_all_values(self):
        return self._dados

    def update_cells(self, celulas, value_input_option="RAW"):
        self.update_cells_chamado = celulas


class _FakeSpreadsheet:
    def __init__(self, ws):
        self._ws = ws

    def worksheet(self, nome):
        return self._ws


CABECALHO = ["SOLICITAÇÃO", "ITEM SC", "CRITICIDADE", "COD SC SCM"]


def test_aplica_mesma_criticidade_em_todos_itens_da_solicitacao():
    ws = _FakeWorksheet([
        CABECALHO,
        ["141762", "1", "", "SCM119046"],
        ["141762", "2", "ROTINEIRA", "SCM119046"],
        ["999999", "1", "ROTINEIRA", "SCM000001"],
    ])
    sheet = _FakeSpreadsheet(ws)
    df = pd.DataFrame([{"Solicitacao": "141762", "CodScmScm": "SCM119046", "Criticidade": "EMERGENCIAL"}])

    atualizadas, nao_encontradas = acs.aplicar_criticidade(sheet, df)

    assert atualizadas == 2
    assert nao_encontradas == 0
    celulas = {(c.row, c.col): c.value for c in ws.update_cells_chamado}
    assert celulas[(2, 3)] == "EMERGENCIAL"
    assert celulas[(3, 3)] == "EMERGENCIAL"
    assert (4, 3) not in celulas


def test_nao_regrava_quando_ja_tem_o_mesmo_valor():
    ws = _FakeWorksheet([
        CABECALHO,
        ["141762", "1", "EMERGENCIAL", "SCM119046"],
    ])
    sheet = _FakeSpreadsheet(ws)
    df = pd.DataFrame([{"Solicitacao": "141762", "CodScmScm": "SCM119046", "Criticidade": "EMERGENCIAL"}])

    atualizadas, nao_encontradas = acs.aplicar_criticidade(sheet, df)

    assert atualizadas == 0
    assert ws.update_cells_chamado is None


def test_usa_cod_sc_scm_como_fallback_quando_sem_numero_protheus():
    ws = _FakeWorksheet([
        CABECALHO,
        ["140935", "1", "", "SCM119067"],
    ])
    sheet = _FakeSpreadsheet(ws)
    df = pd.DataFrame([{"Solicitacao": "", "CodScmScm": "SCM119067", "Criticidade": "ROTINEIRA"}])

    atualizadas, nao_encontradas = acs.aplicar_criticidade(sheet, df)

    assert atualizadas == 1
    assert nao_encontradas == 0
    celula = ws.update_cells_chamado[0]
    assert (celula.row, celula.col, celula.value) == (2, 3, "ROTINEIRA")


def test_solicitacao_do_arquivo_nao_encontrada_na_base():
    ws = _FakeWorksheet([
        CABECALHO,
        ["140935", "1", "ROTINEIRA", "SCM119067"],
    ])
    sheet = _FakeSpreadsheet(ws)
    df = pd.DataFrame([{"Solicitacao": "999999", "CodScmScm": "", "Criticidade": "EMERGENCIAL"}])

    atualizadas, nao_encontradas = acs.aplicar_criticidade(sheet, df)

    assert atualizadas == 0
    assert nao_encontradas == 1
