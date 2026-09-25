"""Logica do importador Protheus (upload de Pedidos/Solicitacoes exportados
do TOTVS Webapp direto pro Google Sheets). Extraido de main.py pra ficar
livre de dependencia do Streamlit - permite rodar testes automatizados e,
futuramente, um script standalone (agente local) sem precisar de
`streamlit run`.

Mesmas regras de sempre: dedup por chave; ENTREGA e QTD ENTREGUE (data e
quantidade da entrega) prevalecem o que vier no arquivo (mesmo que ja tenha
valor - o arquivo mais recente do Totvs e a fonte de verdade); os demais
campos so preenchem em branco (nunca sobrescrevem o que ja tem valor);
status so muda quando esta "em espera" (branco/Em aprovacao/Pendente) -
EXCETO que ENTREGA ganhar uma data (nesta importacao) sempre forca o
Status pra "ATENDIDO", decisao explicita do usuario, sem excecao mesmo pra
status como EXCLUÍDO DO TOTVS. QTD ENTREGUE e' apenas importado/gravado -
nao influencia o Status."""

import re
import unicodedata
from datetime import datetime

import gspread
import pandas as pd

from comum import FILE_ID, obter_client_gspread, parse_data_br

# Pedido marcado assim (ver detectar_pedidos_excluidos_import) sumiu do
# relatorio do Totvs - a linha fica na planilha (base = fonte de verdade),
# mas nao deve aparecer nem ser considerada em nenhum painel/calculo/consulta
# (decisao explicita do usuario). Filtrado logo na leitura, o mais cedo
# possivel, pra nenhum calculo/filtro/exportacao rio abaixo enxergar essa linha.
STATUS_EXCLUIDO_TOTVS = "EXCLUÍDO DO TOTVS"

ABA_PEDIDOS_IMPORT = "Pedidos"
ABA_SOLICITACOES_IMPORT = "Solicitacoes"
COLUNAS_ASSINATURA_PC = "Dt. Dig.Nota"
COLUNAS_ASSINATURA_SC = "Cod SC. SCM"

MAPA_PEDIDOS_IMPORT = {
    "SOLICITAÇÃO":        {"origem": "Numero da SC",   "tipo": "solicitacao"},
    "PEDIDO":             {"origem": "Numero",          "tipo": "inteiro"},
    "CONDIÇÃO PAGAMENTO": {"origem": "Descricao",       "tipo": "texto"},
    "PAGAMENTO":          {"origem": "Descricao",       "tipo": "pagamento_calc"},
    "DATA PEDIDO":        {"origem": "Data Emissao",    "tipo": "data"},
    "DATA LIBERAÇÃO":     {"origem": "Dt Lib. PC",      "tipo": "data"},
    "PREVISÃO DE ENTREGA":{"origem": "Dt. Entrega",     "tipo": "data"},
    "ENTREGA":            {"origem": "Dt. Dig.Nota",    "tipo": "data"},
    # NF REMESSA fica de fora de proposito - o operador insere manualmente,
    # a importação nunca deve preencher/sobrescrever esse campo.
    "FORNECEDOR":         {"origem": "Nome Fornece",    "tipo": "texto"},
    "GRUPO":              {"origem": "Grupo",           "tipo": "texto"},
    "CENTRO DE CUSTO":    {"origem": "Centro Custo",    "tipo": "centro_custo"},
    "PRODUTO":            {"origem": "Produto",         "tipo": "produto"},
    "DESCRICAO":          {"origem": "Descricao.1",     "tipo": "texto"},
    "UM":                 {"origem": "Unidade",         "tipo": "texto"},
    "QTD":                {"origem": "Quantidade",      "tipo": "numero"},
    # Quantidade ja entregue desse item, segundo o proprio Totvs (cumulativa -
    # cresce a cada nota fiscal digitada contra o mesmo Pedido/Produto).
    # Junto com ENTREGA, e' o outro campo que sempre prevalece o que vier no
    # arquivo (ver processar_arquivo_pc_import).
    "QTD ENTREGUE":       {"origem": "Qtd.Entregue",    "tipo": "numero"},
    "PREÇO UNITÁRIO":     {"origem": "Prc Unitario",    "tipo": "decimal"},
    "VALOR TOTAL":        {"origem": "Vlr.Total",       "tipo": "decimal"},
}
ALIASES_PEDIDOS_IMPORT = {
    "SOLICITAÇÃO": ["SOLICITAÇÃO", "SOLICITACAO"],
    "DATA LIBERAÇÃO": ["DATA LIBERAÇÃO", "DATA LIBERACAO"],
    "PREÇO UNITÁRIO": ["PREÇO UNITÁRIO", "PRECO UNITARIO"],
    "QTD ENTREGUE": ["QTD ENTREGUE", "QUANTIDADE ENTREGUE", "QTD. ENTREGUE"],
}
CAMPOS_MANUAIS_PEDIDOS_IMPORT = ["STATUS", "ENVIO", "LOGISTICA"]
CHAVE_PEDIDOS_IMPORT = ("PEDIDO", "PRODUTO")
# Campos onde o arquivo do Totvs sempre prevalece (mesmo que a celula ja
# tenha um valor diferente) - o restante dos campos so preenche em branco.
CAMPOS_SEMPRE_SOBRESCREVE_PEDIDOS_IMPORT = ("ENTREGA", "QTD ENTREGUE")

