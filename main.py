import streamlit as st
import pandas as pd
import re
import unicodedata
import html as html_lib
from datetime import datetime, timedelta
from io import BytesIO
import urllib.request
import gspread
import streamlit.components.v1 as components

from comum import (
    FILE_ID,
    aplicar_estilos,
    renderizar_cabecalho,
    renderizar_rodape,
    inicializar_sessao_login,
    renderizar_popup_login,
    obter_client_gspread,
    _ler_aba_como_df,
    converter_para_numerico,
    formatar_moeda_br,
    validar_formato_data,
    formatar_para_dd_mm_aaaa,
    parse_data_br,
    gerar_bytes_excel,
)
from importador_protheus import (
    STATUS_EXCLUIDO_TOTVS,
    processar_upload_protheus,
)

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Portal Gestão de Compras | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. ESTILOS COMPARTILHADOS
aplicar_estilos()

# Sentinela de _row_idx pras linhas sinteticas "Em Cotação" (Solicitação sem
# Pedido ainda) - bem acima de qualquer linha real possivel na aba Pedidos,
# usado pra bloquear salvamento nelas (ver "SALVAMENTO PROCV" mais abaixo).
SENTINELA_ROW_IDX_EM_COTACAO = 10_000_000

# STATUS_EXCLUIDO_TOTVS vem de importador_protheus.py (ver comentario la) -
# pedido marcado assim sumiu do relatorio do Totvs; a linha fica na planilha
# (base = fonte de verdade), mas nao deve aparecer nem ser considerada em
# nenhum painel/calculo/consulta (decisao explicita do usuario). Filtrado
# logo na leitura, o mais cedo possivel, pra nenhum calculo/filtro/exportacao
# rio abaixo enxergar essa linha.

# ------------------------------------------------------------------
# POPUP DE DADOS BANCÁRIOS (busca por Pedido) - lê as mesmas abas
# "Pedidos" e "CadastroFornecedores" que o app companheiro
# dados-bancarios-fornecedores.streamlit.app usa e mantém, então mostra o
# mesmo card aqui dentro do portal sem precisar abrir o outro app.
ABA_CADASTRO_FORNECEDORES = "CadastroFornecedores"
CABECALHO_CADASTRO_FORNECEDORES = ["FORNECEDOR", "CNPJ", "BANCO", "AGENCIA", "CONTA", "PIX", "EMAIL", "CONTATO", "VENDEDOR"]


