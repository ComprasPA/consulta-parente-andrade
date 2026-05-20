import streamlit as st
import pandas as pd
import base64
import re
from datetime import datetime, timedelta
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA (Interface limpa com barra recolhida)
st.set_page_config(
    page_title="Portal Gestão de Compras | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. FUNÇÃO LOGO
@st.cache_data(ttl=86400)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: 
        return None

base64_logo = get_base64_logo()

# 3. CSS MODERNIZADO (Controles visuais e destaque do Expander de Filtros)
st.markdown(f"""
    <style>
    /* Ocultar elementos padrão do Streamlit e zerar espaço do topo */
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    
    /* Remove o espacamento forcado no topo e nas laterais da pagina */
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }}
    
    /* Fundo geral suave e tipografia limpa */
    .stApp {{ 
        background-color: #f8fafc; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}
    
    /* Topo moderno forcando todos os elementos na mesma linha verticalmente alinhados */
    .header-modern {{
        background: #ffffff;
        padding: 16px 24px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 0px !important;
        margin-bottom: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
    }}
    
    /* Forca os elementos internos das colunas do Streamlit a centralizarem verticalmente */
    div[data-testid="column"] {{
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    
    /* Alinha o titulo a esquerda dentro da sua respectiva coluna */
    div[data-testid="column"]:nth-child(2) {{
        justify-content: flex-start !important;
    }}
    
    .portal-title {{ 
        color: #1e293b !important; 
        font-size: 40px !important; 
        font-weight: 800 !important; 
        margin: 0 !important;
        letter-spacing: -1px;
        line-height: 1;
        white-space: nowrap;
    }}
    
    /* Customizacao fina para campos de input, seletores, botoes e expander de filtros */
    div[data-testid="stVerticalBlock"] > div:has(input), 
    div[data-testid="stVerticalBlock"] > div:has(select),
    div[data-testid="stVerticalBlock"] > div:has(button) {{
        background-color: #ffffff; 
        padding: 2px 6px !important; 
        border-radius: 8px; 
        border: 1px solid #e2e8f0 !important;
        box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02);
        transition: border-color 0.2s;
        width: 100%;
    }}
    div[data-testid="stVerticalBlock"] > div:has(input):focus-within,
    div[data-testid="stVerticalBlock"] > div:has(select):focus-within {{
        border-color: #478c3b !important;
    }}
    
    /* MODIFICAÇÃO ATIVADA (SILVIO): Destaque absoluto no título do Expander */
    div[data-testid="stExpander"] {{
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        margin-bottom: 24px;
    }}
    
    /* Força a cor do texto do cabeçalho do expander para alta visibilidade */
    div[data-testid="stExpander"] summary p {{
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }}
    
    /* Cor de destaque quando o usuário passa o mouse por cima do botão de filtros */
    div[data-testid="stExpander"] summary:hover p {{
        color: #478c3b !important;
    }}
    
    /* Ajuste de largura do input de data nativo */
    div[data-testid="stDateInput"] {{
        width: 100%;
    }}
    
    /* Caixa padrao de sucesso (Registro Localizado) */
    .status-card {{ 
        background: #ffffff; 
        color: #1e293b; 
        padding: 16px 24px; 
        border-radius: 8px; 
        font-weight: 600; 
        font-size: 16px; 
        border-left: 5px solid #478c3b;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 16px;
        width: 100%;
    }}

    /* CAIXA AZUL: Para informacoes positivas */
    .custom-info-blue {{
        background-color: #1e40af !important;
        color: #ffffff !important;
        padding: 16px 24px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 16px;
        width: 100%;
        border-left: 5px solid #3b82f6;
    }}

    /* CAIXA VERMELHA: Para alertas/erros */
    .custom-error-red {{
        background-color: #fee2e2 !important;
        color: #991b1b !important;
        padding: 16px 24px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 16px;
        width: 100%;
        border-left: 5px solid #ef4444;
    }}

    /* SAUDACAO INICIAL */
    .custom-welcome-salutation {{
        background-color: #ffffff;
        color: #1e293b;
        padding: 32px 24px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 20px;
        text-align: center;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
        margin-top: 20px;
    }}
    
    /* Ajustes na visualizacao das tabelas */
    div[data-testid="stDataFrame"] {{
        background: #ffffff;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }}
    
    /* Impedir quebras de palavras e truncamento nos titulos das colunas */
    div[data-testid="stDataFrame"] table th {{
        white-space: nowrap !important;
        min-width: max-content !important;
    }}
    </style>
    """, unsafe_allow_html=True)


# ==========================================
# BACKEND: CARREGAMENTO DOS DADOS
# ==========================================
@st.cache_data(ttl=60)
def carregar_dados_seguros():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]
        return df_pc
    except Exception as e:
        return pd.DataFrame()

