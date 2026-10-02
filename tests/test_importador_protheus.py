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
    @pytest.mark.parametrize("texto_totvs, esperado", [
        ("Aprovado - Totalmente Entregue", "APROVADO"),
        ("Aprovado - Aguardando Entrega", "APROVADO"),
        ("Aprovado - Entregue Parcial", "APROVADO"),
        ("Bloqueado", "BLOQUEADO"),
        ("Estornado", "BLOQUEADO"),
        ("Rejeitado", "REJEITADO"),
        ("Pendente (Nível 01)", "PENDENTE DE APROVAÇÃO"),
        ("Pendente (Nível 02)", "PENDENTE DE APROVAÇÃO"),
        ("Pendente (Nível 03)", "PENDENTE DE APROVAÇÃO"),
        ("Pendente (Nível 1)", "PENDENTE DE APROVAÇÃO"),
        ("Pendente (Nível 3)", "PENDENTE DE APROVAÇÃO"),
        ("Liberado Direto", "ERRO"),
    ])
    def test_tabela_nova_do_mata121(self, texto_totvs, esperado):
        # Tabela "PLANILHA DE ATUALIZAÇÃO = NOVO STATUS NO PORTAL SGC"
        # (decisão do usuário, 2026-10-02) - com Dt Lib. PC preenchida pra não
        # cair na barreira de "Aprovado sem data".
        linha = {"Status Aprov": texto_totvs, "Dt Lib. PC": pd.Timestamp("2026-09-05")}
        assert ip.valor_status_origem_import(linha) == esperado

    def test_valor_desconhecido_passa_cru_em_caixa_alta(self):
        assert ip.valor_status_origem_import({"Status Aprov": "Algo Novo"}) == "ALGO NOVO"

    def test_pendente_vira_texto_completo(self):
        linha = {"Status Aprov": "Pendente"}
        assert ip.valor_status_origem_import(linha) == "PENDENTE DE APROVAÇÃO".upper()

    def test_sem_controle_aprovacao_vira_aprovado(self):
        linha = {"Status Aprov": "Não possui controle de Aprovação", "Dt Lib. PC": pd.Timestamp("2026-09-05")}
        assert ip.valor_status_origem_import(linha) == "APROVADO"

    def test_em_aprovacao_vira_texto_completo_pendente(self):
        # "Em aprovação" e "Pendente" são grafias diferentes do Totvs pro
        # mesmo estado - as duas têm que virar o MESMO texto canônico
        # (decisão do usuário 2026-09-28: nunca ter "EM APROVAÇÃO" e
        # "PENDENTE DE APROVAÇÃO" coexistindo como status distintos na base).
        linha = {"Status Aprov": "Em aprovação"}
        assert ip.valor_status_origem_import(linha) == "PENDENTE DE APROVAÇÃO".upper()

    def test_aprovado_vira_texto_completo_quando_tem_data_liberacao(self):
        linha = {"Status Aprov": "Aprovado", "Dt Lib. PC": pd.Timestamp("2026-09-05")}
        assert ip.valor_status_origem_import(linha) == "APROVADO"

    def test_aprovado_sem_data_liberacao_vira_pendente(self):
        """Caso real (30/09/2026): varios pedidos (180774/180825/180826/
        180831/180832/180833/180841/180857 e outros) confirmados pelo
        usuario como "ainda não foram aprovados" mesmo o Totvs mandando
        "Status Aprov" = Aprovado - sem "Dt Lib. PC" preenchida, a aprovação
        não foi de fato confirmada/finalizada no sistema deles. Decisão
        explícita do usuário: pedido sem data de aprovação nunca pode virar
        "Aprovado" na nossa base, mesmo que o texto diga isso."""
        linha = {"Status Aprov": "Aprovado", "Dt Lib. PC": ""}
        assert ip.valor_status_origem_import(linha) == "PENDENTE DE APROVAÇÃO".upper()

    def test_aprovado_sem_chave_dt_lib_pc_tambem_vira_pendente(self):
        linha = {"Status Aprov": "Aprovado"}
        assert ip.valor_status_origem_import(linha) == "PENDENTE DE APROVAÇÃO".upper()


class TestStatusDaLegenda:
    # Decisão explícita do usuário, 2026-09-29: coluna "Legenda" do
    # relatório de Solicitações do Totvs -> STATUS canônico da aba
    # Solicitacoes. Grafias exatas pedidas pelo usuário (ex.: "REJEITADA",
    # não "REJEITADO" - esse é outro status, de outro pipeline).
    @pytest.mark.parametrize("legenda,esperado", [
        ("Solicitacao bloqueada", "BLOQUEADA"),
        ("Solicitação em processo de cotação", "EM COTAÇÃO"),
        ("Solicitacao parcialmente atendida", "PARCIALMENTE ATENDIDA"),
        ("Solicitacao Pendente", "PENDENTE"),
        ("Solicitacao rejeitada", "REJEITADA"),
        ("Solicitacao totalmente atendida", "ATENDIDA"),
    ])
    def test_mapeia_cada_legenda_conhecida(self, legenda, esperado):
        assert ip.status_da_legenda_import({"Legenda": legenda}) == esperado

    def test_legenda_vazia_nao_mexe(self):
        assert ip.status_da_legenda_import({"Legenda": ""}) == ""

    def test_legenda_desconhecida_nao_mexe(self):
        assert ip.status_da_legenda_import({"Legenda": "Uma legenda nova que o Totvs inventou"}) == ""

    def test_gatilho_protege_status_manuais_de_outro_pipeline(self):
        # REJEITADO/CONTRATO/REVISAR são lançados a mão por
        # atualizar_pendencias_abertas.py / Portal do Comprador - um import
        # comum de Solicitações nunca pode sobrescrever esses.
        for manual in ("REJEITADO", "CONTRATO", "REVISAR"):
            assert ip.normalizar_status_import(manual) not in ip.GATILHO_STATUS_SOLICITACOES_IMPORT

    def test_gatilho_inclui_todos_os_proprios_valores_e_branco(self):
        assert ip.normalizar_status_import("") in ip.GATILHO_STATUS_SOLICITACOES_IMPORT
        for valor in ip.MAPA_LEGENDA_STATUS_IMPORT.values():
            assert ip.normalizar_status_import(valor) in ip.GATILHO_STATUS_SOLICITACOES_IMPORT


