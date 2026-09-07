import streamlit as st
import pandas as pd
import gspread

from comum import (
    FILE_ID,
    aplicar_estilos,
    renderizar_cabecalho,
    renderizar_rodape,
    inicializar_sessao_login,
    renderizar_popup_login,
    obter_client_gspread,
    _ler_aba_como_df,
    formatar_para_dd_mm_aaaa,
    gerar_bytes_excel,
)

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Painel do Comprador | Parente Andrade",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. ESTILOS COMPARTILHADOS (mesmo visual do Portal Gestão de Compras)
aplicar_estilos()

ABA_SOLICITACOES = "Solicitacoes"

# 3. DICIONÁRIO DE COLUNAS DA ABA "Solicitacoes"
DICIONARIO_COLUNAS_SC = [
    {"planilha": ["CENTRO DE CUSTO"], "tela": "Centro De Custo", "tipo": "texto"},
    {"planilha": ["DESC CENTRO DE CUSTO"], "tela": "Desc Centro De Custo", "tipo": "texto"},
    {"planilha": ["SOLICITAÇÃO", "SOLICITACAO"], "tela": "Solicitação", "tipo": "texto"},
    {"planilha": ["ITEM SC"], "tela": "Item Sc", "tipo": "texto"},
    {"planilha": ["FILIAL"], "tela": "Filial", "tipo": "texto"},
    {"planilha": ["PRODUTO"], "tela": "Produto", "tipo": "produto"},
    {"planilha": ["DESCRICAO"], "tela": "Descrição", "tipo": "texto"},
    {"planilha": ["UM"], "tela": "Um", "tipo": "texto"},
    {"planilha": ["QTD"], "tela": "Qtd", "tipo": "numero"},
    {"planilha": ["QTD EM PEDIDO"], "tela": "Qtd Em Pedido", "tipo": "numero"},
    {"planilha": ["COTAÇÃO", "COTACAO"], "tela": "Cotação", "tipo": "texto"},
    {"planilha": ["PEDIDO"], "tela": "Pedido", "tipo": "pedido"},
    {"planilha": ["DATA EMISSAO"], "tela": "Data Emissão", "tipo": "data"},
    {"planilha": ["DATA APROVACAO"], "tela": "Data Aprovação", "tipo": "data"},
]

# Único campo que o comprador preenche manualmente por aqui - o resto vem
# direto da importação do Protheus (ver "Importar Arquivo" no painel de Pedidos).
CAMPOS_EDITAVEIS_COMPRAS = ["Cotação"]

OPCOES_STATUS_SC = [
    "AGUARDANDO COTAÇÃO",
    "EM COTAÇÃO",
    "EM PEDIDO",
    "ATENDIDA PARCIALMENTE",
    "ATENDIDA",
]


def normalizar_nome_coluna(nome) -> str:
    return str(nome).upper().strip().replace('Í', 'I').replace('Ã', 'A').replace('Ç', 'C')


def _numero(valor) -> float:
    try:
        return float(str(valor).replace(',', '.').strip() or 0)
    except ValueError:
        return 0.0


def calcular_status_solicitacao(qtd, qtd_pedido, pedido, cotacao) -> str:
    qtd_num = _numero(qtd)
    qtd_pedido_num = _numero(qtd_pedido)
    if str(pedido).strip():
        if qtd_num > 0 and qtd_pedido_num >= qtd_num:
            return "ATENDIDA"
        if qtd_pedido_num > 0:
            return "ATENDIDA PARCIALMENTE"
        return "EM PEDIDO"
    if str(cotacao).strip():
        return "EM COTAÇÃO"
    return "AGUARDANDO COTAÇÃO"


# 4. CARREGAMENTO SEGURO DIRETO DA ABA "Solicitacoes"
@st.cache_data(ttl=60)
def carregar_solicitacoes():
    try:
        client, _ = obter_client_gspread()
        spreadsheet = client.open_by_key(FILE_ID)
        return _ler_aba_como_df(spreadsheet, ABA_SOLICITACOES)
    except Exception as e:
        st.session_state.erro_tecnico_sc = f"Erro Gspread: {str(e)}"
        return pd.DataFrame()


if 'dados_solicitacoes' not in st.session_state or st.session_state.dados_solicitacoes.empty:
    st.session_state.dados_solicitacoes = carregar_solicitacoes()

df_sc_bruto = st.session_state.dados_solicitacoes

# Estados de sessão (login compartilhado com o painel de Pedidos; filtros e
# gaveta com chaves próprias pra não interferir no outro painel)
inicializar_sessao_login()
if "cmp_filtro_sc_val" not in st.session_state:
    st.session_state.cmp_filtro_sc_val = ""