@st.cache_data(ttl=120)
def buscar_pedido_fornecedor_valor(numero_pedido: str):
    """Devolve (fornecedor, valor_total, qtd_itens) ou None se o pedido não
    existir (ou só existir marcado como EXCLUÍDO DO TOTVS)."""
    client, _ = obter_client_gspread()
    spreadsheet = client.open_by_key(FILE_ID)
    df = _ler_aba_como_df(spreadsheet, "Pedidos")
    if df.empty or "PEDIDO" not in df.columns:
        return None
    termo = re.sub(r"\.0$", "", str(numero_pedido).strip())
    col_pedido = df["PEDIDO"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip()
    linhas = df[col_pedido == termo]
    if "STATUS" in df.columns:
        linhas = linhas[linhas["STATUS"].astype(str).str.strip().str.upper() != STATUS_EXCLUIDO_TOTVS]
    if linhas.empty:
        return None
    fornecedor = str(linhas.iloc[0].get("FORNECEDOR", "")).strip().upper()
    valor_total = sum(converter_para_numerico(v) for v in linhas.get("VALOR TOTAL", []))
    return fornecedor, valor_total, len(linhas)


def buscar_cadastro_fornecedor_bancario(nome_fornecedor: str) -> dict:
    client, _ = obter_client_gspread()
    spreadsheet = client.open_by_key(FILE_ID)
    df = _ler_aba_como_df(spreadsheet, ABA_CADASTRO_FORNECEDORES)
    if df.empty or "FORNECEDOR" not in df.columns:
        return {}
    chave = str(nome_fornecedor or "").strip().upper()
    linhas = df[df["FORNECEDOR"].astype(str).str.strip().str.upper() == chave]
    if linhas.empty:
        return {}
    return {col: str(linhas.iloc[0].get(col, "")) for col in CABECALHO_CADASTRO_FORNECEDORES}


def renderizar_card_dados_bancarios(pedido, fornecedor, cnpj, banco, agencia, conta, pix, email, contato, vendedor, valor_formatado):
    """Mesmo card visual (fundo branco/cinza claro, formato de tabela) do
    app dados-bancarios-fornecedores, embutido aqui pra mostrar no popup
    sem sair do portal."""

    def esc(valor):
        return html_lib.escape(str(valor)) if valor else ""

    linhas = [
        ("CNPJ", cnpj), ("BANCO", banco), ("AGÊNCIA", agencia), ("CONTA", conta),
        ("PIX", pix), ("E-MAIL", email), ("CONTATO", contato), ("VENDEDOR", vendedor),
        ("R$", valor_formatado),
    ]
    linhas_html = "".join(f'<tr><td class="rotulo">{rot}</td><td class="valor">{esc(val)}</td></tr>' for rot, val in linhas)
    pedido_esc = esc(pedido)
    nome_arquivo = f"dados_bancarios_pedido_{re.sub(r'[^0-9A-Za-z_-]', '', str(pedido))}.jpg"

    return f"""
    <div id="wrap">
      <div id="ficha-card">
        <table>
          <tr><td colspan="2" class="cabecalho">
            <span class="rotulo-cabecalho">Pedido de Compras;</span>
            <span class="numero-cabecalho">{pedido_esc}</span>
          </td></tr>
          <tr><td class="rotulo">FORNECEDOR</td><td class="valor">{esc(fornecedor)}</td></tr>
          {linhas_html}
        </table>
      </div>
      <div id="botoes">
        <button id="btn-copiar" onclick="copiarImagem()">📋 Copiar Imagem</button>
        <button id="btn-baixar" onclick="baixarImagem()">⬇️ Baixar JPG</button>
        <span id="status"></span>
      </div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    function gerarCanvas() {{
        return html2canvas(document.getElementById('ficha-card'), {{backgroundColor: '#ffffff'}});
    }}
    function baixarImagem() {{
        var status = document.getElementById('status');
        gerarCanvas().then(function(canvas) {{
            var link = document.createElement('a');
            link.download = '{nome_arquivo}';
            link.href = canvas.toDataURL('image/jpeg', 0.95);
            link.click();
            status.textContent = '✅ Baixado.';
        }});
    }}
    function copiarImagem() {{
        var status = document.getElementById('status');
        gerarCanvas().then(function(canvas) {{
            canvas.toBlob(function(blob) {{
                if (navigator.clipboard && window.ClipboardItem) {{
                    navigator.clipboard.write([new ClipboardItem({{'image/png': blob}})]).then(function() {{
                        status.textContent = '✅ Copiado! Já pode colar (Ctrl+V) em outro lugar.';
                    }}).catch(function() {{
                        status.textContent = '⚠️ Não deu pra copiar automaticamente - use Baixar JPG.';
                    }});
                }} else {{
                    status.textContent = '⚠️ Este navegador não suporta copiar imagem - use Baixar JPG.';
                }}
            }});
        }});
    }}
    </script>
    <style>
    body {{ margin:0; padding-bottom:16px; font-family: 'Segoe UI', Arial, sans-serif; background:#ffffff; }}
    #wrap {{ width: 100%; max-width: 600px; margin: 0 auto; }}
    #ficha-card {{ width: 100%; height: 400px; box-sizing: border-box; border: 5px solid #B8B8B8; background:#ffffff; overflow: hidden; }}
    table {{ width: 100%; height: 100%; border-collapse: collapse; table-layout: auto; }}
    td {{ border: 1px solid #9A9A9A; padding: 5px 18px; font-size: 14px; line-height:1.15; color: #1c1c3a; }}
    td.cabecalho {{ background:#D3D3D3; border-bottom: 3px solid #9A9A9A; padding: 10px 18px; }}
    .rotulo-cabecalho {{ font-weight:700; font-size:17px; }}
    .numero-cabecalho {{ font-weight:800; font-size:22px; float:right; }}
    td.rotulo {{ width:1%; white-space:nowrap; background:#D3D3D3; font-weight:700; padding-left:10px; padding-right:6px; }}
    td.valor {{ background:#ffffff; }}
    #botoes {{ margin-top:22px; display:flex; align-items:center; flex-wrap:wrap; gap:10px; }}
    #botoes button {{ background:#00C2D6; color:#06212E; border:none; padding:10px 16px; border-radius:6px; cursor:pointer; font-weight:600; font-size:13px; }}
    #botoes button:hover {{ background:#00A8B8; }}
    #status {{ font-size:13px; color:#5B6459; }}
    </style>
    """


@st.dialog("🏦 Dados Bancários do Fornecedor")
def abrir_popup_dados_bancarios():
    numero_pedido_popup = st.text_input("Número do Pedido de Compras", key="popup_num_pedido", placeholder="Ex: 179723")
    if st.button("🔍 Buscar", key="popup_btn_buscar", type="primary"):
        if not numero_pedido_popup.strip():
            st.warning("Digite um número de pedido.")
        else:
            resultado = buscar_pedido_fornecedor_valor(numero_pedido_popup)
            if not resultado:
                st.error(f"Nenhum pedido ativo encontrado com o número {numero_pedido_popup.strip()}.")
            else:
                fornecedor, valor_total, qtd_itens = resultado
                cadastro = buscar_cadastro_fornecedor_bancario(fornecedor)
                if not cadastro:
                    st.warning(f"Fornecedor **{fornecedor}** ainda não tem dados bancários cadastrados.")
                    st.link_button(
                        "🏦 Inserir Dados Bancários",
                        "https://dados-bancarios-fornecedores.streamlit.app/",
                        type="primary",
                    )
                else:
                    components.html(
                        renderizar_card_dados_bancarios(
                            pedido=re.sub(r"\.0$", "", numero_pedido_popup.strip()), fornecedor=fornecedor,
                            cnpj=cadastro.get("CNPJ", ""), banco=cadastro.get("BANCO", ""), agencia=cadastro.get("AGENCIA", ""),
                            conta=cadastro.get("CONTA", ""), pix=cadastro.get("PIX", ""), email=cadastro.get("EMAIL", ""),
                            contato=cadastro.get("CONTATO", ""), vendedor=cadastro.get("VENDEDOR", ""),
                            valor_formatado=formatar_moeda_br(valor_total),
                        ),
                        height=490, scrolling=False,
                    )
                    st.caption(f"{qtd_itens} item(ns) somados deste pedido.")
                    st.link_button(
                        "✏️ Editar Dados Bancários",
                        "https://dados-bancarios-fornecedores.streamlit.app/",
                    )


def montar_linhas_em_cotacao(df_pc, df_sc):
    """Solicitações sem PEDIDO proprio preenchido E sem nenhuma linha
    correspondente (mesma Solicitação+Produto) na aba Pedidos - ainda não
    viraram pedido. Devolve um DataFrame com as MESMAS colunas de df_pc,
    STATUS="Em Cotação" e so os campos que fazem sentido pra uma Solicitação
    preenchidos (Centro de Custo, Solicitação, Produto, Descrição, Um, Qtd);
    o resto (Pedido, Fornecedor, datas, valores...) fica em branco. Some do
    resultado sozinha assim que a importação do PC correspondente criar a
    linha real na aba Pedidos - nao precisa de nenhum passo de "substituição"
    manual, e so essa mesma verificação rodando de novo."""
    colunas_normalizadas_pc = {c.upper().strip().replace('Í', 'I').replace('Ã', 'A').replace('Ç', 'C'): c for c in df_pc.columns}
    col_solic_pc = colunas_normalizadas_pc.get("SOLICITAÇÃO") or colunas_normalizadas_pc.get("SOLICITACAO")
    col_produto_pc = colunas_normalizadas_pc.get("PRODUTO")
    col_status_pc = colunas_normalizadas_pc.get("STATUS")

    if df_sc.empty or not col_solic_pc or not col_produto_pc:
        return pd.DataFrame(columns=df_pc.columns)

    chaves_com_pedido = set(zip(
        df_pc[col_solic_pc].astype(str).str.strip(),
        df_pc[col_produto_pc].astype(str).str.strip(),
    ))

    colunas_normalizadas_sc = {c.upper().strip().replace('Í', 'I').replace('Ã', 'A').replace('Ç', 'C'): c for c in df_sc.columns}
    col_solic_sc = colunas_normalizadas_sc.get("SOLICITAÇÃO") or colunas_normalizadas_sc.get("SOLICITACAO")
    col_pedido_sc = colunas_normalizadas_sc.get("PEDIDO")
    col_produto_sc = colunas_normalizadas_sc.get("PRODUTO")

    if not (col_solic_sc and col_pedido_sc and col_produto_sc):
        return pd.DataFrame(columns=df_pc.columns)

    sem_pedido = df_sc[df_sc[col_pedido_sc].astype(str).str.strip() == ""]
    if sem_pedido.empty:
        return pd.DataFrame(columns=df_pc.columns)

    chaves_sc = list(zip(
        sem_pedido[col_solic_sc].astype(str).str.strip(),
        sem_pedido[col_produto_sc].astype(str).str.strip(),
    ))
    candidatas = sem_pedido[[chave not in chaves_com_pedido for chave in chaves_sc]]
    if candidatas.empty:
        return pd.DataFrame(columns=df_pc.columns)

    linhas_cotacao = pd.DataFrame("", index=range(len(candidatas)), columns=df_pc.columns)
    if col_status_pc:
        linhas_cotacao[col_status_pc] = "EM COTAÇÃO"

    mapa_sc_para_pc = {
        "SOLICITACAO": col_solic_sc,
        "PRODUTO": col_produto_sc,
        "DESCRICAO": colunas_normalizadas_sc.get("DESCRICAO"),
        "UM": colunas_normalizadas_sc.get("UM"),
        "QTD": colunas_normalizadas_sc.get("QTD"),
        "CENTRO DE CUSTO": colunas_normalizadas_sc.get("CENTRO DE CUSTO"),
    }
    for campo_pc, col_real_sc in mapa_sc_para_pc.items():
        col_destino = colunas_normalizadas_pc.get(campo_pc)
        if col_destino and col_real_sc:
            linhas_cotacao[col_destino] = candidatas[col_real_sc].values

    linhas_cotacao.index = range(SENTINELA_ROW_IDX_EM_COTACAO, SENTINELA_ROW_IDX_EM_COTACAO + len(linhas_cotacao))
    return linhas_cotacao


# 4. CARREGAMENTO SEGURO DIRETO DA ABA "Pedidos" (+ Solicitações sem pedido, como "Em Cotação")
@st.cache_data(ttl=60)
def carregar_dados_seguros():
    try:
        client, _ = obter_client_gspread()

        spreadsheet = client.open_by_key(FILE_ID)
        try:
            worksheet = spreadsheet.worksheet("Pedidos")
        except:
            worksheet = spreadsheet.get_worksheet(0)

        dados = worksheet.get_all_values()
        if not dados:
            return pd.DataFrame()

        cabecalho = [str(c).strip() for c in dados[0]]
        linhas = dados[1:]

        linhas_normalizadas = []
        for linha in linhas:
            while len(linha) < len(cabecalho):
                linha.append("")
            linhas_normalizadas.append(linha[:len(cabecalho)])

        df = pd.DataFrame(linhas_normalizadas, columns=cabecalho, dtype=str).fillna('')

        col_status_bruto = next((c for c in df.columns if c.upper().strip() == "STATUS"), None)
        if col_status_bruto:
            # NUNCA resetar o index aqui: o _row_idx (linha física da planilha,
            # usado pra gravar via worksheet.update_cell) é calculado em
            # montar_df_painel como index+2, contando com que o index do df
            # continue sendo a posição ORIGINAL na aba "Pedidos" (antes de
            # qualquer filtro). Um reset_index(drop=True) depois de excluir as
            # linhas "EXCLUÍDO DO TOTVS" fazia todo pedido abaixo de uma linha
            # excluída calcular um _row_idx errado (deslocado pela quantidade
            # de linhas excluídas acima dele) e gravar na linha física errada.
            df = df[df[col_status_bruto].astype(str).str.strip().str.upper() != STATUS_EXCLUIDO_TOTVS]

        try:
            df_sc = _ler_aba_como_df(spreadsheet, "Solicitacoes")
            linhas_cotacao = montar_linhas_em_cotacao(df, df_sc)
            if not linhas_cotacao.empty:
                df = pd.concat([df, linhas_cotacao])
        except Exception:
            pass  # "Em Cotação" e um extra - se der erro, so segue com os Pedidos normais

        return df
    except Exception as e:
        st.session_state.erro_tecnico = f"Erro Gspread: {str(e)}"
        return pd.DataFrame()

if 'dados_globais' not in st.session_state or st.session_state.dados_globais.empty:
    st.session_state.dados_globais = carregar_dados_seguros()

df_pc = st.session_state.dados_globais

# Estados de sessão
inicializar_sessao_login()
if "mostrar_popup_importar" not in st.session_state:
    st.session_state.mostrar_popup_importar = False
if "gaveta_aberta" not in st.session_state:
    st.session_state.gaveta_aberta = True

# 5. CABEÇALHO INTEGRADO
renderizar_cabecalho("Portal Gestão de Compras")

# 6. JANELA POPUP DISCRETA DE LOGIN
renderizar_popup_login()

# 8. DICIONÁRIO MAPEADO RIGOROSAMENTE COM AS SUAS COLUNAS EXATAS
DICIONARIO_COLUNAS_EXATAS = [
    {"planilha": ["STATUS"], "tela": "Status", "tipo": "texto"},
    {"planilha": ["CENTRO DE CUSTO"], "tela": "Centro De Custo", "tipo": "texto"},
    {"planilha": ["SOLICITAÇÃO", "SOLICITACAO"], "tela": "Solicitação", "tipo": "texto"},
    {"planilha": ["PEDIDO"], "tela": "Pedido", "tipo": "pedido"},   
    {"planilha": ["CONDIÇÃO PAGAMENTO"], "tela": "Condição Pagamento", "tipo": "texto"},
    {"planilha": ["DATA PEDIDO"], "tela": "Emissão Pc", "tipo": "data"},
    {"planilha": ["DATA LIBERAÇÃO", "DATA LIBERACAO"], "tela": "Aprovação Pc", "tipo": "data"},
    {"planilha": ["ENVIO"], "tela": "Envio Pc", "tipo": "data"},
    {"planilha": ["PAGAMENTO"], "tela": "Pagamento Pc", "tipo": "texto"}, 
    {"planilha": ["PREVISÃO DE ENTREGA"], "tela": "Previsão De Entrega", "tipo": "data"},
    {"planilha": ["ENTREGA"], "tela": "Entrega", "tipo": "data"},
    {"planilha": ["FORNECEDOR"], "tela": "Fornecedor", "tipo": "texto"},
    {"planilha": ["GRUPO"], "tela": "Grupo", "tipo": "texto"},
    {"planilha": ["PRODUTO"], "tela": "Produto", "tipo": "produto"},                 
    {"planilha": ["DESCRICAO"], "tela": "Descrição", "tipo": "texto"},
    {"planilha": ["UM"], "tela": "Um", "tipo": "texto"},
    {"planilha": ["QTD"], "tela": "Qtd", "tipo": "numero"},
    {"planilha": ["PREÇO UNITÁRIO", "PRECO UNITARIO"], "tela": "Preço Unitário", "tipo": "moeda"},
    {"planilha": ["VALOR TOTAL"], "tela": "Valor Total", "tipo": "moeda"},
    {"planilha": ["NF REMESSA"], "tela": "NF Remessa", "tipo": "texto"},
    {"planilha": ["LOGISTICA"], "tela": "Logística", "tipo": "logistica"},
    {"planilha": ["DATA LOGISTICA"], "tela": "Data Logística", "tipo": "data"}
]

def aplicar_filtros(df_pc):
    """Aplica os filtros ativos (lidos do session_state) e devolve (df_final, colunas_normalizadas)."""
    df_final = df_pc.copy()
    colunas_normalizadas = {c.upper().strip().replace('Í', 'I').replace('Ã', 'A').replace('Ç', 'C'): c for c in df_final.columns}

    if st.session_state.filtro_pc_val:
        pc_termo = str(st.session_state.filtro_pc_val).strip()
        col_pc = colunas_normalizadas.get("PEDIDO")
        if col_pc:
            df_final = df_final[df_final[col_pc].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.contains(pc_termo, na=False)]

    if st.session_state.filtro_sc_val:
        sc_termo = str(st.session_state.filtro_sc_val).strip()
        col_sc = colunas_normalizadas.get("SOLICITAÇÃO") or colunas_normalizadas.get("SOLICITACAO")
        if col_sc:
            df_final = df_final[df_final[col_sc].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.contains(sc_termo, na=False)]

    if st.session_state.filtro_cc_val:
        col_cc = colunas_normalizadas.get("CENTRO DE CUSTO")
        if col_cc:
            selecionados_cc = set(st.session_state.filtro_cc_val)
            df_final = df_final[df_final[col_cc].astype(str).str.strip().isin(selecionados_cc)]

    col_status_verificacao = colunas_normalizadas.get("STATUS")
    if st.session_state.filtro_status_val != "Todos" and col_status_verificacao:
        df_final = df_final[df_final[col_status_verificacao].astype(str).str.strip() == st.session_state.filtro_status_val]

    if st.session_state.filtro_data_val and len(st.session_state.filtro_data_val) == 2:
        if st.session_state.filtro_data_val[0] is not None and st.session_state.filtro_data_val[1] is not None:
            col_emissao_original = colunas_normalizadas.get("DATA PEDIDO")
            if col_emissao_original:
                datas_convertidas = pd.to_datetime(df_final[col_emissao_original], errors='coerce', format='mixed', dayfirst=True).dt.date
                df_final = df_final[(datas_convertidas >= st.session_state.filtro_data_val[0]) & (datas_convertidas <= st.session_state.filtro_data_val[1])]

    return df_final, colunas_normalizadas


def montar_df_painel(df_final, colunas_normalizadas):
    """Recebe o df ja filtrado e monta o df_painel (colunas da tela), aplicando as mesmas regras de N/A."""
    df_painel = pd.DataFrame(index=df_final.index)

    for col_config in DICIONARIO_COLUNAS_EXATAS:
        nome_exibicao_tela = col_config["tela"]
        tipo_campo = col_config["tipo"]

        col_real = None
        for alt in col_config["planilha"]:
            alt_clean = alt.upper().strip().replace('Í', 'I').replace('Ã', 'A').replace('Ç', 'C')
            for c_up in colunas_normalizadas:
                c_up_clean = c_up.replace('Í', 'I').replace('Ã', 'A').replace('Ç', 'C')
                if c_up_clean == alt_clean:
                    col_real = colunas_normalizadas[c_up]
                    break
            if col_real:
                break

        if col_real:
            valores_originais = df_final[col_real]
            if tipo_campo == "data":
                df_painel[nome_exibicao_tela] = valores_originais.apply(formatar_para_dd_mm_aaaa)
            elif tipo_campo == "pedido":
                df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            elif tipo_campo == "produto":
                df_painel[nome_exibicao_tela] = valores_originais.apply(lambda val: str(val).split('.')[0].strip().zfill(10) if str(val).strip() and str(val).lower() != 'nan' else "")
            elif tipo_campo == "moeda":
                df_painel[nome_exibicao_tela] = valores_originais.apply(formatar_moeda_br)
            elif tipo_campo == "numero":
                df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            else:
                df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '').str.strip()
        else:
            df_painel[nome_exibicao_tela] = ""

    # Associa a linha física exata da planilha
    df_painel["_row_idx"] = [idx + 2 for idx in df_final.index]

    col_status_tela = colunas_normalizadas.get("STATUS")
    if col_status_tela:
        termos_excecao = ["SERVIÇO", "CANCELADO PELO SOLICITANTE", "REJEITADO PELO APROVADOR", "COMPRA DIRETA", STATUS_EXCLUIDO_TOTVS]
        mask_status = df_painel["Status"].astype(str).str.upper().apply(
            lambda s: any(t in s for t in termos_excecao)
        )
        for col_nome in ["Previsão De Entrega", "Entrega"]:
            if col_nome in df_painel.columns:
                df_painel.loc[mask_status, col_nome] = "N/A"

    if "Previsão De Entrega" in df_painel.columns and "Entrega" in df_painel.columns:
        mascara_vazia = (df_painel["Previsão De Entrega"] == "") | (df_painel["Previsão De Entrega"].isna())
        df_painel.loc[mascara_vazia, "Previsão De Entrega"] = df_painel.loc[mascara_vazia, "Entrega"]

    if "Pagamento Pc" in df_painel.columns and "Condição Pagamento" in df_painel.columns:
        condicao_normalizada = df_painel["Condição Pagamento"].astype(str).str.upper().str.strip()
        mascara_na = (
            (~condicao_normalizada.str.contains("A VISTA", na=False)) &
            (~condicao_normalizada.str.contains("ENT", na=False)) &
            (~condicao_normalizada.str.contains("VENCIDO", na=False)) &
            (~condicao_normalizada.str.contains("PAGO", na=False)) &
            (~condicao_normalizada.str.contains("50%", na=False, regex=False))
        )
        df_painel.loc[mascara_na, "Pagamento Pc"] = "N/A"

    colunas_para_formatar = ["Envio Pc", "Pagamento Pc", "Previsão De Entrega", "Entrega", "Emissão Pc", "Aprovação Pc"]
    for col_data in colunas_para_formatar:
        if col_data in df_painel.columns:
            df_painel[col_data] = df_painel[col_data].apply(
                lambda x: x if str(x).upper() == "N/A" else formatar_para_dd_mm_aaaa(x)
            )

    # Todo texto do painel em caixa alta
    for col in df_painel.columns:
        if col == "_row_idx":
            continue
        df_painel[col] = df_painel[col].astype(str).str.upper()

    return df_painel.dropna(how='all')