CABECALHO_DESTINO_SC = ["SOLICITAÇÃO", "ITEM SC", "PRODUTO", "STATUS", "LEGENDA"]


class TestImportSolicitacoesAtualizaStatusPelaLegenda:
    """Integração ponta a ponta: processar_linhas_import com os parâmetros
    reais usados por processar_arquivo_sc_import (MAPA_SOLICITACOES_IMPORT,
    CAMPOS_MANUAIS_SOLICITACOES_IMPORT, status_da_legenda_import,
    GATILHO_STATUS_SOLICITACOES_IMPORT) - garante que o import comum de
    Solicitações já grava o STATUS certo sozinho, sem precisar de ajuste
    manual depois (pedido do usuário, 2026-09-29)."""

    def _indice_existente(self, row_num=5, **valores_atuais):
        chave = (valores_atuais.get("SOLICITAÇÃO", ""), valores_atuais.get("ITEM SC", ""))
        base = {c: "" for c in CABECALHO_DESTINO_SC}
        base.update(valores_atuais)
        return {chave: {"row_num": row_num, "valores": base}}

    def _rodar(self, df, indice):
        return ip.processar_linhas_import(
            df, ip.MAPA_SOLICITACOES_IMPORT, CABECALHO_DESTINO_SC, {},
            ip.CAMPOS_MANUAIS_SOLICITACOES_IMPORT, ip.CHAVE_SOLICITACOES_IMPORT,
            indice_existentes=indice,
            campo_status="STATUS", calcular_status=ip.status_da_legenda_import,
            gatilho_status=ip.GATILHO_STATUS_SOLICITACOES_IMPORT,
            campos_sempre_sobrescreve=ip.CAMPOS_SEMPRE_SOBRESCREVE_SOLICITACOES_IMPORT,
        )

    def test_solicitacao_nova_ja_nasce_com_status_da_legenda(self):
        df = _df_origem([{
            "Numero da SC": 141500, "Item da SC": 1, "Produto": "5",
            "Legenda": "Solicitacao totalmente atendida",
        }])
        novas, atualizacoes, dup, atualizadas, chaves = self._rodar(df, indice={})
        assert len(novas) == 1
        col_status = CABECALHO_DESTINO_SC.index("STATUS")
        assert novas[0][col_status] == "ATENDIDA"

    def test_solicitacao_existente_pendente_atualiza_para_atendida(self):
        indice = self._indice_existente(SOLICITAÇÃO="141500", **{"ITEM SC": "1"}, STATUS="PENDENTE")
        df = _df_origem([{
            "Numero da SC": 141500, "Item da SC": 1, "Produto": "5",
            "Legenda": "Solicitacao totalmente atendida",
        }])
        novas, atualizacoes, dup, atualizadas, chaves = self._rodar(df, indice)
        col_status = CABECALHO_DESTINO_SC.index("STATUS") + 1
        assert (5, col_status, "ATENDIDA") in atualizacoes

    def test_status_manual_rejeitado_nao_e_sobrescrito(self):
        # REJEITADO foi lançado a mão por outro pipeline (não é o "REJEITADA"
        # que essa importação gera) - tem que ficar intocado, mesmo que
        # outros campos em branco (ex.: PRODUTO) sejam preenchidos.
        indice = self._indice_existente(SOLICITAÇÃO="141500", **{"ITEM SC": "1"}, STATUS="REJEITADO")
        df = _df_origem([{
            "Numero da SC": 141500, "Item da SC": 1, "Produto": "5",
            "Legenda": "Solicitacao totalmente atendida",
        }])
        novas, atualizacoes, dup, atualizadas, chaves = self._rodar(df, indice)
        col_status = CABECALHO_DESTINO_SC.index("STATUS") + 1
        assert not any(col == col_status for _, col, _ in atualizacoes)

    def test_status_manual_contrato_nao_e_sobrescrito(self):
        indice = self._indice_existente(SOLICITAÇÃO="141500", **{"ITEM SC": "1"}, STATUS="CONTRATO")
        df = _df_origem([{
            "Numero da SC": 141500, "Item da SC": 1, "Produto": "5",
            "Legenda": "Solicitacao Pendente",
        }])
        novas, atualizacoes, dup, atualizadas, chaves = self._rodar(df, indice)
        col_status = CABECALHO_DESTINO_SC.index("STATUS") + 1
        assert not any(col == col_status for _, col, _ in atualizacoes)

    def test_status_desconhecido_mantem_bruto_em_maiusculo(self):
        linha = {"Status Aprov": "Liberado"}
        assert ip.valor_status_origem_import(linha) == "LIBERADO"

    def test_legenda_nova_solicitacao_ja_grava_o_texto_bruto(self):
        df = _df_origem([{
            "Numero da SC": 141500, "Item da SC": 1, "Produto": "5",
            "Legenda": "Solicitacao totalmente atendida",
        }])
        novas, atualizacoes, dup, atualizadas, chaves = self._rodar(df, indice={})
        col_legenda = CABECALHO_DESTINO_SC.index("LEGENDA")
        assert novas[0][col_legenda] == "Solicitacao totalmente atendida"

    def test_legenda_sempre_sobrescreve_mesmo_ja_tendo_valor(self):
        # Ao contrario do STATUS (derivado, protegido), LEGENDA e' so um
        # espelho do Totvs - decisao explicita do usuario, 2026-09-30:
        # atualiza sempre com a ultima versao do arquivo, sem excecao.
        indice = self._indice_existente(
            SOLICITAÇÃO="141500", **{"ITEM SC": "1"},
            STATUS="ATENDIDA", LEGENDA="Solicitacao totalmente atendida",
        )
        df = _df_origem([{
            "Numero da SC": 141500, "Item da SC": 1, "Produto": "5",
            "Legenda": "Solicitacao em processo de cotacao",
        }])
        novas, atualizacoes, dup, atualizadas, chaves = self._rodar(df, indice)
        col_legenda = CABECALHO_DESTINO_SC.index("LEGENDA") + 1
        assert (5, col_legenda, "Solicitacao em processo de cotacao") in atualizacoes

    def test_legenda_nao_muda_quando_arquivo_traz_o_mesmo_texto(self):
        indice = self._indice_existente(
            SOLICITAÇÃO="141500", **{"ITEM SC": "1"},
            STATUS="ATENDIDA", LEGENDA="Solicitacao totalmente atendida",
        )
        df = _df_origem([{
            "Numero da SC": 141500, "Item da SC": 1, "Produto": "5",
            "Legenda": "Solicitacao totalmente atendida",
        }])
        novas, atualizacoes, dup, atualizadas, chaves = self._rodar(df, indice)
        col_legenda = CABECALHO_DESTINO_SC.index("LEGENDA") + 1
        assert not any(col == col_legenda for _, col, _ in atualizacoes)


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


