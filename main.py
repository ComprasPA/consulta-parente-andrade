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

# 3. CSS MODERNIZADO (Alinhamento limpo, assinatura fixa, Ajuste Mobile e Ocultação da Toolbar)
st.markdown(f"""
    <style>
    /* Ocultar elementos padrão do Streamlit e zerar espaço do topo */
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    
    /* REMOVER CAIXA DE OPÇÕES FLUTUANTE DO DATAFRAME (Olho, download, lupa) */
    div[data-testid="stElementToolbar"] {{
        display: none !important;
    }}
    
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
    
    /* Alinhamento do título ao meio da página */
    .center-title-container {{
        width: 100%;
        text-align: center;
        display: flex;
        justify-content: center;
        align-items: center;
    }}
    
    .portal-title {{ 
        color: #1e293b !important; 
        font-size: 38px !important; 
        font-weight: 800 !important; 
        margin: 0 auto !important;
        letter-spacing: -1px;
        line-height: 1;
        white-space: nowrap;
    }}
    
    /* Customizacao fina para campos de input, seletores, botoes */
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
    
    /* REMOÇÃO TOTAL DA LINHA DE CONTORNO (FECHADA OU ABERTA) */
    div[data-testid="stExpander"], 
    div[data-testid="stExpander"] > div,
    div[data-testid="stExpander"][data-open="true"],
    div[data-testid="stExpander"][data-open="false"],
    .stElementContainer:has(div[data-testid="stExpander"]) {{
        background-color: transparent !important;
        border: none !important;
        border-width: 0px !important;
        box-shadow: none !important;
        outline: none !important;
    }}
    
    /* Remove contornos residuais e força fundo limpo na barra do expander */
    div[data-testid="stExpander"] summary,
    div[data-testid="stExpander"] [role="button"],
    .streamlit-expanderHeader {{
        background-color: transparent !important;
        border: none !important;
        border-width: 0px !important;
        box-shadow: none !important;
        display: inline-flex !important;
        justify-content: flex-end !important;
        flex-direction: row !important;  
        float: right !important;
        text-align: right !important;
        gap: 8px !important;
        width: auto !important;
    }}
    
    /* INTERAÇÃO DA SETA: Permite o giro nativo e suave do componente original */
    div[data-testid="stExpander"] summary svg {{
        transition: transform 0.2s ease-in-out !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    
    /* Garante cor estável de alta visibilidade (Grafite) independente do estado */
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] [data-open="true"] summary p,
    .streamlit-expanderHeader p,
    .streamlit-expanderHeader:focus p {{
        color: #1e293b !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        margin: 0 !important;
    }}
    
    /* Mudança suave para verde apenas no hover */
    div[data-testid="stExpander"] summary:hover p {{
        color: #478c3b !important;
    }}
    
    /* Ajuste de largura do input de data nativo */
    div[data-testid="stDateInput"] {{
        width: 100%;
    }}
    
    /* Remove a borda e contorno do sub-formulario interno dos filtros */
    div[data-testid="stForm"] {{
        border: none !important;
        padding: 0px !important;
        box-shadow: none !important;
        background-color: transparent !important;
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
        background-color: #e0f2fe !important;
        color: #0369a1 !important;
        padding: 16px 24px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 16px;
        width: 100%;
        border-left: 5px solid #0284c7;
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

    .custom-footer-block {{
        text-align: center !important; 
        margin-top: 60px !important; 
        border-top: 1px solid #e2e8f0 !important; 
        padding-top: 24px !important;
        padding-bottom: 24px !important;
        position: static !important; 
        clear: both !important;
        width: 100% !important;
        display: block !important;
    }}

    /* Assinatura fixa no canto inferior esquerdo da tela */
    .signature-fixed {{
        position: fixed;
        bottom: 12px;
        left: 20px;
        color: #94a3b8;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
        z-index: 999999;
        pointer-events: none;
    }}
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# BACKEND: INGESTÃO CORRIGIDA (ENGENHARIA ANTI-FÓRMULA)
# ==========================================
@st.cache_data(ttl=10)
def carregar_dados_seguros():
    file_id = "1hvVgN-eMojH1Q5mAl9rVUFGIUf9Z-YpiH0_uBDKXvQ0"
    
    # ESTRATÉGIA PRINCIPAL: Exportar como CSV cego. 
    # O CSV anula a existência de fórmulas, trazendo estritamente o valor visível na tela (evita o #ERROR!)
    URL_CSV = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&sheet=Pedidos"
    
    try:
        df_pc = pd.read_csv(URL_CSV, dtype=str).fillna('')
        if not df_pc.empty and len(df_pc.columns) > 1:
            df_pc.columns = [str(c).strip() for c in df_pc.columns]
            return df_pc
    except:
        pass
    
    # FALLBACK DE EMERGÊNCIA: Se o CSV falhar, tenta Excel padrão
    URL_XLSX = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL_XLSX, engine='openpyxl')
        aba = "Pedidos" if "Pedidos" in excel.sheet_names else excel.sheet_names[0]
        df_pc = pd.read_excel(excel, sheet_name=aba, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]
        return df_pc
    except Exception as e:
        return pd.DataFrame()

df_pc = carregar_dados_seguros()

# ==========================================
# 4. CABEÇALHO INTEGRADO
# ==========================================
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

if "filtro_status_val" not in st.session_state:
    st.session_state.filtro_status_val = "Todos"
if "filtro_data_val" not in st.session_state:
    st.session_state.filtro_data_val = ()
if "gaveta_aberta" not in st.session_state:
    st.session_state.gaveta_aberta = False

rotulo_seta = "Filtros Avançados ▲" if st.session_state.gaveta_aberta else "Filtros Avançados ▼"

with st.expander(rotulo_seta, expanded=st.session_state.gaveta_aberta):
    with st.form("form_filtros", clear_on_submit=False):
        f_col1, f_col2, f_col3, f_col4 = st.columns([4.5, 4.5, 1.5, 1.5])
        
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
                st.cache_data.clear()
                st.rerun()

# Mapeamento estrito das novas colunas físicas reais da guia "Pedidos"
DICIONARIO_COLUNAS_EXATAS = [
    {"planilha": "STATUS", "tela": "STATUS", "tipo": "texto"},
    {"planilha": "Centro de Custo", "tela": "Centro de Custo (CC)", "tipo": "texto"},
    {"planilha": "Solicitação", "tela": "Nº Solicitação (SC)", "tipo": "texto"},
    {"planilha": "Pedido", "tela": "Nº Pedido (PC)", "tipo": "pedido"},   
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

def formatar_para_dd_mm_aa(valor):
    txt = str(valor).strip()
    if txt == "" or txt.lower() in ["nan", "none", "0", "n/a"]:
        return txt
    try:
        return pd.to_datetime(txt, errors='coerce', format='mixed').strftime('%d/%m/%y')
    except:
        return txt

# ==========================================
# 6. MOTOR DE BUSCA EM TEXTO PURO REPARAMETRIZADO (LÓGICA CORRIGIDA)
# ==========================================
if busca:
    termo_busca = busca.strip()
    termo_numerico = re.sub(r'[^0-9]', '', termo_busca)
    
    df_final = pd.DataFrame()
    modo_pedido = False
    modo_solicitacao = False
    modo_centro_custo = False
    
    # 1. DEFINIÇÃO DA REGRA DE NEGÓCIO (Feito antes da busca para garantir as mensagens corretas)
    if termo_numerico:
        if len(termo_busca) == 4 and termo_busca.isdigit():
            modo_centro_custo = True
        elif int(termo_numerico) >= 170000:
            modo_pedido = True
        else:
            modo_solicitacao = True

    try:
        # Só executa a busca se a planilha tiver carregado corretamente
        if not df_pc.empty and termo_numerico:
            valor_busca_int = int(termo_numerico)
            
            # A) MÓDULO CENTRO DE CUSTO
            if modo_centro_custo:
                col_real_cc = next((c for c in df_pc.columns if "CUSTO" in c.upper() or "CC" in c.upper()), "Centro de Custo")
                if col_real_cc in df_pc.columns:
                    df_final = df_pc[df_pc[col_real_cc].astype(str).str.strip().str.contains(termo_busca, na=False)].copy()
            
            # B) MÓDULO DOCUMENTOS (Pedido / Solicitação)
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

            # Fallback para buscas por texto livre (se não for número exato)
            if df_final.empty and not termo_busca.isdigit():
                col_busca_geral = df_pc.columns[0]
                df_final = df_pc[df_pc[col_busca_geral].astype(str).str.strip().str.contains(re.escape(termo_busca), flags=re.IGNORECASE, na=False)].copy()

            # Processamento de Filtros Ativos da Gaveta Avançada
            if not df_final.empty and st.session_state.filtro_status_val != "Todos" and col_status_verificacao:
                df_final = df_final[df_final[col_status_verificacao].astype(str).str.strip() == st.session_state.filtro_status_val]

            if not df_final.empty and st.session_state.filtro_data_val and len(st.session_state.filtro_data_val) == 2:
                if st.session_state.filtro_data_val[0] is not None and st.session_state.filtro_data_val[1] is not None:
                    col_emissao_original = next((c for c in df_pc.columns if "EMISSAO" in c.upper()), None)
                    if col_emissao_original:
                        datas_convertidas = pd.to_datetime(df_final[col_emissao_original], errors='coerce', format='mixed').dt.date
                        df_final = df_final[(datas_convertidas >= st.session_state.filtro_data_val[0]) & (datas_convertidas <= st.session_state.filtro_data_val[1])]

        # Renderização do Painel de Resultados Completo
        if not df_final.empty:
            df_painel = pd.DataFrame(index=df_final.index)
            
            for col_config in DICIONARIO_COLUNAS_EXATAS:
                nome_original_planilha = col_config["planilha"]
                nome_exibicao_tela = col_config["tela"]
                tipo_campo = col_config["tipo"]
                
                # Tradução flexível para colunas vitais
                col_real = None
                nome_upper = nome_original_planilha.strip().upper()
                
                for c in df_final.columns:
                    if c.strip().upper() == nome_upper:
                        col_real = c
                        break
                        
                if not col_real:
                    for c in df_final.columns:
                        c_up = c.strip().upper()
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

            colunas_para_formatar = ["Envio", "Pagamento", "Previsão de entrega", "Entrega", "Emissão", "Aprovação"]
            for col_data in colunas_para_formatar:
                if col_data in df_painel.columns:
                    df_painel[col_data] = df_painel[col_data].apply(formatar_para_dd_mm_aa)

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
                    st.markdown('<div class="custom-error-red">⚠️ Erro: Não foi possível carregar a base de dados. Verifique o link do arquivo.</div>', unsafe_allow_html=True)
                elif modo_centro_custo:
                    st.markdown(f'<div class="custom-error-red">⚠️ O Centro de Custo \'{termo_busca}\' informado não possui registros correspondentes com os filtros atuais.</div>', unsafe_allow_html=True)
                elif modo_pedido:
                    st.markdown('<div class="custom-error-red">⚠️ Seu pedido de compras não foi localizado. Entre em contato com o comprador responsável.</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="custom-info-blue">⏳ Sua Solicitação ainda está em cotação. Logo estaremos finalizando o seu pedido de compras!</div>', unsafe_allow_html=True)
        else:
            if df_pc.empty:
                st.markdown('<div class="custom-error-red">⚠️ Erro: Não foi possível carregar a base de dados. Verifique o link ou o nome da aba "Pedidos".</div>', unsafe_allow_html=True)
            elif modo_centro_custo:
                st.markdown(f'<div class="custom-error-red">⚠️ O Centro de Custo \'{termo_busca}\' informado não possui registros correspondentes na base.</div>', unsafe_allow_html=True)
            elif modo_pedido or (termo_numerico and int(termo_numerico) >= 170000):
                st.markdown('<div class="custom-error-red">⚠️ Seu pedido de compras não foi localizado. Entre em contato com o comprador responsável.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="custom-info-blue">⏳ Sua Solicitação ainda está em cotação. Logo estaremos finalizando o seu pedido de compras!</div>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown('<div class="custom-error-red">⚠️ Erro ao processar os dados da busca. Verifique as colunas do seu arquivo.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="custom-welcome-salutation">👋 Olá! Seja bem-vindo ao Portal de Gestão de Compras.</div>', unsafe_allow_html=True)

# 7. RODAPÉ INSTITUCIONAL
st.markdown("<div class=\"custom-footer-block\"><p style='color:#64748b; font-size:13px; font-weight:600; margin:0;'>Parente Andrade | Coordenação de Suprimentos</p></div>", unsafe_allow_html=True)

# 8. MARCA D'ÁGUA FIXA EXCLUSIVA DA AUTORIA
st.markdown('<div class="signature-fixed">Created by SS.</div>', unsafe_allow_html=True)