def calcular_colunas_sla(df_painel):
    """Calcula as colunas Sla Pagamento e Sla Entrega (dias corridos),
    portadas diretamente das formulas reais da planilha de follow up:

    Sla Pagamento (Excel):
      =SEERRO(SE(OU([@STATUS]="rejeitado pelo aprovador";[@STATUS]="Cancelado";D="------");
        ""; SE(C="";""; SE(D="";SE(H="";HOJE()-C;H-C);D-C))); "")
      (C=Envio Pc, D=Pagamento Pc, H=Entrega)

    Sla Entrega: atrelado a Envio Pc - conta todo dia (HOJE-Envio) e congela
    em (Entrega-Envio) assim que a Entrega for inserida, seja manualmente
    pelo almoxarifado ou via importação. Não depende do texto exato do
    Status nem da Previsão De Entrega (o formulário original da planilha de
    follow up usava status="recebido"/Previsão De Entrega, mas isso não
    bate com os dados reais do painel - aqui o Status nunca é literalmente
    "recebido" e a Previsão De Entrega quase sempre já vem preenchida via
    o preenchimento automático a partir da Entrega, então a única regra que
    realmente funciona é: Entrega preenchida -> congela; senão -> conta).
    """
    hoje = datetime.now().date()

    sla_pagamento = []
    sla_entrega = []
    for _, linha in df_painel.iterrows():
        status_upper = str(linha.get("Status", "")).strip().upper()
        pagamento_raw = str(linha.get("Pagamento Pc", "")).strip()

        data_envio = parse_data_br(linha.get("Envio Pc", ""))
        data_pagamento = parse_data_br(pagamento_raw)
        data_entrega = parse_data_br(linha.get("Entrega", ""))

        # --- Sla Pagamento ---
        if status_upper in ("REJEITADO PELO APROVADOR", "CANCELADO", STATUS_EXCLUIDO_TOTVS) or pagamento_raw.upper() in ("------", "N/A"):
            sla_pagamento.append("")
        elif not data_envio:
            sla_pagamento.append("")
        elif not data_pagamento:
            if not data_entrega:
                sla_pagamento.append((hoje - data_envio).days)
            else:
                sla_pagamento.append((data_entrega - data_envio).days)
        else:
            sla_pagamento.append((data_pagamento - data_envio).days)

        # --- Sla Entrega ---
        if not data_envio:
            sla_entrega.append("")
        elif status_upper in ("REJEITADO PELO APROVADOR", STATUS_EXCLUIDO_TOTVS):
            sla_entrega.append("")
        elif data_entrega:
            sla_entrega.append((data_entrega - data_envio).days)
        else:
            sla_entrega.append((hoje - data_envio).days)

    df_painel["Sla Pagamento"] = sla_pagamento
    df_painel["Sla Entrega"] = sla_entrega

    # Reordena pra bater com a planilha de follow up: ... Pagamento Pc, Sla
    # Pagamento, Previsão De Entrega, Sla Entrega, Entrega, ...
    cols = [c for c in df_painel.columns if c not in ("Sla Pagamento", "Sla Entrega")]
    pos_pagamento = cols.index("Pagamento Pc") + 1 if "Pagamento Pc" in cols else len(cols)
    cols.insert(pos_pagamento, "Sla Pagamento")
    pos_previsao = cols.index("Previsão De Entrega") + 1 if "Previsão De Entrega" in cols else len(cols)
    cols.insert(pos_previsao, "Sla Entrega")
    return df_painel[cols]