class TestNormalizarColunasDescricaoPc:
    # Caso real, 2026-10-01: Pedidos 180691/180698/180713/180714 vieram com
    # CONDIÇÃO PAGAMENTO = Descricao do item, e DESCRICAO em branco - o
    # arquivo do Totvs so tinha UMA coluna "Descricao" (a coluna "Condição
    # Pagamento" tinha sido tirada do browse, ver conversa 2026-09-28), mas
    # o mapa (MAPA_PEDIDOS_IMPORT) sempre esperou DUAS ("Descricao" =
    # condicao, "Descricao.1" = item real).

    def test_uma_so_descricao_vira_descricao_1_e_descricao_fica_em_branco(self):
        df = pd.DataFrame({"Produto": ["0001"], "Descricao": ["BOTINA SEGUR ELETRICISTA"]})
        resultado = ip.normalizar_colunas_descricao_pc_import(df)
        assert resultado["Descricao"].tolist() == [""]
        assert resultado["Descricao.1"].tolist() == ["BOTINA SEGUR ELETRICISTA"]

    def test_duas_descricoes_nao_mexe_em_nada(self):
        df = pd.DataFrame({
            "Produto": ["0001"],
            "Descricao": ["30 DIAS D"],
            "Descricao.1": ["BOTINA SEGUR ELETRICISTA"],
        })
        resultado = ip.normalizar_colunas_descricao_pc_import(df)
        assert resultado["Descricao"].tolist() == ["30 DIAS D"]
        assert resultado["Descricao.1"].tolist() == ["BOTINA SEGUR ELETRICISTA"]

    def test_sem_nenhuma_descricao_nao_quebra(self):
        df = pd.DataFrame({"Produto": ["0001"]})
        resultado = ip.normalizar_colunas_descricao_pc_import(df)
        assert "Descricao" not in resultado.columns
        assert "Descricao.1" not in resultado.columns


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
            campos_sempre_sobrescreve=("ENTREGA",),
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
            campo_status="STATUS", campos_sempre_sobrescreve=("ENTREGA",),
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
# detectar_pedidos_duplicados_import
# ---------------------------------------------------------------------------

class TestDetectarPedidosDuplicados:
    CABECALHO = ["PEDIDO", "PRODUTO", "STATUS", "FORNECEDOR"]

    def test_sem_duplicata_devolve_lista_vazia(self):
        ws = _FakeWorksheetComDados([
            self.CABECALHO,
            ["180291", "0000003149", "APROVADO", "FAYAMO"],
            ["180291", "0000003695", "APROVADO", "FAYAMO"],
        ])
        assert ip.detectar_pedidos_duplicados_import(ws) == []

    def test_detecta_mesma_chave_pedido_produto_em_duas_linhas(self):
        ws = _FakeWorksheetComDados([
            self.CABECALHO,
            ["180291", "0000003149", "APROVADO", "FAYAMO"],
            ["180299", "0000000352", "APROVADO", "AUTOTRAC"],
            ["180291", "0000003149", "ENVIADO AO FINANCEIRO", "FAYAMO"],
        ])
        duplicados = ip.detectar_pedidos_duplicados_import(ws)
        assert len(duplicados) == 1
        d = duplicados[0]
        assert d["pedido"] == "180291"
        assert d["produto"] == "0000003149"
        assert d["linhas"] == [2, 4]
        assert d["fornecedor"] == "FAYAMO"
        assert d["status"] == "APROVADO"  # reporta o status da primeira ocorrência

    def test_normaliza_produto_sem_zero_a_esquerda_pra_comparar(self):
        # Caso real: uma linha com PRODUTO já formatado ("0000003149") e outra
        # com o zero à esquerda perdido ("3149", ex.: célula virou número no
        # Sheets) ainda contam como a MESMA chave duplicada.
        ws = _FakeWorksheetComDados([
            self.CABECALHO,
            ["180291", "0000003149", "APROVADO", "FAYAMO"],
            ["180291", "3149", "ENVIADO AO FINANCEIRO", "FAYAMO"],
        ])
        duplicados = ip.detectar_pedidos_duplicados_import(ws)
        assert len(duplicados) == 1
        assert duplicados[0]["linhas"] == [2, 3]

    def test_tres_copias_da_mesma_chave_conta_como_um_grupo_com_tres_linhas(self):
        ws = _FakeWorksheetComDados([
            self.CABECALHO,
            ["180291", "0000003149", "APROVADO", "FAYAMO"],
            ["180291", "0000003149", "APROVADO", "FAYAMO"],
            ["180291", "0000003149", "ENVIADO AO FINANCEIRO", "FAYAMO"],
        ])
        duplicados = ip.detectar_pedidos_duplicados_import(ws)
        assert len(duplicados) == 1
        assert duplicados[0]["linhas"] == [2, 3, 4]

    def test_planilha_vazia_devolve_lista_vazia(self):
        ws = _FakeWorksheetComDados([])
        assert ip.detectar_pedidos_duplicados_import(ws) == []

    def test_linha_sem_pedido_ou_produto_e_ignorada(self):
        ws = _FakeWorksheetComDados([
            self.CABECALHO,
            ["", "0000003149", "APROVADO", "FAYAMO"],
            ["180291", "", "APROVADO", "FAYAMO"],
        ])
        assert ip.detectar_pedidos_duplicados_import(ws) == []