df_pc = carregar_dados_seguros()


# ==========================================
# 4. CABEÇALHO INTEGRADO (CAIXA DE BUSCA PRINCIPAL SEMPRE VISÍVEL)
# ==========================================
st.markdown('<div class="header-modern">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.1, 5.7, 3.2])

with c1:
    if base64_logo: 
        st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:120px; display:block; margin:auto 0;">', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="portal-title">Portal Gestão de Compras</p>', unsafe_allow_html=True)
with c3:
    busca = st.text_input("", placeholder="🔍 Localizar SC, Pedido ou CC...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# GAVETA RETRÁTIL OPERACIONAL COM CABEÇALHO DESTACADO VIA CSS
# ==========================================
with st.expander("⚙️ Filtros Avançados (Status, Emissão e Atualização)", expanded=False):
    f_col1, f_col2, f_col3 = st.columns([3.5, 3.5, 3.0])
    
    with f_col1:
        col_status_verificacao = next((c for c in df_pc.columns if "STATUS" in c.upper()), None) if not df_pc.empty else None
        if col_status_verificacao:
            lista_status = ["Todos"] + sorted([str(x).strip() for x in df_pc[col_status_verificacao].unique() if str(x).strip() != ""])
        else:
            lista_status = ["Todos"]
        filtro_status = st.selectbox("Filtrar por Status Operacional:", options=lista_status, index=0)
        
    with f_col2:
        data_hoje = datetime.now().date()
        trinta_dias_atras = data_hoje - timedelta(days=30)
        filtro_data = st.date_input("Filtrar por Período de Emissão:", value=(trinta_dias_atras, data_hoje), format="DD/MM/YYYY")
        
    with f_col3:
        st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True) 
        if st.button("🔄 Atualizar Dados da Planilha", use_container_width=True):
            st.cache_data.clear()
            st.rerun()


# ==========================================
# 5. ESTRUTURA DE COLUNAS REORGANIZADA
# ==========================================
DICIONARIO_COLUNAS_EXATAS = [
    {"planilha": "STATUS", "tela": "STATUS", "tipo": "texto"},
    {"planilha": "Centro de Custo (CC)", "tela": "Centro de Custo (CC)", "tipo": "texto"},
    {"planilha": "Nº Solicitação (SC)", "tela": "Nº Solicitação (SC)", "tipo": "texto"},
    {"planilha": "Nº Pedido (PC)", "tela": "Nº Pedido (PC)", "tipo": "pedido"},   
    {"planilha": "Condição Pagamento", "tela": "Condição Pagamento", "tipo": "texto"},
    {"planilha": "Data Emissao", "tela": "Emissão", "tipo": "data"},
    {"planilha": "Data Liberação", "tela": "Aprovação", "tipo": "data"},
    {"planilha": "Envio", "tela": "Envio", "tipo": "data"},
    {"planilha": "Pagamento", "tela": "Pagamento", "tipo": "texto"}, 
    {"planilha": "Previsão de entrega", "tela": "Previsão de entrega", "tipo": "data"},
    {"planilha": "Entrega", "tela": "Entrega", "tipo": "data"},
    {"planilha": "Fornecedor", "tela": "Fornecedor", "tipo": "texto"},
    {"planilha": "Produto", "tela": "Produto", "tipo": "produto"},                 
    {"planilha": "Descricao", "tela": "Descrição", "tipo": "texto"},
    {"planilha": "UM", "tela": "UM", "tipo": "texto"},
    {"planilha": "Qtd", "tela": "Qtd", "tipo": "numero"},
    {"planilha": "Preço Unitário", "tela": "Preço Unitário", "tipo": "moeda"},
    {"planilha": "Valor Total", "tela": "Valor Total", "tipo": "moeda"}
]

def ajustar_zeros_protheus(valor, tamanho_alvo):
    val_limpo = str(valor).split('.')[0].strip()
    if val_limpo and val_limpo.lower() != 'nan' and val_limpo != '0' and val_limpo != '':
        return val_limpo.zfill(tamanho_alvo)
    return ""

def converter_para_numerico(valor):
    if not valor or str(valor).lower() == 'nan' or str(valor).strip() == '':
        return ""
    dado = str(valor).replace('.', '').replace(',', '.').strip()
    try:
        return float(dado)
    except:
        return ""

def formatar_para_dd_mm_aa(valor):
    txt = str(valor).strip()
    if txt == "" or txt.lower() in ["nan", "none", "0", "n/a"]:
        return txt
    try:
        return pd.to_datetime(txt, errors='coerce', format='mixed').strftime('%d/%m/%y')
    except:
        return txt


# ==========================================
# 6. MOTOR DE BUSCA DIRECIONADO OPERACIONAL
# ==========================================
if busca:
    termo_busca = busca.strip()
    termo_numerico = re.sub(r'[^0-9]', '', termo_busca)
    valor_numerico_inteiro = int(termo_numerico) if termo_numerico else 0
    tamanho_digitos = len(termo_numerico)
    
    df_final = pd.DataFrame()
    modo_centro_custo = False
    
    try:
        if not df_pc.empty:
            # Passo 1: Varredura por Centro de Custo (4 dígitos)
            if tamanho_digitos == 4:
                modo_centro_custo = True
                col_busca_pc = next((c for c in df_pc.columns if "CENTRO" in c.upper() or "CC" in c.upper() or "CUSTO" in c.upper()), None)
                if col_busca_pc:
                    df_final = df_pc[df_pc[col_busca_pc].astype(str).str.strip().str.contains(re.escape(termo_busca), flags=re.IGNORECASE, regex=True, na=False)].copy()
            
            # Passo 2: Varredura normal para Pedidos (PC) ou Solicitações (SC)
            else:
                if termo_numerico:
                    padrao_regex = f"^{int(termo_numerico)}(\\.0)?$"
                else:
                    padrao_regex = re.escape(termo_busca)
                    
                if valor_numerico_inteiro >= 170000:
                    col_busca_pc = next((c for c in df_pc.columns if "PEDID" in c.upper() or "PC" in c.upper()), None)
                else:
                    col_busca_pc = next((c for c in df_pc.columns if "SOLICITACAO" in c.upper() or "SC" in c.upper()), None)
                    
                if not col_busca_pc:
                    col_busca_pc = next((c for c in df_pc.columns if "SOLICITACAO" in c.upper() or "SC" in c.upper()), df_pc.columns[0])

                res_pc = df_pc[df_pc[col_busca_pc].astype(str).str.strip().str.contains(padrao_regex, flags=re.IGNORECASE, regex=True, na=False)]
                if not res_pc.empty:
                    df_final = res_pc.copy()

            # Execução dos Filtros da Gaveta Oculta (Status)
            if not df_final.empty and filtro_status != "Todos" and col_status_verificacao:
                df_final = df_final[df_final[col_status_verificacao].astype(str).str.strip() == filtro_status]

            # Execução dos Filtros da Gaveta Oculta (Datas de Emissão)
            if not df_final.empty and filtro_data and len(filtro_data) == 2:
                col_emissao_original = next((c for c in df_pc.columns if "EMISSAO" in c.upper()), None)
                if col_emissao_original:
                    datas_convertidas = pd.to_datetime(df_final[col_emissao_original], errors='coerce', format='mixed').dt.date
                    data_inicio = filtro_data[0]
                    data_fim = filtro_data[1]
                    df_final = df_final[(datas_convertidas >= data_inicio) & (datas_convertidas <= data_fim)]

        # ---- MONTAGEM DA LISTA TRATADA PARA EXIBIÇÃO ----
        if not df_final.empty:
            df_painel = pd.DataFrame(index=df_final.index)
            
            for col_config in DICIONARIO_COLUNAS_EXATAS:
                nome_original_planilha = col_config["planilha"]
                nome_exibicao_tela = col_config["tela"]
                tipo_campo = col_config["tipo"]
                
                col_real = nome_original_planilha
                if col_real in df_final.columns:
                    valores_originais = df_final[col_real]
                    
                    if tipo_campo == "data":
                        datas_limpas = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                        datas_limpas = datas_limpas.replace(['nan', 'NONE', '', '0'], '')
                        df_painel[nome_exibicao_tela] = datas_limpas
                    
                    elif tipo_campo == "pedido":
                        df_painel[nome_exibicao_tela] = valores_originais.apply(lambda val: ajustar_zeros_protheus(val, 6))
                    
                    elif tipo_campo == "produto":
                        df_painel[nome_exibicao_tela] = valores_originais.apply(lambda val: ajustar_zeros_protheus(val, 10))
                    
                    elif tipo_campo in ["moeda", "numero"]:
                        df_painel[nome_exibicao_tela] = valores_originais.apply(converter_para_numerico)
                    
                    else:
                        df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '').str.strip()
                else:
                    if nome_exibicao_tela == "Nº Solicitação (SC)" and valor_numerico_inteiro < 170000 and not modo_centro_custo:
                        df_painel[nome_exibicao_tela] = ajustar_zeros_protheus(busca, 6) if busca.strip().isdigit() else busca.strip()
                    elif nome_exibicao_tela == "Nº Pedido (PC)" and valor_numerico_inteiro >= 170000 and not modo_centro_custo:
                        df_painel[nome_exibicao_tela] = ajustar_zeros_protheus(busca, 6) if busca.strip().isdigit() else busca.strip()
                    elif nome_exibicao_tela == "Centro de Custo (CC)" and modo_centro_custo:
                        df_painel[nome_exibicao_tela] = busca.strip()
                    else:
                        df_painel[nome_exibicao_tela] = ""

            # ---- REGRAS OPERACIONAIS INTER-COLUNAS ----
            if "Previsão de entrega" in df_painel.columns and "Entrega" in df_painel.columns:
                mascara_vazia = (df_painel["Previsão de entrega"] == "") | (df_painel["Previsão de entrega"].isna())
                df_painel.loc[mascara_vazia, "Previsão de entrega"] = df_painel.loc[mascara_vazia, "Entrega"]

            if "Pagamento" in df_painel.columns and "Condição Pagamento" in df_painel.columns:
                condicao_normalizada = df_painel["Condição Pagamento"].astype(str).str.upper().str.strip()
                mascara_na = (
                    (~condicao_normalizada.str.contains("A VISTA", na=False)) & 
                    (~condicao_normalizada.str.contains("ENT", na=False)) & 
                    (~condicao_normalizada.str.contains("VENCIDO", na=False)) & 
                    (~condicao_normalizada.str.contains("PAGO", na=False))
                )
                df_painel.loc[mascara_na, "Pagamento"] = "N/A"

            # Formatacao das colunas de datas para o padrao resumido
            colunas_para_formatar = ["Envio", "Pagamento", "Previsão de entrega", "Entrega", "Emissão", "Aprovação"]
            for col_data in colunas_para_formatar:
                if col_data in df_painel.columns:
                    df_painel[col_data] = df_painel[col_data].apply(formatar_para_dd_mm_aa)

            # Ocultar linhas de pagamento liquidado como "PAGO"
            if "Condição Pagamento" in df_painel.columns:
                df_painel = df_painel[~df_painel["Condição Pagamento"].astype(str).str.upper().str.contains("PAGO", na=False)]

            df_painel = df_painel.dropna(how='all')

            if not df_painel.empty:
                txt_status = f"🔍 Registros Ativos para o Centro de Custo: {termo_busca}" if modo_centro_custo else "🔍 Registro Localizado na Base de Pedidos Firme"
                if filtro_status != "Todos":
                    txt_status += f" (Status: {filtro_status})"
                if filtro_data and len(filtro_data) == 2:
                    txt_status += f" (Período: {filtro_data[0].strftime('%d/%m/%y')} até {filtro_data[1].strftime('%d/%m/%y')})"
                    
                st.markdown(f'<div class="status-card">{txt_status}</div>', unsafe_allow_html=True)
                
                c_down, _ = st.columns([2.5, 7.5])
                with c_down:
                    out = BytesIO()
                    with pd.ExcelWriter(out, engine='xlsxwriter') as wr: 
                        df_painel.to_excel(wr, index=False)
                    st.download_button(
                        label="📥 Extrair Relatório Operacional",
                        data=out.getvalue(),
                        file_name=f"Relatorio_Compras_{termo_busca}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                st.write("")

                # ---- 7. CONFIGURAÇÃO VISUAL DE ALINHAMENTO ----
                configuracao_colunas_tela = {}
                for col_config in DICIONARIO_COLUNAS_EXATAS:
                    nome_tela = col_config["tela"]
                    tipo_campo = col_config["tipo"]
                    
                    if nome_tela == "STATUS":
                        configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, alignment="center", width=None)
                    elif tipo_campo == "moeda":
                        configuracao_colunas_tela[nome_tela] = st.column_config.NumberColumn(nome_tela, format="R$ %.2f", alignment="right", width=None)
                    elif tipo_campo == "numero":
                        configuracao_colunas_tela[nome_tela] = st.column_config.NumberColumn(nome_tela, alignment="right", width=None)
                    else:
                        if nome_tela in ["Fornecedor", "Descrição"]:
                            configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, alignment="left", width=None)
                        else:
                            configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, alignment="right", width=None)

                # Estilização absoluta via Pandas Styler para centralizar cabeçalho e dados de STATUS
                tabela_estilizada = df_painel.style.set_table_styles([
                    {'selector': 'th.col_heading.level0.col0', 'props': [('text-align', 'center !important'), ('justify-content', 'center !important')]},
                    {'selector': 'td.col0', 'props': [('text-align', 'center !important')]}
                ], overwrite=False)
                
                st.dataframe(tabela_estilizada, use_container_width=True, hide_index=True, column_config=configuracao_colunas_tela)
            else:
                st.markdown('<div class="custom-info-blue">ℹ️ Nenhum registro ativo atende aos critérios de busca e aos filtros selecionados.</div>', unsafe_allow_html=True)
        else:
            if modo_centro_custo:
                st.markdown(f'<div class="custom-error-red">⚠️ O Centro de Custo \'{termo_busca}\' informado não possui registros correspondentes.</div>', unsafe_allow_html=True)
            elif valor_numerico_inteiro >= 170000:
                st.markdown('<div class="custom-error-red">⚠️ Seu pedido de compras não foi localizado, entre em contato com o comprador.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="custom-info-blue">⏳ Sua Solicitação ainda está em cotação. Logo estaremos finalizando o seu pedido de compras!</div>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown('<div class="custom-error-red">⚠️ Erro ao processar os dados da busca. Verifique as configurações dos filtros e tente novamente.</div>', unsafe_allow_html=True)
else:
    # SAUDAÇÃO INICIAL EXCLUSIVA DO PORTAL
    st.markdown('<div class="custom-welcome-salutation">👋 Olá! Seja bem-vindo ao Portal de Gestão de Compras.</div>', unsafe_allow_html=True)

st.markdown("<div style='text-align:center; margin-top:40px; border-top:1px solid #e2e8f0; padding-top:20px;'><p style='color:#64748b; font-size:13px; font-weight:600;'>Parente Andrade | Coordenação de Suprimentos</p></div>", unsafe_allow_html=True)