# 6.5 IMPORTADOR PROTHEUS - logica movida para importador_protheus.py
# (importada no topo do arquivo); mantida fora do main.py para nao rodar
# codigo de Streamlit na hora de testar essas funcoes.


# 7. FILTROS E LÓGICA DE GAVETA
if "filtro_pc_val" not in st.session_state:
    st.session_state.filtro_pc_val = ""
if "filtro_sc_val" not in st.session_state:
    st.session_state.filtro_sc_val = ""
if "filtro_cc_val" not in st.session_state:
    st.session_state.filtro_cc_val = []
if "filtro_status_val" not in st.session_state:
    st.session_state.filtro_status_val = "Todos"
if "filtro_data_val" not in st.session_state:
    st.session_state.filtro_data_val = ()
if "editor_key_counter" not in st.session_state:
    # Muda a key do st.data_editor a cada nova pesquisa/limpeza/atualizacao de
    # banco e a cada salvamento bem-sucedido - forca o widget a "zerar" (nao
    # reaplicar edicoes antigas em cima de linhas novas) e evita depender de
    # comparar dataframes entre reruns (ver SALVAMENTO mais abaixo).
    st.session_state.editor_key_counter = 0

# Pré-cálculo do relatório (pra habilitar o botão Baixar Relatório dentro dos Filtros Avançados,
# com o resultado da busca mais recente - sem isso o botão mostraria dado de uma busca anterior)
tem_busca_ativa = st.session_state.filtro_pc_val or st.session_state.filtro_sc_val or st.session_state.filtro_cc_val or st.session_state.filtro_status_val != "Todos" or bool(st.session_state.filtro_data_val)