class TestDetectarPedidosDuplicadosComSolicitacaoEQtd:
    # Caso real, 2026-09-30: mesmo Pedido+Produto pode legitimamente
    # consolidar Solicitações diferentes (cada uma com sua própria QTD) - não
    # é cópia acidental, e não deve entrar no relatório de duplicados.
    CABECALHO = ["PEDIDO", "PRODUTO", "STATUS", "FORNECEDOR", "SOLICITAÇÃO", "QTD"]

    def test_mesma_solicitacao_e_qtd_ainda_e_reportada(self):
        ws = _FakeWorksheetComDados([
            self.CABECALHO,
            ["180291", "0000003149", "APROVADO", "FAYAMO", "141535", "30"],
            ["180291", "0000003149", "APROVADO", "FAYAMO", "141535", "30"],
        ])
        duplicados = ip.detectar_pedidos_duplicados_import(ws)
        assert len(duplicados) == 1
        assert duplicados[0]["linhas"] == [2, 3]

    def test_solicitacao_diferente_nao_e_reportada(self):
        ws = _FakeWorksheetComDados([
            self.CABECALHO,
            ["175435", "0000003588", "ATENDIDO", "LUANJO", "139644", "8"],
            ["175435", "0000003588", "ATENDIDO", "LUANJO", "139501", "1"],
        ])
        assert ip.detectar_pedidos_duplicados_import(ws) == []

    def test_qtd_diferente_mesma_solicitacao_nao_e_reportada(self):
        ws = _FakeWorksheetComDados([
            self.CABECALHO,
            ["179727", "0000008055", "ATENDIDO", "REI DAS MANGUEIRAS", "141228", "21"],
            ["179727", "0000008055", "ATENDIDO", "REI DAS MANGUEIRAS", "141228", "40"],
        ])
        assert ip.detectar_pedidos_duplicados_import(ws) == []

    def test_grupo_de_tres_com_uma_solicitacao_diferente_nao_e_reportado(self):
        ws = _FakeWorksheetComDados([
            self.CABECALHO,
            ["180291", "0000003149", "APROVADO", "FAYAMO", "141535", "30"],
            ["180291", "0000003149", "APROVADO", "FAYAMO", "141535", "30"],
            ["180291", "0000003149", "APROVADO", "FAYAMO", "999999", "30"],
        ])
        assert ip.detectar_pedidos_duplicados_import(ws) == []


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


class _FakeWorksheetComDados:
    def __init__(self, dados):
        self._dados = dados
        self.update_cells_chamado = None

    def get_all_values(self):
        return self._dados

    def update_cells(self, celulas, value_input_option="RAW"):
        self.update_cells_chamado = celulas


class _FakeSpreadsheetComAbas:
    def __init__(self, abas: dict):
        self._abas = abas

    def worksheet(self, nome):
        return self._abas[nome]