if "cmp_filtro_cc_val" not in st.session_state:
    st.session_state.cmp_filtro_cc_val = ""
if "cmp_filtro_status_val" not in st.session_state:
    st.session_state.cmp_filtro_status_val = "Todos"
if "cmp_filtro_data_val" not in st.session_state:
    st.session_state.cmp_filtro_data_val = ()
if "cmp_gaveta_aberta" not in st.session_state:
    st.session_state.cmp_gaveta_aberta = True

# 5. CABEÇALHO INTEGRADO
renderizar_cabecalho("Painel do Comprador")

# 6. JANELA POPUP DISCRETA DE LOGIN (mesma lógica do painel de Pedidos)
renderizar_popup_login()


def aplicar_filtros_sc(df):
    """Filtra pelos campos que já existem na planilha (Solicitação, Centro de
    Custo, Data de Emissão) - o filtro de Status é aplicado depois, sobre a
    coluna calculada em montar_df_painel_sc."""
    df_final = df.copy()
    colunas_normalizadas = {normalizar_nome_coluna(c): c for c in df_final.columns}

    if st.session_state.cmp_filtro_sc_val:
        termo = str(st.session_state.cmp_filtro_sc_val).strip()
        col = colunas_normalizadas.get("SOLICITACAO")
        if col:
            df_final = df_final[df_final[col].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.contains(termo, na=False)]

    if st.session_state.cmp_filtro_cc_val:
        termo = st.session_state.cmp_filtro_cc_val.strip().lower()
        col = colunas_normalizadas.get("CENTRO DE CUSTO")
        if col:
            df_final = df_final[df_final[col].astype(str).str.lower().str.contains(termo, na=False)]

    if st.session_state.cmp_filtro_data_val and len(st.session_state.cmp_filtro_data_val) == 2:
        if st.session_state.cmp_filtro_data_val[0] is not None and st.session_state.cmp_filtro_data_val[1] is not None:
            col = colunas_normalizadas.get("DATA EMISSAO")
            if col:
                datas_convertidas = pd.to_datetime(df_final[col], errors='coerce', format='mixed', dayfirst=True).dt.date
                df_final = df_final[(datas_convertidas >= st.session_state.cmp_filtro_data_val[0]) & (datas_convertidas <= st.session_state.cmp_filtro_data_val[1])]

    return df_final, colunas_normalizadas


def montar_df_painel_sc(df_final, colunas_normalizadas):
    """Recebe o df já filtrado e monta o df_painel (colunas da tela), com a
    coluna Status calculada a partir de Pedido/Qtd Em Pedido/Cotação."""
    df_painel = pd.DataFrame(index=df_final.index)

    for col_config in DICIONARIO_COLUNAS_SC:
        nome_tela = col_config["tela"]
        tipo_campo = col_config["tipo"]

        col_real = None
        for alt in col_config["planilha"]:
            alt_clean = normalizar_nome_coluna(alt)
            for c_up, c_real in colunas_normalizadas.items():
                if c_up == alt_clean:
                    col_real = c_real
                    break
            if col_real:
                break

        if col_real:
            valores = df_final[col_real]
            if tipo_campo == "data":
                df_painel[nome_tela] = valores.apply(formatar_para_dd_mm_aaaa)
            elif tipo_campo in ("pedido", "numero"):
                df_painel[nome_tela] = valores.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            elif tipo_campo == "produto":
                df_painel[nome_tela] = valores.apply(lambda v: str(v).split('.')[0].strip().zfill(10) if str(v).strip() and str(v).lower() != 'nan' else "")
            else:
                df_painel[nome_tela] = valores.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '').str.strip()
        else:
            df_painel[nome_tela] = ""

    df_painel["_row_idx"] = [idx + 2 for idx in df_final.index]

    df_painel["Status"] = [
        calcular_status_solicitacao(qtd, qtd_pedido, pedido, cotacao)
        for qtd, qtd_pedido, pedido, cotacao in zip(
            df_painel["Qtd"], df_painel["Qtd Em Pedido"], df_painel["Pedido"], df_painel["Cotação"]
        )
    ]
    colunas_ordenadas = ["Status"] + [c for c in df_painel.columns if c not in ("Status", "_row_idx")] + ["_row_idx"]
    df_painel = df_painel[colunas_ordenadas]

    for col in df_painel.columns:
        if col == "_row_idx":
            continue
        df_painel[col] = df_painel[col].astype(str).str.upper()

    return df_painel.dropna(how='all')


# 7. FILTROS
tem_busca_ativa = (
    st.session_state.cmp_filtro_sc_val
    or st.session_state.cmp_filtro_cc_val
    or st.session_state.cmp_filtro_status_val != "Todos"
    or bool(st.session_state.cmp_filtro_data_val)
)