relatorio_bytes = None
if tem_busca_ativa and not df_pc.empty:
    try:
        _df_final_preview, _colunas_preview = aplicar_filtros(df_pc)
        if not _df_final_preview.empty:
            _df_painel_preview = montar_df_painel(_df_final_preview, _colunas_preview)
            if not _df_painel_preview.empty:
                if st.session_state.autenticado and st.session_state.departamento_ativo in ("almoxarifado", "gestor"):
                    _df_painel_preview = calcular_colunas_sla(_df_painel_preview)
                relatorio_bytes = gerar_bytes_excel(_df_painel_preview)
    except Exception:
        relatorio_bytes = None

col_cc_bruto = next((c for c in df_pc.columns if c.upper().strip() == "CENTRO DE CUSTO"), None) if not df_pc.empty else None
OPCOES_CENTRO_CUSTO = sorted({str(v).strip() for v in df_pc[col_cc_bruto] if str(v).strip()}) if col_cc_bruto else []

rotulo_seta = "Filtros Avançados ▲" if st.session_state.gaveta_aberta else "Filtros Avançados ▼"

with st.expander(rotulo_seta, expanded=st.session_state.gaveta_aberta):
    with st.form("form_filtros", clear_on_submit=False):
        f1, f2, f3, f4, f5 = st.columns(5)
        
        with f1:
            filtro_pc = st.text_input("Pedido (PC):", value=st.session_state.filtro_pc_val, placeholder="Nº do PC...")
        with f2:
            filtro_sc = st.text_input("Solicitação (SC):", value=st.session_state.filtro_sc_val, placeholder="Nº da SC...")
        with f3:
            valor_padrao_cc = [v for v in st.session_state.filtro_cc_val if v in OPCOES_CENTRO_CUSTO]
            filtro_cc = st.multiselect("Centro de Custo:", options=OPCOES_CENTRO_CUSTO, default=valor_padrao_cc, placeholder="Selecione um ou mais...")
        with f4:
            col_status_verificacao = next((c for c in df_pc.columns if "STATUS" in c.upper()), None) if not df_pc.empty else None
            if col_status_verificacao:
                lista_status_Filtro = ["Todos"] + sorted([str(x).strip() for x in df_pc[col_status_verificacao].unique() if str(x).strip() != ""])
            else:
                lista_status_Filtro = ["Todos"]
            idx_padrao = lista_status_Filtro.index(st.session_state.filtro_status_val) if st.session_state.filtro_status_val in lista_status_Filtro else 0
            filtro_status = st.selectbox("Status:", options=lista_status_Filtro, index=idx_padrao)
        with f5:
            filtro_data = st.date_input("Data de Emissão:", value=st.session_state.filtro_data_val, format="DD/MM/YYYY")

        st.write("") 
        
        esp0, espb, b1, b2, b3, b4 = st.columns([1.6, 1, 1, 1, 1, 1])
        with esp0:
            st.markdown("&nbsp;", unsafe_allow_html=True)
        with espb:
            st.markdown("&nbsp;", unsafe_allow_html=True)
        with b1:
            btn_pesquisar = st.form_submit_button("🔍 Pesquisar", use_container_width=True, type="primary")
            if btn_pesquisar:
                st.session_state.filtro_pc_val = filtro_pc
                st.session_state.filtro_sc_val = filtro_sc
                st.session_state.filtro_cc_val = filtro_cc
                st.session_state.filtro_status_val = filtro_status
                st.session_state.filtro_data_val = filtro_data
                st.session_state.gaveta_aberta = False
                st.session_state.editor_key_counter += 1
                st.rerun()

        with b2:
            btn_limpar = st.form_submit_button("❌ Limpar", use_container_width=True)
            if btn_limpar:
                st.session_state.filtro_pc_val = ""
                st.session_state.filtro_sc_val = ""
                st.session_state.filtro_cc_val = []
                st.session_state.filtro_status_val = "Todos"
                st.session_state.filtro_data_val = ()
                st.session_state.gaveta_aberta = True
                st.session_state.editor_key_counter += 1
                st.rerun()

        with b3:
            btn_atualizar = st.form_submit_button("🔄 Atualizar Banco", use_container_width=True)
            if btn_atualizar:
                st.session_state.dados_globais = carregar_dados_seguros()
                st.session_state.gaveta_aberta = True
                st.session_state.editor_key_counter += 1
                st.rerun()

        with b4:
            if not st.session_state.autenticado:
                if st.form_submit_button("🔐 Operador", use_container_width=True):
                    st.session_state.mostrar_popup_login = not st.session_state.mostrar_popup_login
                    st.rerun()
            else:
                if st.form_submit_button("🚪 Sair", use_container_width=True, key="btn_sair"):
                    st.session_state.autenticado = False
                    st.session_state.departamento_ativo = ""
                    st.session_state.mostrar_popup_login = False
                    st.rerun()