class TestSincronizarStatusCompraDireta:
    CABECALHO_SOL = ["SOLICITAÇÃO", "ITEM SC", "PEDIDO", "STATUS", "CRITICIDADE"]
    CABECALHO_PED = ["STATUS", "SOLICITAÇÃO", "PEDIDO", "FORNECEDOR"]

    def _montar(self, linhas_sol, linhas_ped):
        ws_sol = _FakeWorksheetComDados([self.CABECALHO_SOL, *linhas_sol])
        ws_ped = _FakeWorksheetComDados([self.CABECALHO_PED, *linhas_ped])
        sheet = _FakeSpreadsheetComAbas({"Solicitacoes": ws_sol, "Pedidos": ws_ped})
        return sheet, ws_sol, ws_ped

    def test_marca_compra_direta_sobrescrevendo_status_existente(self):
        sheet, ws_sol, ws_ped = self._montar(
            linhas_sol=[["140380", "1", "177074", "", "COMPRA DIRETA"]],
            linhas_ped=[["ATENDIDO", "140380", "177074", "FORNECEDOR X"]],
        )
        total = ip.sincronizar_status_compra_direta_import(sheet)
        assert total == 1
        celulas = ws_ped.update_cells_chamado
        assert len(celulas) == 1
        assert (celulas[0].row, celulas[0].col, celulas[0].value) == (2, 1, "COMPRA DIRETA")

    def test_ja_marcado_nao_gera_atualizacao(self):
        sheet, ws_sol, ws_ped = self._montar(
            linhas_sol=[["140380", "1", "177074", "", "COMPRA DIRETA"]],
            linhas_ped=[["COMPRA DIRETA", "140380", "177074", "FORNECEDOR X"]],
        )
        total = ip.sincronizar_status_compra_direta_import(sheet)
        assert total == 0
        assert ws_ped.update_cells_chamado is None

    def test_pedido_sem_solicitacao_compra_direta_nao_muda(self):
        sheet, ws_sol, ws_ped = self._montar(
            linhas_sol=[["140380", "1", "177074", "", "URGENTE"]],
            linhas_ped=[["ATENDIDO", "140380", "177074", "FORNECEDOR X"]],
        )
        total = ip.sincronizar_status_compra_direta_import(sheet)
        assert total == 0
        assert ws_ped.update_cells_chamado is None

    def test_casa_solicitacao_com_zfill_diferente(self):
        # aba Solicitacoes as vezes tem o numero sem zero a esquerda / com
        # sufixo .0 vindo do Excel - tem que casar mesmo assim.
        sheet, ws_sol, ws_ped = self._montar(
            linhas_sol=[["140380.0", "1", "177074", "", "COMPRA DIRETA"]],
            linhas_ped=[["ATENDIDO", "140380", "177074", "FORNECEDOR X"]],
        )
        total = ip.sincronizar_status_compra_direta_import(sheet)
        assert total == 1

    def test_aceita_criticidade_no_plural_compras_direta(self):
        # Caso real, 2026-09-30: SC 141457/PC 179785 - a fonte que alimenta
        # CRITICIDADE as vezes grava no plural ("COMPRAS DIRETA"), e a
        # sincronizacao tem que casar mesmo assim (o valor gravado em
        # Pedidos.STATUS continua singular, so a leitura aceita as duas).
        sheet, ws_sol, ws_ped = self._montar(
            linhas_sol=[["141457", "1", "179785", "", "COMPRAS DIRETA"]],
            linhas_ped=[["APROVADO", "141457", "179785", "MR COMERCIO"]],
        )
        total = ip.sincronizar_status_compra_direta_import(sheet)
        assert total == 1
        celulas = ws_ped.update_cells_chamado
        assert (celulas[0].row, celulas[0].col, celulas[0].value) == (2, 1, "COMPRA DIRETA")


class TestForcarPedidoGeradoQuandoSemStatus:
    CABECALHO_SOL = ["SOLICITAÇÃO", "ITEM SC", "PEDIDO", "STATUS"]

    def _montar(self, linhas_sol):
        ws_sol = _FakeWorksheetComDados([self.CABECALHO_SOL, *linhas_sol])
        sheet = _FakeSpreadsheetComAbas({"Solicitacoes": ws_sol})
        return sheet, ws_sol

    def test_marca_pedido_gerado_quando_status_em_branco_e_pedido_preenchido(self):
        sheet, ws_sol = self._montar([["140380", "1", "177074", ""]])
        total = ip.forcar_pedido_gerado_quando_sem_status_import(sheet)
        assert total == 1
        celulas = ws_sol.update_cells_chamado
        assert len(celulas) == 1
        assert (celulas[0].row, celulas[0].col, celulas[0].value) == (2, 4, "PEDIDO GERADO")

    def test_nao_mexe_quando_pedido_tambem_esta_em_branco(self):
        sheet, ws_sol = self._montar([["140380", "1", "", ""]])
        total = ip.forcar_pedido_gerado_quando_sem_status_import(sheet)
        assert total == 0
        assert ws_sol.update_cells_chamado is None

    def test_nao_sobrescreve_status_ja_existente(self):
        sheet, ws_sol = self._montar([["140380", "1", "177074", "ATENDIDA"]])
        total = ip.forcar_pedido_gerado_quando_sem_status_import(sheet)
        assert total == 0
        assert ws_sol.update_cells_chamado is None


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


# ---------------------------------------------------------------------------
# Cenario de negocio real: reimportar um Pedido que ANTES estava com datas em
# branco (aprovacao/entrega pendentes) e o arquivo novo do Totvs ja traz essas
# datas preenchidas - a celula vazia deve ser preenchida E o Status deve ser
# recalculado de acordo. Usa o MAPA_PEDIDOS_IMPORT real (nao um mapa
# simplificado), pra validar o comportamento de ponta a ponta como ele
# realmente roda em processar_arquivo_pc_import.
# ---------------------------------------------------------------------------

CABECALHO_REAL_PEDIDOS = [
    "SOLICITAÇÃO", "PEDIDO", "CONDIÇÃO PAGAMENTO", "PAGAMENTO", "DATA PEDIDO",
    "DATA LIBERAÇÃO", "PREVISÃO DE ENTREGA", "ENTREGA", "FORNECEDOR", "GRUPO",
    "CENTRO DE CUSTO", "PRODUTO", "DESCRICAO", "UM", "QTD", "QTD ENTREGUE",
    "PREÇO UNITÁRIO", "VALOR TOTAL", "STATUS", "ENVIO", "LOGISTICA",
]


def _linha_origem_pedido(**overrides):
    base = {
        "Numero da SC": "3419", "Numero": 100, "Descricao": "A VISTA",
        "Data Emissao": pd.Timestamp("2026-09-01"), "Dt Lib. PC": "",
        "Dt. Entrega": "", "Dt. Dig.Nota": "", "Nome Fornece": "Fornecedor X",
        "Grupo": "G1", "Centro Custo": "1200", "Produto": 5,
        "Descricao.1": "Parafuso", "Unidade": "UN", "Quantidade": 10,
        "Prc Unitario": 2.5, "Vlr.Total": 25.0, "Status Aprov": "Pendente",
    }
    base.update(overrides)
    return pd.DataFrame([base])


def _indice_pedido_existente(row_num=8, **valores_atuais):
    base = {c: "" for c in CABECALHO_REAL_PEDIDOS}
    base.update(valores_atuais)
    chave = (base["PEDIDO"], base["PRODUTO"])
    return {chave: {"row_num": row_num, "valores": base}}