CABECALHO_SOLICITACOES_IMPORT = [
    "SOLICITAÇÃO", "ITEM SC", "COTAÇÃO", "PEDIDO", "PRODUTO", "DESCRICAO",
    "QTD", "UM", "CENTRO DE CUSTO", "DESC CENTRO DE CUSTO",
    "DATA EMISSAO", "DATA APROVACAO", "FILIAL", "QTD EM PEDIDO",
]
MAPA_SOLICITACOES_IMPORT = {
    "SOLICITAÇÃO":          {"origem": "Numero da SC", "tipo": "solicitacao"},
    "ITEM SC":              {"origem": "Item da SC",   "tipo": "texto"},
    "COTAÇÃO":              {"origem": "Num. Cotacao", "tipo": "texto"},
    "PEDIDO":               {"origem": "Num. Pedido",  "tipo": "inteiro"},
    "PRODUTO":              {"origem": "Produto",      "tipo": "produto"},
    "DESCRICAO":            {"origem": "Descricao",    "tipo": "texto"},
    "QTD":                  {"origem": "Quantidade",   "tipo": "numero"},
    "UM":                   {"origem": "Unid Medida",  "tipo": "texto"},
    "CENTRO DE CUSTO":      {"origem": "C Custo",      "tipo": "centro_custo"},
    "DESC CENTRO DE CUSTO": {"origem": "Desc C.C.",    "tipo": "texto"},
    "DATA EMISSAO":         {"origem": "DT Emissao",   "tipo": "data"},
    "DATA APROVACAO":       {"origem": "Dt Aprovacao", "tipo": "data"},
    "FILIAL":               {"origem": "Filial",       "tipo": "texto"},
    "QTD EM PEDIDO":        {"origem": "Quant.em Ped", "tipo": "numero"},
}
CHAVE_SOLICITACOES_IMPORT = ("SOLICITAÇÃO", "ITEM SC")


def normalizar_nome_import(nome) -> str:
    return str(nome).upper().strip().replace("Í", "I").replace("Ã", "A")


def normalizar_status_import(texto) -> str:
    texto = str(texto or "").strip().upper()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c))


def limpar_numero_texto_import(valor) -> str:
    txt = str(valor).strip()
    if txt.lower() in ("nan", "none", "nat", ""):
        return ""
    return re.sub(r"\.0$", "", txt)


def valor_e_zero_ou_vazio_import(valor) -> bool:
    txt = str(valor or "").strip()
    return txt == "" or txt.lstrip("0") == ""


def fmt_inteiro_import(valor) -> str:
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    try:
        return str(int(float(valor)))
    except (ValueError, TypeError):
        return limpar_numero_texto_import(valor)


def fmt_texto_import(valor) -> str:
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def fmt_produto_import(valor) -> str:
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    return limpar_numero_texto_import(valor).strip().zfill(10)


def fmt_solicitacao_import(valor) -> str:
    """Numero da Solicitação sempre tem 6 digitos - algumas filiais usam
    numeração baixa com zeros à esquerda (ex: 003419), que um tipo 'inteiro'
    normal perderia ao converter pra int."""
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    return limpar_numero_texto_import(valor).strip().zfill(6)


def fmt_centro_custo_import(valor) -> str:
    """Centro de Custo tem 4 digitos - o Excel as vezes exporta a coluna
    como numero (float), o que vira "1223.0" num tipo 'texto' comum. So
    limpa o ".0" (sem zfill - nao converte pra int, pra nao arriscar
    derrubar um eventual zero a esquerda de verdade)."""
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    return limpar_numero_texto_import(valor).strip()


def fmt_numero_import(valor) -> str:
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    try:
        num = float(valor)
        return str(int(num)) if num.is_integer() else str(num)
    except (ValueError, TypeError):
        return limpar_numero_texto_import(valor)


def fmt_decimal_import(valor) -> str:
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    try:
        return f"{float(valor):.2f}"
    except (ValueError, TypeError):
        return limpar_numero_texto_import(valor)