# 8.5 AÇÕES DO PAINEL (Importar Arquivo / Baixar Relatório / Salvar Alterações)
# Unificadas numa linha so, no mesmo nivel (logo apos os Filtros Avançados),
# pra sobrar mais espaço vertical pra tabela de amostra abaixo.
with st.container(key="acoes_painel_wrap"):
    if st.session_state.autenticado and st.session_state.departamento_ativo in ("compras", "gestor"):
        if st.button("📤 Importar Arquivo", key="btn_abrir_importar"):
            st.session_state.mostrar_popup_importar = not st.session_state.mostrar_popup_importar
            st.rerun()

    if relatorio_bytes:
        st.download_button(
            label="📥 Baixar Relatório",
            data=relatorio_bytes,
            file_name="Relatorio_Compras_Filtro.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_baixar_relatorio",
        )

    if st.session_state.autenticado:
        btn_salvar_dados = st.button("💾 Salvar Alterações", type="primary")
    else:
        btn_salvar_dados = False

    if st.session_state.autenticado and st.session_state.departamento_ativo == "compras":
        if st.button("🏦 Dados Bancários", key="btn_abrir_dados_bancarios"):
            abrir_popup_dados_bancarios()

if st.session_state.autenticado and st.session_state.departamento_ativo in ("compras", "gestor"):
    if st.session_state.mostrar_popup_importar:
        with st.container():
            st.markdown("""
                <div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border: 2px solid #478c3b; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <h3 style="color: #1e293b; margin-top: 0; font-size: 18px;">📤 Importar Arquivo do Protheus (PC/SC)</h3>
                </div>
            """, unsafe_allow_html=True)

            pop_imp_c1, pop_imp_c2 = st.columns([5, 1])
            with pop_imp_c1:
                arquivo_importar = st.file_uploader(
                    "Selecione o arquivo exportado do Protheus (Listagem de Pedidos ou de Solicitações):",
                    type=["xlsx", "xls"],
                    key="uploader_protheus",
                )
            with pop_imp_c2:
                st.write("")
                st.write("")
                if st.button("✖ Fechar", use_container_width=True, key="btn_fechar_importar"):
                    st.session_state.mostrar_popup_importar = False
                    st.rerun()

            if arquivo_importar is not None:
                if st.button("Processar Arquivo", type="primary", key="btn_processar_importacao"):
                    with st.spinner("Processando arquivo e gravando na planilha..."):
                        ok, mensagem = processar_upload_protheus(arquivo_importar)
                    if ok:
                        st.toast(mensagem)
                        st.cache_data.clear()
                        st.session_state.dados_globais = carregar_dados_seguros()
                        st.session_state.mostrar_popup_importar = False
                        st.rerun()
                    else:
                        st.error(mensagem)
            st.divider()

# 9. MOTOR DE BUSCA CASCATA
# tem_busca_ativa e o relatorio ja foram calculados antes dos Filtros Avançados
# (usados aqui embaixo, na contagem de registros).