def _rodar_import_pedidos(df_origem, indice_existentes):
    return ip.processar_linhas_import(
        df_origem, ip.MAPA_PEDIDOS_IMPORT, CABECALHO_REAL_PEDIDOS,
        ip.ALIASES_PEDIDOS_IMPORT, ip.CAMPOS_MANUAIS_PEDIDOS_IMPORT,
        ip.CHAVE_PEDIDOS_IMPORT, indice_existentes,
        campo_status="STATUS", calcular_status=ip.valor_status_origem_import,
        gatilho_status=ip.STATUS_GATILHO_SUBSTITUICAO_IMPORT,
        campos_obrigatorios=("SOLICITAÇÃO",),
        campos_sempre_sobrescreve=ip.CAMPOS_SEMPRE_SOBRESCREVE_PEDIDOS_IMPORT,
    )


class TestReimportacaoPreenchendoCelulasVazias:
    """Reproduz o pedido do usuario: reimportar um arquivo mais recente do
    Totvs deve preencher campos de data que antes estavam em branco E
    atualizar o Status de acordo - sem sobrescrever o que ja tinha valor."""

    def test_data_liberacao_preenche_e_status_vira_aprovado(self):
        """Pedido estava 'Em Aprovação', sem Data Liberação (nosso campo mais
        proximo de 'data de aprovacao' na aba Pedidos). O arquivo novo traz
        a Data Liberação preenchida e Status Aprov='Aprovado' - a celula
        vazia deve ser preenchida e o Status deve mudar pra 'APROVADO'."""
        indice = _indice_pedido_existente(
            PEDIDO="100", PRODUTO="0000000005", SOLICITAÇÃO="003419",
            **{"DATA PEDIDO": "01/09/2026", "DATA LIBERAÇÃO": "", "STATUS": "Em Aprovação"},
        )
        df = _linha_origem_pedido(**{"Dt Lib. PC": pd.Timestamp("2026-09-05"), "Status Aprov": "Aprovado"})
        novas, atualizacoes, dup, atualizadas, _ = _rodar_import_pedidos(df, indice)

        assert novas == []
        assert atualizadas == 1
        col_liberacao = CABECALHO_REAL_PEDIDOS.index("DATA LIBERAÇÃO") + 1
        col_status = CABECALHO_REAL_PEDIDOS.index("STATUS") + 1
        assert (8, col_liberacao, "05/09/2026") in atualizacoes
        assert (8, col_status, "APROVADO") in atualizacoes

    def test_entrega_preenche_e_forca_status_atendido(self):
        """Pedido ja aprovado, com Previsão De Entrega definida, mas sem
        Entrega ainda. Arquivo novo traz a Entrega (Dt. Dig.Nota) - deve
        preencher a celula vazia e forcar Status = ATENDIDO, sem tocar na
        Previsão De Entrega que ja tinha valor."""
        indice = _indice_pedido_existente(
            PEDIDO="200", PRODUTO="0000000007", SOLICITAÇÃO="003420",
            **{"PREVISÃO DE ENTREGA": "10/09/2026", "ENTREGA": "", "STATUS": "Aprovado"},
        )
        df = _linha_origem_pedido(
            Numero=200, Produto=7,
            **{"Dt. Entrega": pd.Timestamp("2026-09-30"),  # ignorado - campo ja preenchido
               "Dt. Dig.Nota": pd.Timestamp("2026-09-12"), "Status Aprov": "Não possui controle de Aprovação"},
        )
        novas, atualizacoes, dup, atualizadas, _ = _rodar_import_pedidos(df, indice)

        col_entrega = CABECALHO_REAL_PEDIDOS.index("ENTREGA") + 1
        col_previsao = CABECALHO_REAL_PEDIDOS.index("PREVISÃO DE ENTREGA") + 1
        col_status = CABECALHO_REAL_PEDIDOS.index("STATUS") + 1
        assert (8, col_entrega, "12/09/2026") in atualizacoes
        assert not any(c == col_previsao for _, c, _ in atualizacoes), (
            "Previsão De Entrega ja tinha valor - nao deveria ser sobrescrita"
        )
        assert (8, col_status, ip.STATUS_ATENDIDO_IMPORT) in atualizacoes

    def test_aprovacao_e_entrega_no_mesmo_ciclo_gera_duas_atualizacoes_de_status(self):
        """Caso raro mas possivel: o Pedido pula direto de 'Em Aprovação'
        pra entregue num unico ciclo de importacao (ex: reimportacao depois
        de varios dias). O motor enfileira DUAS atualizacoes pra STATUS na
        mesma celula (APROVADO, depois ATENDIDO) - documentando esse
        comportamento aqui. O valor que realmente fica gravado no Google
        Sheets depende da ordem em que aplicar_no_google_sheets_import monta
        o lote (ultima entrada da lista vence - ver teste abaixo que prova
        isso via gspread de verdade)."""
        indice = _indice_pedido_existente(
            PEDIDO="300", PRODUTO="0000000009", SOLICITAÇÃO="003421",
            **{"DATA LIBERAÇÃO": "", "ENTREGA": "", "STATUS": "Em Aprovação"},
        )
        df = _linha_origem_pedido(
            Numero=300, Produto=9,
            **{"Dt Lib. PC": pd.Timestamp("2026-09-05"),
               "Dt. Dig.Nota": pd.Timestamp("2026-09-12"),
               "Status Aprov": "Aprovado"},
        )
        novas, atualizacoes, dup, atualizadas, _ = _rodar_import_pedidos(df, indice)

        col_status = CABECALHO_REAL_PEDIDOS.index("STATUS") + 1
        status_queued = [valor for row, col, valor in atualizacoes if col == col_status]
        assert status_queued == ["APROVADO", ip.STATUS_ATENDIDO_IMPORT], (
            "Duas atualizacoes de Status ficam enfileiradas pra mesma celula "
            "quando aprovacao e entrega chegam juntas - ver proximo teste "
            "pra ver qual valor realmente e gravado no Sheets."
        )

    def test_valor_final_gravado_quando_ha_duas_atualizacoes_na_mesma_celula(self):
        """Prova, usando o proprio gspread (nao uma suposicao), qual valor
        fica de pe quando duas atualizacoes de Status colidem na mesma
        celula na mesma chamada: a API do Sheets recebe um retangulo de
        valores (values_update) montado por gspread.utils.cell_list_to_rect,
        que usa um dict por (linha,coluna) - a ULTIMA Cell da lista pra
        aquela posicao vence. Como o codigo sempre acrescenta a atualizacao
        de ATENDIDO depois da de APROVADO (ver processar_linhas_import), o
        resultado final e ATENDIDO - o que, nesse caso, e o status
        semanticamente correto (o pedido foi entregue)."""
        import gspread.utils as gspread_utils

        indice = _indice_pedido_existente(
            PEDIDO="300", PRODUTO="0000000009", SOLICITAÇÃO="003421",
            **{"DATA LIBERAÇÃO": "", "ENTREGA": "", "STATUS": "Em Aprovação"},
        )
        df = _linha_origem_pedido(
            Numero=300, Produto=9,
            **{"Dt Lib. PC": pd.Timestamp("2026-09-05"),
               "Dt. Dig.Nota": pd.Timestamp("2026-09-12"),
               "Status Aprov": "Aprovado"},
        )
        _, atualizacoes, _, _, _ = _rodar_import_pedidos(df, indice)

        celulas = [ip.gspread.Cell(row, col, valor) for row, col, valor in atualizacoes]
        retangulo = gspread_utils.cell_list_to_rect(celulas)

        col_status = CABECALHO_REAL_PEDIDOS.index("STATUS") + 1
        row_offset = min(c.row for c in celulas)
        col_offset = min(c.col for c in celulas)
        valor_final_status = retangulo[8 - row_offset][col_status - col_offset]
        assert valor_final_status == ip.STATUS_ATENDIDO_IMPORT


