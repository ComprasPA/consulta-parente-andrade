import streamlit as st
import pandas as pd
import base64
import re
from datetime import datetime, timedelta
from io import BytesIO
import urllib.request

# 1. CONFIGURAÇÃO DA PÁGINA
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

# 3. CSS MODERNIZADO
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    div[data-testid="stElementToolbar"] { display: none !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }
    .stApp { background-color: #f8fafc; font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    .header-modern { background: #ffffff; padding: 16px 24px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; margin-top: 0px !important; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); }
    div[data-testid="column"] { display: flex; align-items: center; justify-content: center; }
    .center-title-container { width: 100%; text-align: center; display: flex; justify-content: center; align-items: center; }
    .portal-title { color: #1e293b !important; font-size: 38px !important; font-weight: 800 !important; margin: 0 auto !important; letter-spacing: -1px; line-height: 1; white-space: nowrap; }
    div[data-testid="stVerticalBlock"] > div:has(input), div[data-testid="stVerticalBlock"] > div:has(select), div[data-testid="stVerticalBlock"] > div:has(button) { background-color: #ffffff; padding: 2px 6px !important; border-radius: 8px; border: 1px solid #e2e8f0 !important; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02); transition: border-color 0.2s; width: 100%; }
    div[data-testid="stVerticalBlock"] > div:has(input):focus-within, div[data-testid="stVerticalBlock"] > div:has(select):focus-within { border-color: #478c3b !important; }
    div[data-testid="stExpander"], div[data-testid="stExpander"] > div, div[data-testid="stExpander"][data-open="true"], div[data-testid="stExpander"][data-open="false"], .stElementContainer:has(div[data-testid="stExpander"]) { background-color: transparent !important; border: none !important; border-width: 0px !important; box-shadow: none !important; outline: none !important; }
    div[data-testid="stExpander"] summary, div[data-testid="stExpander"] [role="button"], .streamlit-expanderHeader { background-color: transparent !important; border: none !important; border-width: 0px !important; box-shadow: none !important; display: inline-flex !important; justify-content: flex-end !important; flex-direction: row !important; float: right !important; text-align: right !important; gap: 8px !important; width: auto !important; }
    div[data-testid="stExpander"] summary svg { transition: transform 0.2s ease-in-out !important; margin: 0 !important; padding: 0 !important; }
    div[data-testid="stExpander"] summary p, div[data-testid="stExpander"] [data-open="true"] summary p, .streamlit-expanderHeader p, .streamlit-expanderHeader:focus p { color: #1e293b !important; font-weight: 700 !important; font-size: 16px !important; margin: 0 !important; }
    div[data-testid="stExpander"] summary:hover p { color: #478c3b !important; }
    div[data-testid="stDateInput"] { width: 100%; }
    div[data-testid="stForm"] { border: none !important; padding: 0px !important; box-shadow: none !important; background-color: transparent !important; }
    .status-card { background: #ffffff; color: #1e293b; padding: 16px 24px; border-radius: 8px; font-weight: 600; font-size: 16px; border-left: 5px solid #478c3b; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 16px; width: 100%; }
    .custom-info-blue { background-color: #e0f2fe !important; color: #0369a1 !important; padding: 16px 24px; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 16px; width: 100%; border-left: 5px solid #0284c7; }
    .custom-error-red { background-color: #fee2e2 !important; color: #991b1b !important; padding: 16px 24px; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 16px; width: 100%; border-left: 5px solid #ef4444; }
    .custom-welcome-salutation { background-color: #ffffff; color: #1e293b; padding: 32px 24px; border-radius: 12px; font-weight: 600; font-size: 20px; text-align: center; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); margin-top: 20px; }
    div[data-testid="stDataFrame"] { background: #ffffff; padding: 16px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    div[data-testid="stDataFrame"] table th { white-space: nowrap !important; min-width: max-content !important; }
    .custom-footer-block { text-align: center !important; margin-top: 60px !important; border-top: 1px solid #e2e8f0 !important; padding-top: 24px !important; padding-bottom: 24px !important; position: static !important; clear: both !important; width: 100% !important; display: block !important; }
    .signature-fixed { position: fixed; bottom: 12px; left: 20px; color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; z-index: 999999; pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

# 4. CARREGAMENTO COM ESTADO
def carregar_dados_seguros():
    file_id = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"
    URL_CSV = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid=0"
    
    try:
        df = pd.read_csv(URL_CSV, dtype=str).fillna('')
        if "<html" in str(df.columns[0]).lower():
            raise ValueError("O Google retornou bloqueio HTML.")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e_csv:
        try:
            URL_XLSX = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
            excel = pd.ExcelFile(URL_XLSX, engine='openpyxl')
            aba = "Pedidos_App" if "Pedidos_App" in excel.sheet_names else ("Pedidos" if "Pedidos" in excel.sheet_names else excel.sheet_names[0])
            df = pd.read_excel(excel, sheet_name=aba, dtype=str).fillna('')
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception as e_xlsx:
            st.session_state.erro_tecnico = f"CSV: {str(e_csv)} | XLSX: {str(e_xlsx)}"
            return pd.DataFrame()

# Inicializa ou atualiza os dados globais
if 'dados_globais' not in st.session_state:
    st.session_state.dados_globais = carregar_dados_seguros()

df_pc = st.session_state.dados_globais

# 5. CABEÇALHO INTEGRADO 
st.markdown('<div class="header-modern">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.5, 6.5, 2.0])

with c1:
    if base64_logo: 
        st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:120px; display:block; margin:auto 0;">', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="center-title-container"><p class="portal-title">Portal Gestão de Compras</p></div>', unsafe_allow_html=True)
with c3:
    busca = st.text_input("", placeholder="🔍 Rastrear SC, PC ou CC...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# 6. FILTROS E LÓGICA DE GAVETA COM BOTÃO DE ATUALIZAÇÃO
if "filtro_status_val" not in st.session_state:
    st.session_state.filtro_status_val = "Todos"
if "filtro_data_val" not in st.session_state:
    st.session_state.filtro_data_val = ()
if "gaveta_aberta" not in st.session_state:
    st.session_state.gaveta_aberta = False

rotulo_seta = "Filtros Avançados ▲" if st.session_state.gaveta_aberta else "Filtros Avançados ▼"

with st.expander(rotulo_seta, expanded=st.session_state.gaveta_aberta):
    with st.form("form_filtros", clear_on_submit=False):
        f_col1, f_col2, f_col3, f_col4, f_col5 = st.columns([3.0, 3.0, 1.5, 1.5, 2.0])
        
        with f_col1:
            col_status_verificacao = next((c for c in df_pc.columns if "STATUS" in c.upper()), None) if not df_pc.empty else None
            if col_status_verificacao:
                lista_status = ["Todos"] + sorted([str(x).strip() for x in df_pc[col_status_verificacao].unique() if str(x).strip() != ""])
            else:
                lista_status = ["Todos"]
                
            idx_padrao = lista_status.index(st.session_state.filtro_status_val) if st.session_state.filtro_status_val in lista_status else 0
            filtro_status = st.selectbox("Filtrar por Status Operacional:", options=lista_status, index=idx_padrao)
            
        with f_col2:
            filtro_data = st.date_input("Filtrar por Período de Emissão:", value=st.session_state.filtro_data_val, format="DD/MM/YYYY")
            
        with f_col3:
            st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True) 
            btn_pesquisar = st.form_submit_button("🔍 Pesquisar", use_container_width=True)
            
            if btn_pesquisar:
                st.session_state.filtro_status_val = filtro_status
                st.session_state.filtro_data_val = filtro_data
                st.session_state.gaveta_aberta = True  
                st.rerun()

        with f_col4:
            st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True) 
            btn_limpar = st.form_submit_button("❌ Limpar", use_container_width=True)
            
            if btn_limpar:
                st.session_state.filtro_status_val = "Todos"
                st.session_state.filtro_data_val = ()
                st.session_state.gaveta_aberta = False  
                st.rerun()
                
        with f_col5:
            st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True) 
            btn_atualizar = st.form_submit_button("🔄 Atualizar Banco", use_container_width=True)
            
            if btn_atualizar:
                st.session_state.dados_globais = carregar_dados_seguros()
                st.session_state.gaveta_aberta = True  
                st.rerun()

# 7. MAPEAMENTO DAS COLUNAS
DICIONARIO_COLUNAS_EXATAS = [
    {"planilha": "STATUS", "tela": "STATUS", "tipo": "texto"},
    {"planilha": "Centro de Custo", "tela": "Centro de Custo", "tipo": "texto"},
    {"planilha": "Solicitação", "tela": "Solicitação", "tipo": "texto"},
    {"planilha": "Pedido", "tela": "Pedidos", "tipo": "pedido"},   
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
        return 0.0
    dado = str(valor).strip().replace(' ', '')
    try:
        if ',' in dado and '.' in dado:
            dado = dado.replace('.', '').replace(',', '.')
        elif ',' in dado:
            dado = dado.replace(',', '.')
        val_float = float(dado)
        return round(val_float, 2)
    except:
        return 0.0

# AJUSTE DA DATA PARA DD/MM/AAAA (4 DÍGITOS NO ANO)
def formatar_para_dd_mm_aaaa(valor):
    txt = str(valor).strip()
    if txt == "" or txt.lower() in ["nan", "none", "0", "n/a"]:
        return txt
    try:
        # AQUI FOI ALTERADO DE %y PARA %Y
        return pd.to_datetime(txt, errors='coerce', format='mixed').strftime('%d/%m/%Y')
    except:
        return txt

# 8. MOTOR DE BUSCA EM TEXTO PURO
if busca:
    termo_busca = busca.strip()
    termo_numerico = re.sub(r'[^0-9]', '', termo_busca)
    
    df_final = pd.DataFrame()
    modo_pedido = False
    modo_solicitacao = False
    modo_centro_custo = False
    
    if termo_numerico:
        if len(termo_busca) == 4 and termo_busca.isdigit():
            modo_centro_custo = True
        elif int(termo_numerico) >= 170000:
            modo_pedido = True
        else:
            modo_solicitacao = True

    try:
        if not df_pc.empty and termo_numerico:
            valor_busca_int = int(termo_numerico)
            
            if modo_centro_custo:
                col_real_cc = next((c for c in df_pc.columns if "CUSTO" in c.upper() or "CC" in c.upper()), "Centro de Custo")
                if col_real_cc in df_pc.columns:
                    df_final = df_pc[df_pc[col_real_cc].astype(str).str.strip().str.contains(termo_busca, na=False)].copy()
            
            else:
                if modo_pedido:
                    col_pc = next((c for c in df_pc.columns if "PEDIDO" in c.upper()), "Pedido")
                    if col_pc in df_pc.columns:
                        serie_pc_txt = df_pc[col_pc].astype(str).str.split('.').str[0].str.replace(r'[^0-9]', '', regex=True).str.strip()
                        df_final = df_pc[serie_pc_txt == str(valor_busca_int)].copy()
                
                if modo_solicitacao:
                    col_sc = next((c for c in df_pc.columns if "SOLICITA" in c.upper()), "Solicitação")
                    if col_sc in df_pc.columns:
                        serie_sc_txt = df_pc[col_sc].astype(str).str.split('.').str[0].str.replace(r'[^0-9]', '', regex=True).str.strip()
                        df_final = df_pc[serie_sc_txt == str(valor_busca_int)].copy()

            if df_final.empty and not termo_busca.isdigit():
                col_busca_geral = df_pc.columns[0]
                df_final = df_pc[df_pc[col_busca_geral].astype(str).str.strip().str.contains(re.escape(termo_busca), flags=re.IGNORECASE, na=False)].copy()

            if not df_final.empty and st.session_state.filtro_status_val != "Todos" and col_status_verificacao:
                df_final = df_final[df_final[col_status_verificacao].astype(str).str.strip() == st.session_state.filtro_status_val]

            if not df_final.empty and st.session_state.filtro_data_val and len(st.session_state.filtro_data_val) == 2:
                if st.session_state.filtro_data_val[0] is not None and st.session_state.filtro_data_val[1] is not None:
                    col_emissao_original = next((c for c in df_pc.columns if "EMISSAO" in c.upper()), None)
                    if col_emissao_original:
                        datas_convertidas = pd.to_datetime(df_final[col_emissao_original], errors='coerce', format='mixed').dt.date
                        df_final = df_final[(datas_convertidas >= st.session_state.filtro_data_val[0]) & (datas_convertidas <= st.session_state.filtro_data_val[1])]

        if not df_final.empty:
            df_painel = pd.DataFrame(index=df_final.index)
            
            for col_config in DICIONARIO_COLUNAS_EXATAS:
                nome_original_planilha = col_config["planilha"]
                nome_exibicao_tela = col_config["tela"]
                tipo_campo = col_config["tipo"]
                
                col_real = None
                nome_upper = nome_original_planilha.strip().upper()
                
                for c in df_final.columns:
                    if c.strip().upper() == nome_upper:
                        col_real = c
                        break
                        
                if not col_real:
                    for c in df_final.columns:
                        c_up = c.strip().upper()
                        if "STATUS" in nome_upper and "STATUS" in c_up: col_real = c; break
                        if "SOLICITA" in nome_upper and "SOLICITA" in c_up: col_real = c; break
                        if "PEDIDO" in nome_upper and "PEDIDO" in c_up: col_real = c; break
                        if "CENTRO" in nome_upper and "CUSTO" in nome_upper and "CENTRO" in c_up and "CUSTO" in c_up: col_real = c; break
                
                if col_real:
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
                    df_painel[nome_exibicao_tela] = ""

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

            # CHAMADA DA NOVA FUNÇÃO DE DATA AQUI
            colunas_para_formatar = ["Envio", "Pagamento", "Previsão de entrega", "Entrega", "Emissão", "Aprovação"]
            for col_data in colunas_para_formatar:
                if col_data in df_painel.columns:
                    df_painel[col_data] = df_painel[col_data].apply(formatar_para_dd_mm_aaaa)

            df_painel = df_painel.dropna(how='all')

            if not df_painel.empty:
                if modo_centro_custo:
                    txt_status = f"🔍 Registros Ativos para o Centro de Custo: {termo_busca}"
                elif modo_pedido:
                    txt_status = f"📦 Pedido de Compras Firme Localizado: {termo_busca}"
                elif modo_solicitacao:
                    txt_status = f"⏳ Solicitação de Compras Localizada: {termo_busca}"
                else:
                    txt_status = f"🔍 Registros Localizados para o termo: {termo_busca}"
                
                st.markdown(f'<div class="status-card">{txt_status}</div>', unsafe_allow_html=True)
                
                c_down, _ = st.columns([2.5, 7.5])
                with c_down:
                    out = BytesIO()
                    with pd.ExcelWriter(out, engine='xlsxwriter') as wr: 
                        df_painel.to_excel(wr, index=False, sheet_name="Relatório")
                        workbook  = wr.book
                        worksheet = wr.sheets["Relatório"]
                        formato_moeda = workbook.add_format({'num_format': 'R$ #,##0.00'})
                        for idx, col_config in enumerate(DICIONARIO_COLUNAS_EXATAS):
                            if col_config["tipo"] == "moeda":
                                worksheet.set_column(idx, idx, 22, formato_moeda)

                    st.download_button(
                        label="📥 Extrair Relatório Operacional",
                        data=out.getvalue(),
                        file_name=f"Relatorio_Compras_{termo_busca}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                
                configuracao_colunas_tela = {}
                for col_config in DICIONARIO_COLUNAS_EXATAS:
                    nome_tela = col_config["tela"]
                    tipo_campo = col_config["tipo"]
                    if nome_tela == "STATUS":
                        configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, alignment="center")
                    elif tipo_campo == "moeda":
                        configuracao_colunas_tela[nome_tela] = st.column_config.NumberColumn(nome_tela, format="R$ %.2f", alignment="right")
                    elif tipo_campo == "numero":
                        configuracao_colunas_tela[nome_tela] = st.column_config.NumberColumn(nome_tela, alignment="right")
                    else:
                        if nome_tela in ["Fornecedor", "Descrição"]:
                            configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, alignment="left")
                        else:
                            configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, alignment="right")

                st.dataframe(df_painel, use_container_width=True, hide_index=True, column_config=configuracao_colunas_tela)
            else:
                if df_pc.empty:
                    erro = st.session_state.get('erro_tecnico', 'Erro desconhecido.')
                    st.markdown(f'<div class="custom-error-red">⚠️ Erro: Não foi possível carregar a base de dados. Detalhe: {erro}</div>', unsafe_allow_html=True)
                elif modo_centro_custo:
                    st.markdown(f'<div class="custom-error-red">⚠️ O Centro de Custo \'{termo_busca}\' informado não possui registros correspondentes com os filtros atuais.</div>', unsafe_allow_html=True)
                elif modo_pedido:
                    st.markdown('<div class="custom-error-red">⚠️ Seu pedido de compras não foi localizado. Entre em contato com a equipe.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="custom-info-blue">⏳ Sua Solicitação ainda está em cotação. Logo estaremos finalizando o seu pedido de compras!</div>', unsafe_allow_html=True)
        else:
            if df_pc.empty:
                erro = st.session_state.get('erro_tecnico', 'Permissão negada ou aba ausente.')
                st.markdown(f'<div class="custom-error-red">⚠️ Erro: Acesso Negado à Planilha.<br><br><b>1.</b> Verifique se o link está como "Qualquer pessoa com o link".<br><b>2.</b> Renomeie a aba para "Pedidos".<br><br><small>Erro Técnico: {erro}</small></div>', unsafe_allow_html=True)
            elif modo_centro_custo:
                st.markdown(f'<div class="custom-error-red">⚠️ O Centro de Custo \'{termo_busca}\' informado não possui registros correspondentes na base.</div>', unsafe_allow_html=True)
            elif modo_pedido or (termo_numerico and int(termo_numerico) >= 170000):
                st.markdown('<div class="custom-error-red">⚠️ Seu pedido de compras não foi localizado. Entre em contato com a equipe.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="custom-info-blue">⏳ Sua Solicitação ainda está em cotação. Logo estaremos finalizando o seu pedido de compras!</div>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown('<div class="custom-error-red">⚠️ Erro ao processar os dados da busca. Verifique as colunas do seu arquivo.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="custom-welcome-salutation">👋 Olá! Seja bem-vindo ao Portal de Gestão de Compras.</div>', unsafe_allow_html=True)

# 9. RODAPÉ INSTITUCIONAL
st.markdown("<div class=\"custom-footer-block\"><p style='color:#64748b; font-size:13px; font-weight:600; margin:0;'>Parente Andrade | Coordenação de Suprimentos</p></div>", unsafe_allow_html=True)

# 10. MARCA D'ÁGUA FIXA EXCLUSIVA DA AUTORIA
st.markdown('<div class="signature-fixed">Created by SS.</div>', unsafe_allow_html=True)