relatorio_bytes = None
if tem_busca_ativa and not df_sc_bruto.empty:
    try:
        _df_final_preview, _colunas_preview = aplicar_filtros_sc(df_sc_bruto)
        if not _df_final_preview.empty:
            _df_painel_preview = montar_df_painel_sc(_df_final_preview, _colunas_preview)
            if st.session_state.cmp_filtro_status_val != "Todos":
                _df_painel_preview = _df_painel_preview[_df_painel_preview["Status"] == st.session_state.cmp_filtro_status_val]
            if not _df_painel_preview.empty:
                relatorio_bytes = gerar_bytes_excel(_df_painel_preview)
    except Exception:
        relatorio_bytes = None

rotulo_seta = "Filtros Avançados ▲" if st.session_state.cmp_gaveta_aberta else "Filtros Avançados ▼"

with st.expander(rotulo_seta, expanded=st.session_state.cmp_gaveta_aberta):
    with st.form("form_filtros_comprador", clear_on_submit=False):
        f1, f2, f3, f4 = st.columns(4)

        with f1:
            filtro_sc = st.text_input("Solicitação (SC):", value=st.session_state.cmp_filtro_sc_val, placeholder="Nº da SC...")
        with f2:
            filtro_cc = st.text_input("Centro de Custo:", value=st.session_state.cmp_filtro_cc_val, placeholder="Centro de custo...")
        with f3:
            idx_padrao = (["Todos"] + OPCOES_STATUS_SC).index(st.session_state.cmp_filtro_status_val) if st.session_state.cmp_filtro_status_val in (["Todos"] + OPCOES_STATUS_SC) else 0
            filtro_status = st.selectbox("Status:", options=["Todos"] + OPCOES_STATUS_SC, index=idx_padrao)
        with f4:
            filtro_data = st.date_input("Data de Emissão:", value=st.session_state.cmp_filtro_data_val, format="DD/MM/YYYY")

        st.write("")

        esp0, espb, b1, b2, b3, b4 = st.columns([1.6, 1, 1, 1, 1, 1])
        with esp0:
            st.markdown("&nbsp;", unsafe_allow_html=True)
        with espb:
            st.markdown("&nbsp;", unsafe_allow_html=True)
        with b1:
            btn_pesquisar = st.form_submit_button("🔍 Pesquisar", use_container_width=True, type="primary")
            if btn_pesquisar:
                st.session_state.cmp_filtro_sc_val = filtro_sc
                st.session_state.cmp_filtro_cc_val = filtro_cc
                st.session_state.cmp_filtro_status_val = filtro_status
                st.session_state.cmp_filtro_data_val = filtro_data
                st.session_state.cmp_gaveta_aberta = False
                st.rerun()

        with b2:
            btn_limpar = st.form_submit_button("❌ Limpar", use_container_width=True)
            if btn_limpar:
                st.session_state.cmp_filtro_sc_val = ""
                st.session_state.cmp_filtro_cc_val = ""
                st.session_state.cmp_filtro_status_val = "Todos"
                st.session_state.cmp_filtro_data_val = ()
                st.session_state.cmp_gaveta_aberta = True
                st.rerun()

        with b3:
            btn_atualizar = st.form_submit_button("🔄 Atualizar Banco", use_container_width=True)
            if btn_atualizar:
                st.cache_data.clear()
                st.session_state.dados_solicitacoes = carregar_solicitacoes()
                st.session_state.cmp_gaveta_aberta = True
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

# 8. AÇÕES DO PAINEL (Baixar Relatório / Salvar Alterações)
with st.container(key="acoes_painel_wrap"):
    if relatorio_bytes:
        st.download_button(
            label="📥 Baixar Relatório",
            data=relatorio_bytes,
            file_name="Relatorio_Solicitacoes_Filtro.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_baixar_relatorio_comprador",
        )

    pode_editar = st.session_state.autenticado and st.session_state.departamento_ativo in ("compras", "gestor")
    if pode_editar:
        btn_salvar_dados = st.button("💾 Salvar Alterações", type="primary", key="btn_salvar_comprador")
    else:
        btn_salvar_dados = False