# ---------------------------------------------------------------------------
# Correcao de Descricao via Solicitacoes: o relatorio "Listagem do Browse" de
# Pedidos do proprio Totvs as vezes repete a Descricao do primeiro item
# quando varias Solicitacoes diferentes sao consolidadas num mesmo Pedido
# (visto ao vivo no PEDIDO 180032 - 7 itens bem diferentes, todos com a
# Descricao do primeiro). A aba Solicitacoes vem de outro relatorio do Totvs
# que nao tem esse problema, entao serve de fonte confiavel pra corrigir.
# ---------------------------------------------------------------------------

class TestCorrecaoDescricaoViaSolicitacoes:
    def test_usa_descricao_da_solicitacao_quando_existe_correcao(self):
        correcao = {("003419", "0000000005"): "Descricao correta da SC"}
        df = _linha_origem_pedido()
        novas, _, _, _, _ = ip.processar_linhas_import(
            df, ip.MAPA_PEDIDOS_IMPORT, CABECALHO_REAL_PEDIDOS,
            ip.ALIASES_PEDIDOS_IMPORT, ip.CAMPOS_MANUAIS_PEDIDOS_IMPORT,
            ip.CHAVE_PEDIDOS_IMPORT, indice_existentes={},
            campo_status="STATUS", calcular_status=ip.valor_status_origem_import,
            gatilho_status=ip.STATUS_GATILHO_SUBSTITUICAO_IMPORT,
            campos_obrigatorios=("SOLICITAÇÃO",),
            campos_sempre_sobrescreve=ip.CAMPOS_SEMPRE_SOBRESCREVE_PEDIDOS_IMPORT,
            correcao_descricao=correcao,
        )
        assert len(novas) == 1
        assert novas[0][CABECALHO_REAL_PEDIDOS.index("DESCRICAO")] == "Descricao correta da SC"

    def test_mantem_descricao_do_arquivo_quando_nao_ha_correcao(self):
        df = _linha_origem_pedido()
        novas, _, _, _, _ = ip.processar_linhas_import(
            df, ip.MAPA_PEDIDOS_IMPORT, CABECALHO_REAL_PEDIDOS,
            ip.ALIASES_PEDIDOS_IMPORT, ip.CAMPOS_MANUAIS_PEDIDOS_IMPORT,
            ip.CHAVE_PEDIDOS_IMPORT, indice_existentes={},
            campo_status="STATUS", calcular_status=ip.valor_status_origem_import,
            gatilho_status=ip.STATUS_GATILHO_SUBSTITUICAO_IMPORT,
            campos_obrigatorios=("SOLICITAÇÃO",),
            campos_sempre_sobrescreve=ip.CAMPOS_SEMPRE_SOBRESCREVE_PEDIDOS_IMPORT,
            correcao_descricao={("999999", "9999999999"): "Nao deveria ser usada"},
        )
        assert len(novas) == 1
        assert novas[0][CABECALHO_REAL_PEDIDOS.index("DESCRICAO")] == "Parafuso"

    def test_sem_correcao_descricao_comportamento_igual_a_antes(self):
        """Passar correcao_descricao=None (default) nao muda nada - mesmo
        resultado de sempre, usando so a Descricao do arquivo."""
        df = _linha_origem_pedido()
        novas, _, _, _, _ = _rodar_import_pedidos(df, indice_existentes={})
        assert novas[0][CABECALHO_REAL_PEDIDOS.index("DESCRICAO")] == "Parafuso"


