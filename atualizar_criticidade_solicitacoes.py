"""Atualiza a coluna CRITICIDADE na aba "Solicitacoes" com os dados
exportados da tela de Cotações do TOTVS.

Processo manual temporário: o TOTVS ainda não carrega o campo Criticidade
por Solicitação (troca de sistema em andamento), então esse dado chega por
fora, num export da tela de Cotações. Rode este script toda vez que chegar
um export novo - ele sempre sobrescreve a CRITICIDADE com o valor mais
recente do arquivo (decisão explícita do usuário, 2026-09-30), aplicando o
mesmo valor em todas as linhas (todo ITEM SC) daquela Solicitação.

Casa pela coluna "Número Protheus" do export (= SOLICITAÇÃO na base). Uma
Solicitação pode vir sem Número Protheus preenchido no export (visto ao
vivo, 2026-09-30: 28 de 252 linhas) - nesse caso casa pelo "Número
Solicitação" do export (= COD SC SCM na base) como alternativa.

Uso:
    python atualizar_criticidade_solicitacoes.py --arquivo "Cotações - ....xls"
"""
import argparse
import tomllib
from pathlib import Path

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

FILE_ID = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"
ABA_SOLICITACOES = "Solicitacoes"
SECRETS_PADRAO = Path(__file__).parent / ".streamlit" / "secrets.toml"


def obter_client(secrets_path):
    with open(secrets_path, "rb") as f:
        dados = tomllib.load(f)
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(dados["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)


def resolver_coluna(colunas, contem, obrigatoria=True):
    achada = next((c for c in colunas if contem.lower() in c.lower()), None)
    if achada is None and obrigatoria:
        raise RuntimeError(f"Coluna contendo '{contem}' nao encontrada. Colunas do arquivo: {list(colunas)}")
    return achada


def carregar_arquivo(caminho) -> pd.DataFrame:
    """Devolve um DataFrame com colunas Solicitacao (SOLICITAÇÃO, 6 digitos,
    pode vir vazio), CodScmScm (COD SC SCM, fallback de chave) e Criticidade
    (maiuscula, pronta pra gravar)."""
    df = pd.read_excel(caminho, sheet_name=0, header=0)
    df.columns = df.columns.astype(str).str.strip()

    col_num = resolver_coluna(df.columns, "Protheus")
    col_scm = resolver_coluna(df.columns, "Número Solicitação")
    col_crit = resolver_coluna(df.columns, "Criticidade")

    def fmt_solicitacao(v):
        if pd.isna(v):
            return ""
        return str(int(v)).strip().zfill(6)

    saida = pd.DataFrame({
        "Solicitacao": df[col_num].apply(fmt_solicitacao),
        "CodScmScm": df[col_scm].fillna("").astype(str).str.strip(),
        "Criticidade": df[col_crit].fillna("").astype(str).str.strip().str.upper(),
    })
    saida = saida[saida["Criticidade"] != ""]
    return saida


def aplicar_criticidade(spreadsheet, df_origem: pd.DataFrame):
    """Sobrescreve CRITICIDADE em toda linha (ITEM SC) de cada Solicitação
    encontrada - casa primeiro por SOLICITAÇÃO, senao por COD SC SCM.
    Devolve (linhas_atualizadas, solicitacoes_nao_encontradas)."""
    worksheet = spreadsheet.worksheet(ABA_SOLICITACOES)
    valores = worksheet.get_all_values()
    if not valores:
        return 0, len(df_origem)
    cabecalho = valores[0]
    idx_sol = cabecalho.index("SOLICITAÇÃO")
    idx_criticidade = cabecalho.index("CRITICIDADE")
    idx_codscm = cabecalho.index("COD SC SCM") if "COD SC SCM" in cabecalho else None

    linhas_por_sol: dict[str, list[int]] = {}
    linhas_por_codscm: dict[str, list[int]] = {}
    for i, linha in enumerate(valores[1:], start=2):
        sol = linha[idx_sol].strip().lstrip("0").zfill(6) if idx_sol < len(linha) and linha[idx_sol].strip() else ""
        if sol:
            linhas_por_sol.setdefault(sol, []).append(i)
        if idx_codscm is not None and idx_codscm < len(linha) and linha[idx_codscm].strip():
            linhas_por_codscm.setdefault(linha[idx_codscm].strip().upper(), []).append(i)

    celulas = []
    nao_encontradas = 0
    for _, row in df_origem.iterrows():
        linhas_alvo = linhas_por_sol.get(row["Solicitacao"]) if row["Solicitacao"] else None
        if not linhas_alvo and row["CodScmScm"]:
            linhas_alvo = linhas_por_codscm.get(row["CodScmScm"].upper())
        if not linhas_alvo:
            nao_encontradas += 1
            continue
        for linha_num in linhas_alvo:
            valor_atual = valores[linha_num - 1][idx_criticidade].strip() if idx_criticidade < len(valores[linha_num - 1]) else ""
            if valor_atual != row["Criticidade"]:
                celulas.append(gspread.Cell(linha_num, idx_criticidade + 1, row["Criticidade"]))

    if celulas:
        worksheet.update_cells(celulas, value_input_option="RAW")
    return len(celulas), nao_encontradas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arquivo", required=True)
    parser.add_argument("--secrets", default=str(SECRETS_PADRAO))
    args = parser.parse_args()

    client = obter_client(args.secrets)
    spreadsheet = client.open_by_key(FILE_ID)

    df = carregar_arquivo(args.arquivo)
    atualizadas, nao_encontradas = aplicar_criticidade(spreadsheet, df)
    print(f"{atualizadas} celula(s) de CRITICIDADE atualizada(s). {nao_encontradas} solicitacao(oes) do arquivo nao encontrada(s) na base.")


if __name__ == "__main__":
    main()