def fmt_data_import(valor) -> str:
    if pd.isna(valor) or str(valor).strip() == "":
        return ""
    dt = pd.to_datetime(valor, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return ""
    return dt.strftime("%d/%m/%Y")


CONDICOES_PAGAMENTO_SEM_MARCADOR_IMPORT = {
    "A VISTA", "ENT +1PARC", "ENT+3PARC", "ENTR + 1 PARC", "PAGO", "VENCIDO",
}


def fmt_pagamento_calc_import(valor) -> str:
    condicao = fmt_texto_import(valor).upper()
    if condicao == "":
        return ""
    if condicao in CONDICOES_PAGAMENTO_SEM_MARCADOR_IMPORT:
        return ""
    return "------"


FORMATADORES_IMPORT = {
    "inteiro": fmt_inteiro_import,
    "texto": fmt_texto_import,
    "produto": fmt_produto_import,
    "solicitacao": fmt_solicitacao_import,
    "centro_custo": fmt_centro_custo_import,
    "numero": fmt_numero_import,
    "decimal": fmt_decimal_import,
    "data": fmt_data_import,
    "pagamento_calc": fmt_pagamento_calc_import,
}

TEXTO_PENDENTE_APROVACAO_IMPORT = "Pendente de Aprovação"

STATUS_GATILHO_SUBSTITUICAO_IMPORT = {
    normalizar_status_import(""),
    normalizar_status_import("Em aprovação"),
    normalizar_status_import("Pendente"),
    normalizar_status_import(TEXTO_PENDENTE_APROVACAO_IMPORT),
    # Pedido que reaparece num import (a chave bateu = ele existe no arquivo
    # de agora) nunca deve continuar preso em EXCLUÍDO DO TOTVS - isso só
    # acontece quando o arquivo anterior que gerou a exclusão era parcial/
    # filtrado (ex.: relatorio diario mais estreito que o Browse completo do
    # Totvs) e o pedido nunca tinha realmente sumido de lá.
    normalizar_status_import(STATUS_EXCLUIDO_TOTVS),
}

MAPA_STATUS_APROV_TEXTO_IMPORT = {
    normalizar_status_import("Pendente"): TEXTO_PENDENTE_APROVACAO_IMPORT,
    normalizar_status_import("Não possui controle de Aprovação"): "Aprovado",
}

# Pedido some do relatorio mais recente do Totvs = provavelmente foi excluido
# la, mas a importacao nunca remove linha da base - sem isso o pedido ficaria
# preso pra sempre com o status antigo, parecendo ainda em aberto.
STATUS_EXCLUIDO_TOTVS_IMPORT = STATUS_EXCLUIDO_TOTVS
DIAS_JANELA_EXCLUSAO_TOTVS_IMPORT = 30
# ENTREGA ganhando data (na importacao) sempre forca esse status - decisao
# explicita do usuario, sem excecao mesmo pra status como EXCLUÍDO DO TOTVS.
STATUS_ATENDIDO_IMPORT = "ATENDIDO"
# Quando ha Entrega mas a Qtd Entregue ainda e' menor que a Qtd pedida -
# decisao explicita do usuario, 2026-09-25: com Entrega preenchida, o status
# e' ATENDIDO se Qtd Entregue == Qtd, ou ENTREGA PARCIAL se Qtd Entregue <
# Qtd (nunca o contrario - Entrega sempre implica pelo menos parcial).
STATUS_ENTREGA_PARCIAL_IMPORT = "ENTREGA PARCIAL"
STATUS_TERMINAIS_SEM_REALERTA_IMPORT = {
    normalizar_status_import(STATUS_EXCLUIDO_TOTVS_IMPORT),
    normalizar_status_import("Cancelado"),
    normalizar_status_import("Cancelado Pelo Solicitante"),
    normalizar_status_import("Rejeitado Pelo Aprovador"),
    normalizar_status_import("Rejeitado"),
}

# A Criticidade "COMPRA DIRETA" mora na aba Solicitacoes (coluna CRITICIDADE,
# alimentada por fora - aba Criticidade_Solicitacoes/formula, nao pelo
# importador). Decisao explicita do usuario: quando a Solicitacao de um
# Pedido tem essa criticidade, o STATUS do Pedido deve espelhar "COMPRA
# DIRETA" na aba Pedidos - sempre prevalece, mesmo sobre um status ja
# preenchido (ex.: ATENDIDO, ou os que o agente_pedidos_pagamento grava:
# ENVIADO AO FINANCEIRO/ENVIADO AO FORNECEDOR).
CRITICIDADE_COMPRA_DIRETA_IMPORT = "COMPRA DIRETA"
STATUS_COMPRA_DIRETA_IMPORT = "COMPRA DIRETA"


def valor_status_origem_import(linha_origem) -> str:
    bruto = fmt_texto_import(linha_origem.get("Status Aprov", ""))
    valor = MAPA_STATUS_APROV_TEXTO_IMPORT.get(normalizar_status_import(bruto), bruto)
    return valor.upper()


def _para_float_status_import(valor_str):
    """Converte um valor de QTD/QTD ENTREGUE (ja como string) pra float, ou
    None se vazio/nao numerico - usado so pra decidir entre ATENDIDO e
    ENTREGA PARCIAL, nunca pra gravar de volta na planilha."""
    txt = str(valor_str).strip().replace(",", ".")
    if not txt:
        return None
    try:
        return float(txt)
    except ValueError:
        return None


def status_por_entrega_import(qtd_str, qtd_entregue_str) -> str:
    """Decide entre ATENDIDO e ENTREGA PARCIAL comparando Qtd pedida com Qtd
    entregue (ambas strings já como estão na planilha/arquivo). Se não der
    pra comparar (falta uma das duas, ou não é número), assume ATENDIDO -
    mesmo comportamento de antes dessa distinção existir."""
    qtd = _para_float_status_import(qtd_str)
    qtd_entregue = _para_float_status_import(qtd_entregue_str)
    if qtd is not None and qtd_entregue is not None and qtd_entregue < qtd:
        return STATUS_ENTREGA_PARCIAL_IMPORT
    return STATUS_ATENDIDO_IMPORT


def construir_lookup_campo_import(campos: list, aliases: dict) -> dict:
    lookup = {}
    for campo in campos:
        for alt in [campo] + aliases.get(campo, []):
            lookup[normalizar_nome_import(alt)] = campo
    return lookup


def resolver_coluna_real_import(cabecalho_real: list, campo: str, aliases: dict):
    normalizado = {normalizar_nome_import(c): c for c in cabecalho_real}
    for alt in [campo] + aliases.get(campo, []):
        achado = normalizado.get(normalizar_nome_import(alt))
        if achado:
            return achado
    return None


def carregar_indice_existentes_import(worksheet, campos_chave, aliases):
    valores = worksheet.get_all_values()
    if not valores:
        return {}, []
    cabecalho_real = valores[0]
    indices = {}
    for campo in campos_chave:
        col_real = resolver_coluna_real_import(cabecalho_real, campo, aliases)
        if not col_real:
            return {}, cabecalho_real
        indices[campo] = cabecalho_real.index(col_real)

    n_cols = len(cabecalho_real)
    indice = {}
    for i, linha in enumerate(valores[1:], start=2):
        linha_pad = linha + [""] * (n_cols - len(linha))
        partes = []
        for campo in campos_chave:
            valor = linha_pad[indices[campo]]
            valor_limpo = limpar_numero_texto_import(valor)
            if campo == "PRODUTO" and valor.strip():
                valor_limpo = valor_limpo.zfill(10)
            elif campo == "SOLICITAÇÃO" and valor.strip():
                valor_limpo = valor_limpo.zfill(6)
            partes.append(valor_limpo)
        chave = tuple(partes)
        if not all(chave):
            continue
        indice[chave] = {"row_num": i, "valores": dict(zip(cabecalho_real, linha_pad))}
    return indice, cabecalho_real


def detectar_tipo_arquivo_import(arquivo):
    arquivo.seek(0)
    try:
        amostra = pd.read_excel(arquivo, header=1, nrows=1)
    except Exception:
        return None
    finally:
        arquivo.seek(0)
    colunas = set(amostra.columns.astype(str))
    if COLUNAS_ASSINATURA_PC in colunas:
        return "PC"
    if COLUNAS_ASSINATURA_SC in colunas:
        return "SC"
    return None


def processar_linhas_import(df_origem, mapa, cabecalho_destino, aliases, campos_manuais,
                             campos_chave, indice_existentes, campo_status=None,
                             calcular_status=None, gatilho_status=None, campos_obrigatorios=(),
                             campos_sempre_sobrescreve=(), correcao_descricao=None,
                             mapa_pedidos_por_produto=None):
    lookup_campo = construir_lookup_campo_import(list(mapa.keys()) + campos_manuais, aliases)
    col_status = resolver_coluna_real_import(cabecalho_destino, campo_status, {}) if campo_status else None

    novas_linhas = []
    atualizacoes = []
    chaves_deste_arquivo = set()
    duplicadas = 0
    linhas_atualizadas = 0

    for _, linha_origem in df_origem.iterrows():
        valores_por_campo = {
            campo_tela: FORMATADORES_IMPORT[config["tipo"]](linha_origem.get(config["origem"], ""))
            for campo_tela, config in mapa.items()
        }

        if mapa_pedidos_por_produto and not valores_por_campo.get("PEDIDO", ""):
            # O relatorio de Solicitacoes do Totvs nem sempre traz o Num.
            # Pedido preenchido mesmo quando o Pedido ja foi gerado (visto ao
            # vivo: SC 140965/140963, Pedido ja ATENDIDO na aba Pedidos, e a
            # propria Solicitacao nunca recebeu essa referencia de volta no
            # Totvs) - usa a aba Pedidos (cruzando por Solicitação+Produto,
            # fonte mais confiavel) como fallback so quando o arquivo nao
            # trouxe nada.
            pedido_fallback = mapa_pedidos_por_produto.get(
                (valores_por_campo.get("SOLICITAÇÃO", ""), valores_por_campo.get("PRODUTO", ""))
            )
            if pedido_fallback:
                valores_por_campo["PEDIDO"] = pedido_fallback

        if correcao_descricao and "DESCRICAO" in valores_por_campo:
            # O relatorio "Listagem do Browse" de Pedidos do proprio Totvs as
            # vezes repete a Descricao do primeiro item quando varias
            # Solicitacoes diferentes sao consolidadas num mesmo Pedido -
            # visto ao vivo no PEDIDO 180032 (7 itens bem diferentes, todos
            # com a Descricao do primeiro). A aba Solicitacoes vem de um
            # relatorio Totvs diferente que nao tem esse problema, entao e'
            # a fonte mais confiavel pra Descricao quando disponivel.
            descricao_correta = correcao_descricao.get(
                (valores_por_campo.get("SOLICITAÇÃO", ""), valores_por_campo.get("PRODUTO", ""))
            )
            if descricao_correta:
                valores_por_campo["DESCRICAO"] = descricao_correta

        if any(valor_e_zero_ou_vazio_import(valores_por_campo.get(c, "")) for c in campos_obrigatorios):
            duplicadas += 1
            continue

        chave = tuple(valores_por_campo.get(c, "") for c in campos_chave)
        if not all(chave) or chave in chaves_deste_arquivo:
            duplicadas += 1
            continue

        if chave in indice_existentes:
            chaves_deste_arquivo.add(chave)
            info = indice_existentes[chave]
            valores_atuais = info["valores"]
            alterou = False
            entrega_definida_agora = False

            for campo_tela, config_campo in mapa.items():
                col_real = resolver_coluna_real_import(cabecalho_destino, campo_tela, aliases)
                if not col_real:
                    continue
                valor_atual = valores_atuais.get(col_real, "").strip()
                novo_valor = valores_por_campo.get(campo_tela, "")
                if campo_tela in campos_sempre_sobrescreve:
                    # Campos onde o arquivo do Totvs sempre prevalece, mesmo
                    # se ja tiver um valor diferente - nao sao mais editaveis
                    # a mao (ver campos_permitidos_compras), entao nao ha
                    # risco de sobrescrever uma correcao manual do operador.
                    if novo_valor and novo_valor != valor_atual:
                        atualizacoes.append((info["row_num"], cabecalho_destino.index(col_real) + 1, novo_valor))
                        alterou = True
                        if campo_tela == "ENTREGA":
                            entrega_definida_agora = True
                else:
                    # Todo o resto (incl. os demais campos de data, como
                    # Previsão De Entrega, que o operador ainda edita a mao) so
                    # preenche quando esta em branco - nunca sobrescreve o que
                    # ja tem valor.
                    if valor_atual:
                        continue
                    if novo_valor:
                        atualizacoes.append((info["row_num"], cabecalho_destino.index(col_real) + 1, novo_valor))
                        alterou = True

            if col_status and calcular_status:
                atual_status = normalizar_status_import(valores_atuais.get(col_status, ""))
                if atual_status in gatilho_status:
                    novo_status = calcular_status(linha_origem)
                    if novo_status and normalizar_status_import(novo_status) != atual_status:
                        atualizacoes.append((info["row_num"], cabecalho_destino.index(col_status) + 1, novo_status))
                        alterou = True

            # ENTREGA ganhando data (nesta importacao) sempre forca esse
            # status - decisao explicita do usuario, sem excecao mesmo pra
            # status como EXCLUÍDO DO TOTVS. So reavalia quando ENTREGA
            # acabou de ser gravada NESTA importacao (nao a cada ciclo) -
            # senao um Status corrigido a mao pelo gestor seria desfeito no
            # proximo import so por causa de um ENTREGA antigo que nunca mudou.
            if col_status and entrega_definida_agora:
                atual_status_norm = normalizar_status_import(valores_atuais.get(col_status, ""))
                if atual_status_norm != normalizar_status_import(STATUS_ATENDIDO_IMPORT):
                    atualizacoes.append((info["row_num"], cabecalho_destino.index(col_status) + 1, STATUS_ATENDIDO_IMPORT))
                    alterou = True

            if alterou:
                linhas_atualizadas += 1
            else:
                duplicadas += 1
            continue

        chaves_deste_arquivo.add(chave)
        linha_final = [valores_por_campo.get(lookup_campo.get(normalizar_nome_import(c)), "") for c in cabecalho_destino]
        if col_status and calcular_status:
            novo_status = calcular_status(linha_origem)
            if novo_status:
                linha_final[cabecalho_destino.index(col_status)] = novo_status
        if col_status and valores_por_campo.get("ENTREGA", ""):
            linha_final[cabecalho_destino.index(col_status)] = STATUS_ATENDIDO_IMPORT
        novas_linhas.append(linha_final)

    return novas_linhas, atualizacoes, duplicadas, linhas_atualizadas, chaves_deste_arquivo


def detectar_pedidos_excluidos_import(indice_existentes, chaves_deste_arquivo, cabecalho_real):
    """Varre a base atual de Pedidos e marca como STATUS_EXCLUIDO_TOTVS_IMPORT
    quem: (1) tem Emissão Pc dentro da janela dos ultimos N dias, (2) ainda
    nao tem Entrega preenchida (senao sumir do relatorio de pedidos em aberto
    e esperado, nao indicio de exclusao), (3) o status atual nao e ja um
    status terminal, e (4) nao veio no arquivo importado agora."""
    col_status = resolver_coluna_real_import(cabecalho_real, "STATUS", {})
    col_data_pedido = resolver_coluna_real_import(cabecalho_real, "DATA PEDIDO", {})
    col_entrega = resolver_coluna_real_import(cabecalho_real, "ENTREGA", {})
    if not col_status or not col_data_pedido:
        return []

    hoje = datetime.now().date()
    atualizacoes = []
    for chave, info in indice_existentes.items():
        if chave in chaves_deste_arquivo:
            continue

        valores = info["valores"]
        if col_entrega and limpar_numero_texto_import(valores.get(col_entrega, "")).strip():
            continue

        status_atual = normalizar_status_import(valores.get(col_status, ""))
        if status_atual in STATUS_TERMINAIS_SEM_REALERTA_IMPORT:
            continue

        data_pedido = parse_data_br(valores.get(col_data_pedido, ""))
        if not data_pedido or (hoje - data_pedido).days > DIAS_JANELA_EXCLUSAO_TOTVS_IMPORT:
            continue

        atualizacoes.append((info["row_num"], cabecalho_real.index(col_status) + 1, STATUS_EXCLUIDO_TOTVS_IMPORT))
    return atualizacoes


def aplicar_no_google_sheets_import(worksheet, novas_linhas, atualizacoes):
    if novas_linhas:
        worksheet.append_rows(novas_linhas, value_input_option="RAW")
    if atualizacoes:
        celulas = [gspread.Cell(row, col, valor) for row, col, valor in atualizacoes]
        worksheet.update_cells(celulas, value_input_option="RAW")


def sincronizar_status_compra_direta_import(spreadsheet) -> int:
    """Espelha em STATUS (aba Pedidos) quando a Solicitação daquele Pedido
    tem CRITICIDADE = "COMPRA DIRETA" na aba Solicitacoes - decisão
    explícita do usuário: sempre prevalece, sobrescrevendo qualquer outro
    STATUS que a linha já tivesse - EXCETO quando o Pedido já tem ENTREGA
    preenchida (decisão explícita do usuário, 2026-09-24: "ATENDIDO impera
    sobre todos os outros status" - Entrega registrada significa NF
    classificada e entrega realizada, isso nunca pode ser desfeito por essa
    sincronização). Roda depois de qualquer import (PC ou SC) - a
    Criticidade fica em Solicitacoes mas o espelho é em Pedidos, e aqui
    sempre lê o estado atual das duas abas de novo (nunca confia em cache),
    já que o import mexeu numa delas. Devolve quantas linhas de Pedidos
    foram atualizadas."""
    ws_solicitacoes = spreadsheet.worksheet(ABA_SOLICITACOES_IMPORT)
    dados_sol = ws_solicitacoes.get_all_values()
    if not dados_sol:
        return 0
    cabecalho_sol = dados_sol[0]
    if "SOLICITAÇÃO" not in cabecalho_sol or "CRITICIDADE" not in cabecalho_sol:
        return 0
    idx_sc_sol = cabecalho_sol.index("SOLICITAÇÃO")
    idx_criticidade = cabecalho_sol.index("CRITICIDADE")

    scs_compra_direta = set()
    for linha in dados_sol[1:]:
        if idx_criticidade < len(linha) and linha[idx_criticidade].strip().upper() == CRITICIDADE_COMPRA_DIRETA_IMPORT:
            sc = limpar_numero_texto_import(linha[idx_sc_sol] if idx_sc_sol < len(linha) else "")
            if sc:
                scs_compra_direta.add(sc.zfill(6))
    if not scs_compra_direta:
        return 0

    ws_pedidos = spreadsheet.worksheet(ABA_PEDIDOS_IMPORT)
    dados_ped = ws_pedidos.get_all_values()
    if not dados_ped:
        return 0
    cabecalho_ped = dados_ped[0]
    col_sc_ped = resolver_coluna_real_import(cabecalho_ped, "SOLICITAÇÃO", ALIASES_PEDIDOS_IMPORT)
    if not col_sc_ped or "STATUS" not in cabecalho_ped:
        return 0
    idx_sc_ped = cabecalho_ped.index(col_sc_ped)
    idx_status_ped = cabecalho_ped.index("STATUS")
    col_entrega_ped = resolver_coluna_real_import(cabecalho_ped, "ENTREGA", {})
    idx_entrega_ped = cabecalho_ped.index(col_entrega_ped) if col_entrega_ped else None

    celulas = []
    for i, linha in enumerate(dados_ped[1:], start=2):
        sc_pedido = limpar_numero_texto_import(linha[idx_sc_ped] if idx_sc_ped < len(linha) else "")
        if sc_pedido and sc_pedido.zfill(6) in scs_compra_direta:
            if idx_entrega_ped is not None and idx_entrega_ped < len(linha) and linha[idx_entrega_ped].strip():
                continue  # ja atendido de verdade - Entrega nao pode ser desfeita
            status_atual = linha[idx_status_ped] if idx_status_ped < len(linha) else ""
            if status_atual.strip().upper() != STATUS_COMPRA_DIRETA_IMPORT:
                celulas.append(gspread.Cell(i, idx_status_ped + 1, STATUS_COMPRA_DIRETA_IMPORT))

    if celulas:
        ws_pedidos.update_cells(celulas, value_input_option="RAW")
    return len(celulas)


def forcar_atendido_quando_entrega_import(spreadsheet) -> int:
    """Varredura geral (decisão explícita do usuário, 2026-09-24/25): quando
    o Pedido tem ENTREGA preenchida (NF classificada), o status correto e'
    ATENDIDO se a Qtd Entregue já cobre a Qtd pedida, ou ENTREGA PARCIAL se
    ainda falta (ver status_por_entrega_import) - sempre prevalece sobre
    qualquer outro status que a linha tivesse (Compra Direta, Correção de
    Processo, Enviado ao Fornecedor, etc.). Roda periodicamente (ver
    agente_importador.py) como uma rede de segurança, cobrindo qualquer
    causa de divergência - não só a sincronização de Compra Direta.
    Devolve quantas linhas foram corrigidas."""
    ws_pedidos = spreadsheet.worksheet(ABA_PEDIDOS_IMPORT)
    dados_ped = ws_pedidos.get_all_values()
    if not dados_ped:
        return 0
    cabecalho_ped = dados_ped[0]
    col_entrega = resolver_coluna_real_import(cabecalho_ped, "ENTREGA", {})
    col_qtd = resolver_coluna_real_import(cabecalho_ped, "QTD", {})
    col_qtd_entregue = resolver_coluna_real_import(cabecalho_ped, "QTD ENTREGUE", ALIASES_PEDIDOS_IMPORT)
    if not col_entrega or "STATUS" not in cabecalho_ped:
        return 0
    idx_entrega = cabecalho_ped.index(col_entrega)
    idx_status = cabecalho_ped.index("STATUS")
    idx_qtd = cabecalho_ped.index(col_qtd) if col_qtd else None
    idx_qtd_entregue = cabecalho_ped.index(col_qtd_entregue) if col_qtd_entregue else None

    celulas = []
    for i, linha in enumerate(dados_ped[1:], start=2):
        if idx_entrega < len(linha) and linha[idx_entrega].strip():
            qtd_str = linha[idx_qtd] if idx_qtd is not None and idx_qtd < len(linha) else ""
            qtd_entregue_str = linha[idx_qtd_entregue] if idx_qtd_entregue is not None and idx_qtd_entregue < len(linha) else ""
            alvo = status_por_entrega_import(qtd_str, qtd_entregue_str)
            status_atual = linha[idx_status] if idx_status < len(linha) else ""
            if status_atual.strip().upper() != alvo:
                celulas.append(gspread.Cell(i, idx_status + 1, alvo))

    if celulas:
        ws_pedidos.update_cells(celulas, value_input_option="RAW")
    return len(celulas)


def carregar_descricoes_solicitacoes_import(spreadsheet):
    """Monta um lookup (SOLICITAÇÃO, PRODUTO) -> DESCRICAO a partir da aba
    Solicitacoes, usado pra corrigir a Descricao vinda do relatorio de
    Pedidos do Totvs quando ela vem errada (ver comentario em
    processar_linhas_import). Devolve {} se a aba nao existir/estiver vazia
    ou faltar alguma das 3 colunas - nesse caso o import de Pedidos
    simplesmente nao aplica nenhuma correcao."""
    try:
        worksheet = spreadsheet.worksheet(ABA_SOLICITACOES_IMPORT)
    except gspread.WorksheetNotFound:
        return {}

    valores = worksheet.get_all_values()
    if not valores:
        return {}
    cabecalho = valores[0]
    col_sol = resolver_coluna_real_import(cabecalho, "SOLICITAÇÃO", {"SOLICITAÇÃO": ["SOLICITAÇÃO", "SOLICITACAO"]})
    col_produto = resolver_coluna_real_import(cabecalho, "PRODUTO", {})
    col_desc = resolver_coluna_real_import(cabecalho, "DESCRICAO", {})
    if not col_sol or not col_produto or not col_desc:
        return {}
    idx_sol = cabecalho.index(col_sol)
    idx_produto = cabecalho.index(col_produto)
    idx_desc = cabecalho.index(col_desc)

    lookup = {}
    for linha in valores[1:]:
        if len(linha) <= max(idx_sol, idx_produto, idx_desc):
            continue
        sol = fmt_solicitacao_import(linha[idx_sol])
        produto = fmt_produto_import(linha[idx_produto])
        descricao = fmt_texto_import(linha[idx_desc])
        if sol and produto and descricao:
            lookup[(sol, produto)] = descricao
    return lookup


def carregar_mapa_pedidos_por_produto_import(spreadsheet):
    """Monta um lookup (SOLICITAÇÃO, PRODUTO) -> PEDIDO a partir da aba
    Pedidos, usado como fallback no import de Solicitacoes quando o proprio
    relatorio do Totvs nao traz o Num. Pedido preenchido (acontece mesmo com
    o Pedido ja gerado e ATENDIDO - visto ao vivo nas SCs 140965/140963, ver
    comentario em processar_linhas_import). Devolve {} se a aba nao
    existir/estiver vazia ou faltar alguma das 3 colunas - nesse caso o
    import de Solicitacoes simplesmente nao aplica nenhum fallback."""
    try:
        worksheet = spreadsheet.worksheet(ABA_PEDIDOS_IMPORT)
    except gspread.WorksheetNotFound:
        return {}

    valores = worksheet.get_all_values()
    if not valores:
        return {}
    cabecalho = valores[0]
    col_sol = resolver_coluna_real_import(cabecalho, "SOLICITAÇÃO", ALIASES_PEDIDOS_IMPORT)
    col_produto = resolver_coluna_real_import(cabecalho, "PRODUTO", {})
    col_pedido = resolver_coluna_real_import(cabecalho, "PEDIDO", {})
    if not col_sol or not col_produto or not col_pedido:
        return {}
    idx_sol = cabecalho.index(col_sol)
    idx_produto = cabecalho.index(col_produto)
    idx_pedido = cabecalho.index(col_pedido)

    lookup = {}
    for linha in valores[1:]:
        if len(linha) <= max(idx_sol, idx_produto, idx_pedido):
            continue
        sol = fmt_solicitacao_import(linha[idx_sol])
        produto = fmt_produto_import(linha[idx_produto])
        pedido = fmt_inteiro_import(linha[idx_pedido])
        if sol and produto and pedido:
            lookup.setdefault((sol, produto), pedido)
    return lookup


def obter_ou_criar_aba_import(spreadsheet, nome_aba, cabecalho_padrao=None):
    try:
        return spreadsheet.worksheet(nome_aba)
    except gspread.WorksheetNotFound:
        aba = spreadsheet.add_worksheet(title=nome_aba, rows=1000, cols=max(20, len(cabecalho_padrao or [])))
        if cabecalho_padrao:
            aba.update([cabecalho_padrao], "A1")
        return aba


def processar_arquivo_pc_import(arquivo, spreadsheet):
    worksheet = obter_ou_criar_aba_import(spreadsheet, ABA_PEDIDOS_IMPORT)
    indice_existentes, cabecalho_real = carregar_indice_existentes_import(worksheet, CHAVE_PEDIDOS_IMPORT, ALIASES_PEDIDOS_IMPORT)
    if not cabecalho_real:
        raise RuntimeError(f"Aba '{ABA_PEDIDOS_IMPORT}' está vazia (sem cabeçalho). Configure o cabeçalho antes de importar.")

    correcao_descricao = carregar_descricoes_solicitacoes_import(spreadsheet)

    arquivo.seek(0)
    df = pd.read_excel(arquivo, header=1)
    novas_linhas, atualizacoes, duplicadas, atualizadas, chaves_deste_arquivo = processar_linhas_import(
        df, MAPA_PEDIDOS_IMPORT, cabecalho_real, ALIASES_PEDIDOS_IMPORT, CAMPOS_MANUAIS_PEDIDOS_IMPORT,
        CHAVE_PEDIDOS_IMPORT, indice_existentes,
        campo_status="STATUS", calcular_status=valor_status_origem_import, gatilho_status=STATUS_GATILHO_SUBSTITUICAO_IMPORT,
        campos_obrigatorios=("SOLICITAÇÃO",),
        campos_sempre_sobrescreve=CAMPOS_SEMPRE_SOBRESCREVE_PEDIDOS_IMPORT,
        correcao_descricao=correcao_descricao,
    )
    atualizacoes_exclusao = detectar_pedidos_excluidos_import(indice_existentes, chaves_deste_arquivo, cabecalho_real)
    aplicar_no_google_sheets_import(worksheet, novas_linhas, atualizacoes + atualizacoes_exclusao)
    return len(novas_linhas), duplicadas, atualizadas, len(atualizacoes_exclusao)


def processar_arquivo_sc_import(arquivo, spreadsheet):
    worksheet = obter_ou_criar_aba_import(spreadsheet, ABA_SOLICITACOES_IMPORT, CABECALHO_SOLICITACOES_IMPORT)
    indice_existentes, cabecalho_real = carregar_indice_existentes_import(worksheet, CHAVE_SOLICITACOES_IMPORT, {})
    if not cabecalho_real:
        cabecalho_real = CABECALHO_SOLICITACOES_IMPORT

    mapa_pedidos_por_produto = carregar_mapa_pedidos_por_produto_import(spreadsheet)

    arquivo.seek(0)
    df = pd.read_excel(arquivo, header=1)
    novas_linhas, atualizacoes, duplicadas, atualizadas, _ = processar_linhas_import(
        df, MAPA_SOLICITACOES_IMPORT, cabecalho_real, {}, [], CHAVE_SOLICITACOES_IMPORT, indice_existentes,
        mapa_pedidos_por_produto=mapa_pedidos_por_produto,
    )
    aplicar_no_google_sheets_import(worksheet, novas_linhas, atualizacoes)
    return len(novas_linhas), duplicadas, atualizadas


def processar_upload_protheus(arquivo):
    """Recebe um arquivo enviado via st.file_uploader, descobre se e PC ou SC
    e aplica a mesma logica do agente local direto no Google Sheets. Devolve
    (ok: bool, mensagem: str)."""
    try:
        client, _ = obter_client_gspread()
        spreadsheet = client.open_by_key(FILE_ID)
    except Exception as e:
        return False, f"❌ Erro ao conectar no Google Sheets: {e}"

    try:
        tipo = detectar_tipo_arquivo_import(arquivo)
        if tipo == "PC":
            novos, dup, atualizadas, excluidos = processar_arquivo_pc_import(arquivo, spreadsheet)
            msg_excluidos = f", {excluidos} marcado(s) como '{STATUS_EXCLUIDO_TOTVS_IMPORT}' (sumiram do relatório)" if excluidos else ""
            msg_compra_direta = _sufixo_compra_direta_import(spreadsheet)
            return True, f"✅ Pedidos: {novos} linha(s) nova(s), {atualizadas} atualizada(s) (campos em branco/status){msg_excluidos}, {dup} sem nenhuma alteração.{msg_compra_direta}"
        elif tipo == "SC":
            novos, dup, atualizadas = processar_arquivo_sc_import(arquivo, spreadsheet)
            msg_compra_direta = _sufixo_compra_direta_import(spreadsheet)
            return True, f"✅ Solicitações: {novos} linha(s) nova(s), {atualizadas} atualizada(s), {dup} sem nenhuma alteração.{msg_compra_direta}"
        else:
            return False, "❌ Layout do arquivo não reconhecido (não parece Listagem de Pedidos nem de Solicitações do Protheus)."
    except Exception as e:
        return False, f"❌ Erro ao processar o arquivo: {e}"


def _sufixo_compra_direta_import(spreadsheet) -> str:
    """Roda sincronizar_status_compra_direta_import e depois
    forcar_atendido_quando_entrega_import (nessa ordem - a segunda corrige
    qualquer coisa que a primeira, ou qualquer outra causa, tenha deixado
    errada) e devolve um sufixo de mensagem pronto pra concatenar no
    retorno de processar_upload_protheus - nunca deixa uma falha nessa
    sincronização derrubar o import principal (que já rodou e já foi salvo
    com sucesso antes desta parte)."""
    partes = []
    try:
        atualizados = sincronizar_status_compra_direta_import(spreadsheet)
        if atualizados:
            partes.append(f" {atualizados} pedido(s) marcado(s) como 'COMPRA DIRETA' (Criticidade da Solicitação).")
    except Exception as e:
        partes.append(f" ⚠️ Falha ao sincronizar status de Compra Direta: {e}")
    try:
        corrigidos = forcar_atendido_quando_entrega_import(spreadsheet)
        if corrigidos:
            partes.append(f" {corrigidos} pedido(s) corrigido(s) para 'ATENDIDO' (já tinham Entrega registrada).")
    except Exception as e:
        partes.append(f" ⚠️ Falha ao forçar status Atendido: {e}")
    return "".join(partes)