class TestEnvioProtegeStatusDeRecalculoNaImportacao:
    """Caso real (30/09/2026): 12 pedidos (ex.: 179937) ja tinham ENVIO
    preenchido pelo Agente Pedidos Pagamento (e-mail de verdade ja enviado),
    mas uma reimportacao do Totvs recalculou o STATUS de volta pra "APROVADO"
    - ENVIO preenchido e' prova de que o pedido ja foi tratado, entao a
    importacao nunca deve recalcular o STATUS por cima disso, mesmo que o
    STATUS atual bata com o gatilho de substituicao (ex.: um branco
    reintroduzido por engano)."""

    def test_envio_preenchido_bloqueia_recalculo_mesmo_com_status_no_gatilho(self):
        indice = _indice_pedido_existente(
            PEDIDO="100", PRODUTO="0000000005", SOLICITAÇÃO="003419",
            **{"STATUS": "", "ENVIO": "08/09/2026"},  # STATUS em branco bate no gatilho
        )
        df = _linha_origem_pedido(**{"Status Aprov": "Aprovado"})
        novas, atualizacoes, dup, atualizadas, _ = _rodar_import_pedidos(df, indice)

        col_status = CABECALHO_REAL_PEDIDOS.index("STATUS") + 1
        assert not any(c == col_status for _, c, _ in atualizacoes), (
            "ENVIO ja preenchido - o STATUS nao deveria ser recalculado pela importacao"
        )

    def test_aprovado_reverte_pra_pendente_quando_totvs_reporta_isso(self):
        """Caso real (30/09/2026): 24 pedidos ficaram presos como "APROVADO"
        pra sempre porque esse status nao era gatilho de recalculo - mesmo
        depois do Totvs reverter de verdade pra "Em Aprovacao". Sem ENVIO
        preenchido (pedido ainda nao foi tratado pelo agente), o STATUS
        precisa poder regredir tambem, nao so avancar."""
        indice = _indice_pedido_existente(
            PEDIDO="102", PRODUTO="0000000008", SOLICITAÇÃO="003419",
            **{"STATUS": "APROVADO", "ENVIO": ""},
        )
        df = _linha_origem_pedido(Numero=102, Produto=8, **{"Status Aprov": "Em aprovação"})
        novas, atualizacoes, dup, atualizadas, _ = _rodar_import_pedidos(df, indice)

        col_status = CABECALHO_REAL_PEDIDOS.index("STATUS") + 1
        assert (8, col_status, ip.TEXTO_PENDENTE_APROVACAO_IMPORT.upper()) in atualizacoes

    def test_aprovado_com_envio_preenchido_nao_regride(self):
        """Mesmo cenario do teste acima, mas o pedido JA tem ENVIO preenchido
        (agente ja tratou) - a barreira do ENVIO tem que segurar mesmo com
        "Aprovado" agora sendo gatilho."""
        indice = _indice_pedido_existente(
            PEDIDO="103", PRODUTO="0000000009", SOLICITAÇÃO="003419",
            **{"STATUS": "APROVADO", "ENVIO": "08/09/2026"},
        )
        df = _linha_origem_pedido(Numero=103, Produto=9, **{"Status Aprov": "Em aprovação"})
        novas, atualizacoes, dup, atualizadas, _ = _rodar_import_pedidos(df, indice)

        col_status = CABECALHO_REAL_PEDIDOS.index("STATUS") + 1
        assert not any(c == col_status for _, c, _ in atualizacoes)

    def test_envio_vazio_nao_bloqueia_recalculo_normal(self):
        """Confirma que a barreira nova so age quando ENVIO tem valor - sem
        ENVIO, o recalculo normal de STATUS continua acontecendo (mesmo
        comportamento de antes, ja coberto pelos outros testes desta classe)."""
        indice = _indice_pedido_existente(
            PEDIDO="101", PRODUTO="0000000006", SOLICITAÇÃO="003419",
            **{"STATUS": "", "ENVIO": ""},
        )
        df = _linha_origem_pedido(Numero=101, Produto=6, **{"Status Aprov": "Aprovado", "Dt Lib. PC": pd.Timestamp("2026-09-05")})
        novas, atualizacoes, dup, atualizadas, _ = _rodar_import_pedidos(df, indice)

        col_status = CABECALHO_REAL_PEDIDOS.index("STATUS") + 1
        assert (8, col_status, "APROVADO") in atualizacoes


class TestCarregarDescricoesSolicitacoes:
    """Testes do lookup (SOLICITAÇÃO, PRODUTO) -> DESCRICAO montado a partir
    da aba Solicitacoes, com um worksheet/spreadsheet fake (sem gspread real)."""

    def _spreadsheet_fake(self, linhas, cabecalho=None):
        cabecalho = cabecalho or ["SOLICITAÇÃO", "ITEM SC", "PEDIDO", "PRODUTO", "DESCRICAO"]

        class _WorksheetFake:
            def get_all_values(self):
                return [cabecalho] + linhas

        class _SpreadsheetFake:
            def worksheet(self, nome):
                if nome != ip.ABA_SOLICITACOES_IMPORT:
                    raise ip.gspread.WorksheetNotFound(nome)
                return _WorksheetFake()

        return _SpreadsheetFake()

    def test_monta_lookup_normalizando_chaves(self):
        sh = self._spreadsheet_fake([
            ["3419", "1", "100", "5", "Descricao correta"],
        ])
        lookup = ip.carregar_descricoes_solicitacoes_import(sh)
        assert lookup == {("003419", "0000000005"): "Descricao correta"}

    def test_aba_solicitacoes_inexistente_devolve_vazio(self):
        class _SpreadsheetSemAba:
            def worksheet(self, nome):
                raise ip.gspread.WorksheetNotFound(nome)
        assert ip.carregar_descricoes_solicitacoes_import(_SpreadsheetSemAba()) == {}

    def test_linha_sem_descricao_e_ignorada(self):
        sh = self._spreadsheet_fake([
            ["3419", "1", "100", "5", ""],
        ])
        assert ip.carregar_descricoes_solicitacoes_import(sh) == {}