if tem_busca_ativa:
    if df_pc.empty:
        st.markdown('<div class="custom-error-red custom-empty-state">⚠️ Base de dados vazia. Clique em "🔄 Atualizar Banco" nos Filtros Avançados.</div>', unsafe_allow_html=True)
    else:
        df_final, colunas_normalizadas = aplicar_filtros(df_pc)
        col_status_verificacao = colunas_normalizadas.get("STATUS")

        try:
            if not df_final.empty:
                df_painel = montar_df_painel(df_final, colunas_normalizadas)

                if not df_painel.empty:
                    txt_status = f"🔍 Registros Localizados ({len(df_painel)} itens)"
                    st.markdown(f'<div class="status-card">{txt_status}</div>', unsafe_allow_html=True)

                    # Confirmação de gravação persistida - o st.success() antigo
                    # aparecia e sumia no mesmo instante por causa do st.rerun()
                    # logo em seguida, entao o operador quase nunca chegava a
                    # ver a mensagem. Agora ela fica guardada e é mostrada aqui,
                    # de forma visível, ate a proxima acao (nova busca ou save).
                    if "msg_salvar_sucesso" in st.session_state:
                        st.success(st.session_state.pop("msg_salvar_sucesso"))

                    # Baixar Relatório / Salvar Alterações renderizados la em cima,
                    # na linha unificada de ações (ver seção 8.5) - btn_salvar_dados
                    # ja foi calculado por la.

                    # SLA (Pagamento/Entrega) - visivel so pro almoxarifado e o gestor
                    mostrar_sla = st.session_state.autenticado and st.session_state.departamento_ativo in ("almoxarifado", "gestor")
                    if mostrar_sla:
                        df_painel = calcular_colunas_sla(df_painel)

                    configuracao_colunas_tela = {}
                    
                    status_existentes = [str(x).strip() for x in df_pc[col_status_verificacao].unique() if str(x).strip() not in ("", "EM COTAÇÃO")] if col_status_verificacao else []
                    status_oficiais = [
                        "ENVIADO AO FORNECEDOR",
                        "ENVIADO AO FINANCEIRO",
                        "PAGO",
                        "FORNECEDOR DECLINOU",
                        "RECEBIDO NA OBRA",
                        "SERVIÇO",
                        "COMPRA DIRETA",
                        "CORREÇÃO DE PROCESSO",
                        "ATENDIDO",
                        "ATENDIDO PARCIALMENTE",
                        "REJEITADO",
                        "APROVADO",
                        "BLOQUEADO",
                        "PENDENTE DE APROVAÇÃO"
                    ]
                    lista_historico_status = sorted(list(set(status_existentes + status_oficiais)))

                    opcoes_logistica = [
                        "RETIRADO DO ALMOXARIFADO SEDE",
                        "ENTREGUE NO PEA",
                        "A CAMINHO DA OBRA",
                        "ENTREGUE NA OBRA"
                    ]

                    # Autosize: calcula a largura (px) de cada coluna a partir do
                    # conteudo REAL da busca atual (nao do heuristico do grid, que
                    # so olha o cabecalho e pode ficar "grudado" numa largura
                    # antiga entre reruns) - roda de novo a cada busca/edicao.
                    larguras_colunas = {}
                    for col_config in DICIONARIO_COLUNAS_EXATAS:
                        nome_tela = col_config["tela"]
                        if nome_tela not in df_painel.columns:
                            continue
                        serie_txt = df_painel[nome_tela].astype(str)
                        maior_valor = serie_txt.map(len).max() if not serie_txt.empty else 0
                        maior_len = max(int(maior_valor or 0), len(nome_tela))
                        larguras_colunas[nome_tela] = max(70, min(int(maior_len * 7.5) + 40, 380))
                    larguras_colunas["Logística"] = max(larguras_colunas.get("Logística", 0), max(len(o) for o in opcoes_logistica) * 7.5 + 40)
                    larguras_colunas["Status"] = max(larguras_colunas.get("Status", 0), max(len(o) for o in lista_historico_status) * 7.5 + 40) if lista_historico_status else larguras_colunas.get("Status", 120)
                    if mostrar_sla:
                        for nome_sla in ("Sla Pagamento", "Sla Entrega"):
                            serie_txt = df_painel[nome_sla].astype(str)
                            maior_len = max(int(serie_txt.map(len).max() or 0), len(nome_sla))
                            larguras_colunas[nome_sla] = max(70, min(int(maior_len * 7.5) + 40, 380))

                    for col_config in DICIONARIO_COLUNAS_EXATAS:
                        nome_tela = col_config["tela"]
                        tipo_campo = col_config["tipo"]
                        largura_px = int(larguras_colunas.get(nome_tela, 120))
                        rotulo_tela = nome_tela.replace(" Pc", " PC")

                        if st.session_state.autenticado:
                            dep = st.session_state.departamento_ativo
                            if dep == "logistica":
                                if nome_tela == "Logística":
                                    configuracao_colunas_tela[nome_tela] = st.column_config.SelectboxColumn(
                                        rotulo_tela, options=opcoes_logistica, required=False, width=largura_px
                                    )
                                elif nome_tela == "Data Logística":
                                    configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, disabled=False, width=largura_px)
                                else:
                                    configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, disabled=True, width=largura_px)
                            elif dep == "gestor":
                                # Gestor visualiza e edita tudo, sem restrição de campo
                                if nome_tela == "Status":
                                    configuracao_colunas_tela[nome_tela] = st.column_config.SelectboxColumn(
                                        rotulo_tela, options=lista_historico_status, required=True, width=largura_px
                                    )
                                elif nome_tela == "Logística":
                                    configuracao_colunas_tela[nome_tela] = st.column_config.SelectboxColumn(
                                        rotulo_tela, options=opcoes_logistica, required=False, width=largura_px
                                    )
                                else:
                                    configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, disabled=False, width=largura_px)
                            else:
                                # "Entrega" fica de fora de proposito - so a base (import do Totvs)
                                # preenche esse campo agora, o operador nao digita mais na mao.
                                campos_permitidos_compras = ["Status", "Envio Pc", "Pagamento Pc", "Previsão De Entrega", "NF Remessa"]
                                if nome_tela in campos_permitidos_compras:
                                    if nome_tela == "Status":
                                        configuracao_colunas_tela[nome_tela] = st.column_config.SelectboxColumn(
                                            rotulo_tela, options=lista_historico_status, required=True, width=largura_px
                                        )
                                    else:
                                        configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, disabled=False, width=largura_px)
                                else:
                                    configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, disabled=True, width=largura_px)
                        else:
                            if nome_tela == "Status":
                                configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, alignment="center", width=largura_px)
                            else:
                                configuracao_colunas_tela[nome_tela] = st.column_config.Column(rotulo_tela, disabled=True, width=largura_px)

                    configuracao_colunas_tela["_row_idx"] = None

                    if mostrar_sla:
                        for nome_sla in ("Sla Pagamento", "Sla Entrega"):
                            configuracao_colunas_tela[nome_sla] = st.column_config.Column(
                                nome_sla, disabled=True, width=int(larguras_colunas.get(nome_sla, 90)),
                                help="Dias corridos - calculado automaticamente"
                            )

                    if st.session_state.autenticado:
                        # A key inclui uma "impressao digital" das linhas realmente
                        # exibidas (hash dos _row_idx) - nao so o contador manual.
                        # Descobri um bug real assim: se o usuario pesquisa A (15
                        # linhas), depois pesquisa B (1 linha) SEM que o contador
                        # mude por algum motivo, o widget (mesma key) pode manter
                        # de um render pro outro um edited_rows["posicao 0"] que
                        # pertencia a uma linha de A, e aplicar essa edicao na
                        # linha ERRADA que agora esta na posicao 0 de B. Com a
                        # impressao digital, qualquer mudanca no CONJUNTO de linhas
                        # exibidas (nova busca, nova ordenacao, novo import) sempre
                        # forca uma key nova e portanto um widget "zerado".
                        fingerprint_linhas = hash(tuple(df_painel["_row_idx"].tolist()))
                        chave_editor = f"editor_painel_compras_{fingerprint_linhas}_{st.session_state.editor_key_counter}"
                        edited_df = st.data_editor(
                            df_painel,
                            use_container_width=True,
                            hide_index=True,
                            column_config=configuracao_colunas_tela,
                            key=chave_editor
                        )

                        # SALVAMENTO - le direto do estado interno do widget
                        # (session_state[chave_editor]["edited_rows"]), NAO do
                        # dataframe "edited_df" devolvido por st.data_editor.
                        # E um bug conhecido e documentado do Streamlit
                        # (streamlit/streamlit#7749, #7868, #7354): o dataframe
                        # devolvido fica "um ciclo atrasado" quando a edicao e
                        # seguida rapido por outro widget (o botao Salvar),
                        # reportando falsamente "nenhuma alteracao" mesmo com
                        # uma edicao real na tela. O dict edited_rows nao sofre
                        # desse atraso - e a fonte que o proprio Streamlit usa
                        # pra reconstruir o dataframe devolvido, entao ler
                        # direto daqui e mais confiavel. Bonus: as chaves de
                        # edited_rows sao a POSIÇÃO na tabela como foi passada
                        # pro editor (df_painel), imune a qualquer ordenacao
                        # que o usuario aplique clicando num cabecalho de coluna.
                        if btn_salvar_dados:
                            estado_editor = st.session_state.get(chave_editor, {})
                            edited_rows = estado_editor.get("edited_rows", {})

                            if not edited_rows:
                                st.info("ℹ️ Nenhuma alteração foi realizada para salvar.")
                            else:
                                # Datas fora do formato DD/MM/AAAA (ex: "5/6/2026", "05/06/26") sao
                                # corrigidas automaticamente antes de salvar - so bloqueia o save se
                                # o texto digitado nem der pra reconhecer como data nenhuma.
                                colunas_de_data_tela = ["Emissão Pc", "Aprovação Pc", "Envio Pc", "Previsão De Entrega", "Entrega", "Data Logística"]
                                data_invalida_encontrada = False
                                campo_data_invalido = None
                                for mudancas in edited_rows.values():
                                    for col_dt in colunas_de_data_tela:
                                        if col_dt in mudancas:
                                            val_novo_dt = str(mudancas[col_dt])
                                            if not validar_formato_data(val_novo_dt):
                                                val_corrigido = formatar_para_dd_mm_aaaa(val_novo_dt)
                                                if validar_formato_data(val_corrigido):
                                                    mudancas[col_dt] = val_corrigido
                                                else:
                                                    data_invalida_encontrada = True
                                                    campo_data_invalido = (col_dt, val_novo_dt)
                                    if data_invalida_encontrada:
                                        break

                                if data_invalida_encontrada:
                                    col_dt, valor_ruim = campo_data_invalido
                                    st.markdown(f'<div class="custom-error-red">⚠️ Erro: O campo <b>{col_dt}</b> tem o valor "<b>{valor_ruim}</b>", que não é reconhecível como data. Nenhuma alteração foi salva. Corrija para o formato <b>DD/MM/AAAA</b> antes de salvar.</div>', unsafe_allow_html=True)
                                else:
                                    try:
                                        client, creds_dict = obter_client_gspread()
                                        email_servico = creds_dict.get("client_email", "desconhecido")

                                        spreadsheet = client.open_by_key(FILE_ID)
                                        try:
                                            worksheet = spreadsheet.worksheet("Pedidos")
                                        except:
                                            worksheet = spreadsheet.get_worksheet(0)

                                        dados_planilha = worksheet.get_all_values()
                                        cabecalho_bruto = dados_planilha[0]
                                        cabecalho_map = {c.upper().strip().replace('Í', 'I').replace('Ã', 'A').replace('Ç', 'C'): i + 1 for i, c in enumerate(cabecalho_bruto)}

                                        alteracoes_detectadas = 0
                                        detalhes_gravados = []
                                        divergencias = []
                                        for posicao, mudancas in edited_rows.items():
                                            linha_df = df_painel.iloc[int(posicao)]
                                            linha_planilha = int(linha_df["_row_idx"])
                                            if linha_planilha >= SENTINELA_ROW_IDX_EM_COTACAO:
                                                # Linha sintetica "Em Cotação" (Solicitação sem
                                                # Pedido ainda) - nao existe na aba Pedidos, nunca salva.
                                                continue
                                            pedido_num = str(linha_df.get("Pedido", "")).strip()
                                            for col, valor_novo in mudancas.items():
                                                col_config_item = next((item for item in DICIONARIO_COLUNAS_EXATAS if item["tela"] == col), None)
                                                if not col_config_item:
                                                    continue
                                                col_index = None
                                                for alt in col_config_item["planilha"]:
                                                    alt_clean = alt.upper().strip().replace('Í', 'I').replace('Ã', 'A').replace('Ç', 'C')
                                                    col_index = cabecalho_map.get(alt_clean)
                                                    if col_index:
                                                        break

                                                if col_index:
                                                    worksheet.update_cell(linha_planilha, col_index, str(valor_novo))
                                                    # Confere na hora se realmente ficou gravado - sem
                                                    # isso o painel podia dizer "sucesso" mesmo que a
                                                    # escrita nao tivesse pego por algum motivo.
                                                    valor_conferido = worksheet.cell(linha_planilha, col_index).value
                                                    if str(valor_conferido or "").strip() != str(valor_novo).strip():
                                                        divergencias.append(
                                                            f"Pedido {pedido_num} — {col}: tentei gravar **{valor_novo}**, "
                                                            f"mas a planilha ainda mostra \"{valor_conferido}\" (linha {linha_planilha})"
                                                        )
                                                    else:
                                                        alteracoes_detectadas += 1
                                                        detalhes_gravados.append(f"Pedido {pedido_num} — {col}: **{valor_novo}**")

                                        if divergencias:
                                            st.markdown(
                                                '<div class="custom-error-red">⚠️ A gravação não foi confirmada na planilha:<br>'
                                                + "<br>".join(divergencias)
                                                + '<br>Tente novamente e avise o suporte se persistir.</div>',
                                                unsafe_allow_html=True,
                                            )
                                        elif alteracoes_detectadas > 0:
                                            lista_detalhes = "\n".join(f"- {item}" for item in detalhes_gravados)
                                            st.session_state.msg_salvar_sucesso = (
                                                f"✅ {alteracoes_detectadas} alteração(ões) gravada(s) e conferida(s) na planilha!\n\n{lista_detalhes}"
                                            )
                                            st.session_state.editor_key_counter += 1
                                            st.cache_data.clear()
                                            # Sem isso a tabela continuava mostrando o valor ANTIGO
                                            # apos salvar - limpar so o cache do decorador nao bastava,
                                            # dados_globais e guardado a parte na sessao e so recarrega
                                            # se estiver ausente/vazio.
                                            del st.session_state.dados_globais
                                            st.rerun()
                                        else:
                                            st.info("ℹ️ Nenhuma alteração foi realizada para salvar.")

                                    except Exception as e:
                                        erro_str = str(e)
                                        if "403" in erro_str or "permission" in erro_str.lower():
                                            st.error(f"❌ Erro 403 (Permissão Negada). Verifique se o e-mail da conta de serviço **{email_servico}** está adicionado como **Editor** na planilha.")
                                        else:
                                            st.error(f"❌ Erro ao gravar: {e}")
                    else:
                        st.dataframe(
                            df_painel.drop(columns=["_row_idx"], errors="ignore"), 
                            use_container_width=True, 
                            hide_index=True, 
                            column_config=configuracao_colunas_tela
                        )
                else:
                    st.markdown('<div class="custom-error-red custom-empty-state">⚠️ Nenhum registro correspondente encontrado com os filtros informados.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="custom-error-red custom-empty-state">⚠️ Nenhum registro correspondente encontrado.</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="custom-error-red">⚠️ Erro ao processar os dados da busca: {e}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="custom-welcome-salutation">👋 Olá! Seja bem-vindo ao Portal de Gestão de Compras. Utilize os Filtros Avançados acima para pesquisar.</div>', unsafe_allow_html=True)

# 10. RODAPÉ INSTITUCIONAL
renderizar_rodape()