# 9. MOTOR DE BUSCA
if tem_busca_ativa:
    if df_sc_bruto.empty:
        st.markdown('<div class="custom-error-red custom-empty-state">⚠️ Base de dados vazia. Clique em "🔄 Atualizar Banco" nos Filtros Avançados.</div>', unsafe_allow_html=True)
    else:
        df_final, colunas_normalizadas = aplicar_filtros_sc(df_sc_bruto)

        try:
            if not df_final.empty:
                df_painel = montar_df_painel_sc(df_final, colunas_normalizadas)

                if st.session_state.cmp_filtro_status_val != "Todos":
                    df_painel = df_painel[df_painel["Status"] == st.session_state.cmp_filtro_status_val]

                if not df_painel.empty:
                    txt_status = f"🔍 Registros Localizados ({len(df_painel)} itens)"
                    st.markdown(f'<div class="status-card">{txt_status}</div>', unsafe_allow_html=True)

                    configuracao_colunas_tela = {}
                    larguras_colunas = {}
                    for nome_tela in df_painel.columns:
                        if nome_tela == "_row_idx":
                            continue
                        serie_txt = df_painel[nome_tela].astype(str)
                        maior_valor = serie_txt.map(len).max() if not serie_txt.empty else 0
                        maior_len = max(int(maior_valor or 0), len(nome_tela))
                        larguras_colunas[nome_tela] = max(70, min(int(maior_len * 7.5) + 40, 380))
                    larguras_colunas["Status"] = max(larguras_colunas.get("Status", 0), max(len(o) for o in OPCOES_STATUS_SC) * 7.5 + 40)

                    for nome_tela in df_painel.columns:
                        if nome_tela == "_row_idx":
                            configuracao_colunas_tela[nome_tela] = None
                            continue
                        largura_px = int(larguras_colunas.get(nome_tela, 120))
                        if nome_tela == "Status":
                            configuracao_colunas_tela[nome_tela] = st.column_config.Column("Status", disabled=True, width=largura_px)
                        elif pode_editar and nome_tela in CAMPOS_EDITAVEIS_COMPRAS:
                            configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, disabled=False, width=largura_px)
                        else:
                            configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, disabled=True, width=largura_px)

                    if st.session_state.autenticado:
                        if "df_original_cache_comprador" not in st.session_state or st.session_state.get("atualizar_cache_editor_comprador", True):
                            st.session_state.df_original_cache_comprador = df_painel.copy()
                            st.session_state.atualizar_cache_editor_comprador = False

                        edited_df = st.data_editor(
                            df_painel,
                            use_container_width=True,
                            hide_index=True,
                            column_config=configuracao_colunas_tela,
                            key="editor_painel_comprador",
                        )

                        if btn_salvar_dados:
                            if "df_original_cache_comprador" in st.session_state:
                                df_orig = st.session_state.df_original_cache_comprador
                                alteracoes_detectadas = 0
                                try:
                                    client, creds_dict = obter_client_gspread()
                                    email_servico = creds_dict.get("client_email", "desconhecido")
                                    spreadsheet = client.open_by_key(FILE_ID)
                                    worksheet = spreadsheet.worksheet(ABA_SOLICITACOES)

                                    dados_planilha = worksheet.get_all_values()
                                    cabecalho_bruto = dados_planilha[0]
                                    cabecalho_map = {normalizar_nome_coluna(c): i + 1 for i, c in enumerate(cabecalho_bruto)}

                                    for idx in edited_df.index:
                                        linha_planilha = int(edited_df.loc[idx, "_row_idx"])
                                        for campo_tela in CAMPOS_EDITAVEIS_COMPRAS:
                                            valor_antigo = str(df_orig.loc[idx, campo_tela])
                                            valor_novo = str(edited_df.loc[idx, campo_tela])
                                            if valor_antigo == valor_novo:
                                                continue

                                            col_config_item = next((item for item in DICIONARIO_COLUNAS_SC if item["tela"] == campo_tela), None)
                                            if not col_config_item:
                                                continue
                                            col_index = None
                                            for alt in col_config_item["planilha"]:
                                                col_index = cabecalho_map.get(normalizar_nome_coluna(alt))
                                                if col_index:
                                                    break
                                            if col_index:
                                                worksheet.update_cell(linha_planilha, col_index, valor_novo)
                                                alteracoes_detectadas += 1

                                    if alteracoes_detectadas > 0:
                                        st.success(f"✅ {alteracoes_detectadas} alteração(ões) gravada(s) com sucesso na planilha!")
                                        st.session_state.df_original_cache_comprador = edited_df.copy()
                                        st.cache_data.clear()
                                        st.session_state.dados_solicitacoes = carregar_solicitacoes()
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
                            column_config=configuracao_colunas_tela,
                        )
                else:
                    st.markdown('<div class="custom-error-red custom-empty-state">⚠️ Nenhum registro correspondente encontrado com os filtros informados.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="custom-error-red custom-empty-state">⚠️ Nenhum registro correspondente encontrado.</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="custom-error-red">⚠️ Erro ao processar os dados da busca: {e}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="custom-welcome-salutation">👋 Olá! Seja bem-vindo ao Painel do Comprador. Utilize os Filtros Avançados acima para pesquisar as Solicitações.</div>', unsafe_allow_html=True)

# 10. RODAPÉ INSTITUCIONAL
renderizar_rodape()
