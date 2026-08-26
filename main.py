import streamlit as st
import pandas as pd
import base64
import re
from datetime import datetime, timedelta
from io import BytesIO
import urllib.request
import gspread
from google.oauth2.service_account import Credentials

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
    
    div.stFormSubmitButton > button { width: 100% !important; min-height: 36px !important; max-height: 36px !important; font-size: 13px !important; font-weight: 600 !important; padding: 0px 8px !important; }

    .status-card { background: #ffffff; color: #1e293b; padding: 16px 24px; border-radius: 8px; font-weight: 600; font-size: 16px; border-left: 5px solid #478c3b; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 16px; width: 100%; }
    .custom-error-red { background-color: #fee2e2 !important; color: #991b1b !important; padding: 16px 24px; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 16px; width: 100%; border-left: 5px solid #ef4444; }
    .custom-welcome-salutation { background-color: #ffffff; color: #1e293b; padding: 32px 24px; border-radius: 12px; font-weight: 600; font-size: 20px; text-align: center; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); margin-top: 20px; }
    
    div[data-testid="stDataFrame"] { background: #ffffff; padding: 16px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    div[data-testid="stDataFrame"] table th { white-space: nowrap !important; min-width: max-content !important; }

    /* ESTILIZAÇÃO DO DROPDOWN / LISTA SUSPENSA */
    div[data-baseweb="menu"], ul[data-baseweb="menu"], div[role="listbox"] {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
    }
    div[data-baseweb="menu"] li, ul[data-baseweb="menu"] li, div[role="option"] {
        background-color: #ffffff !important;
        color: #1e293b !important;
    }
    div[data-baseweb="menu"] li:hover, ul[data-baseweb="menu"] li:hover, div[role="option"]:hover {
        background-color: #e2e8f0 !important;
        color: #0f172a !important;
    }

    .custom-footer-block { text-align: center !important; margin-top: 60px !important; border-top: 1px solid #e2e8f0 !important; padding-top: 24px !important; padding-bottom: 24px !important; position: static !important; clear: both !important; width: 100% !important; display: block !important; }
    .signature-fixed { position: fixed; bottom: 12px; left: 20px; color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; z-index: 999999; pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

FILE_ID = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"

# 4. CARREGAMENTO SEGURO DIRETO DA ABA "Pedidos"
@st.cache_data(ttl=60)
def carregar_dados_seguros():
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
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
        return df
    except Exception as e:
        st.session_state.erro_tecnico = f"Erro Gspread: {str(e)}"
        return pd.DataFrame()

if 'dados_globais' not in st.session_state or st.session_state.dados_globais.empty:
    st.session_state.dados_globais = carregar_dados_seguros()

df_pc = st.session_state.dados_globais

# Estados de sessão
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "departamento_ativo" not in st.session_state:
    st.session_state.departamento_ativo = ""
if "mostrar_popup_login" not in st.session_state:
    st.session_state.mostrar_popup_login = False
if "gaveta_aberta" not in st.session_state:
    st.session_state.gaveta_aberta = True

# 5. CABEÇALHO INTEGRADO
st.markdown('<div class="header-modern">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.5, 7.0, 1.5])

with c1:
    if base64_logo: 
        st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:120px; display:block; margin:auto 0;">', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="center-title-container"><p class="portal-title">Portal Gestão de Compras</p></div>', unsafe_allow_html=True)
with c3:
    if not st.session_state.autenticado:
        if st.button("🔐 Operador", use_container_width=True):
            st.session_state.mostrar_popup_login = not st.session_state.mostrar_popup_login
            st.rerun()
    else:
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.departamento_ativo = ""
            st.session_state.mostrar_popup_login = False
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 6. JANELA POPUP DISCRETA DE LOGIN
if st.session_state.mostrar_popup_login and not st.session_state.autenticado:
    with st.container():
        st.markdown("""
            <div style="background-color: #ffffff; padding: 20px; border-radius: 12px; border: 2px solid #478c3b; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h3 style="color: #1e293b; margin-top: 0; font-size: 18px;">🔐 Autenticação de Operador</h3>
            </div>
        """, unsafe_allow_html=True)
        
        pop_c1, pop_c2, pop_c3, pop_c4 = st.columns([2.5, 2.5, 2.0, 1.5])
        with pop_c1:
            dep_escolhido = st.selectbox("Departamento:", ["compras", "almoxarifado", "logistica"], key="pop_dep")
        with pop_c2:
            senha_tentativa = st.text_input("Senha:", type="password", placeholder="Digite a senha...", key="pop_senha")
        with pop_c3:
            st.write("")
            st.write("")
            btn_confirmar = st.button("Confirmar Acesso", use_container_width=True)
            if btn_confirmar:
                senhas = {
                    "compras": "compras@2026",
                    "almoxarifado": "almox@2026",
                    "logistica": "log@2026"
                }
                if senha_tentativa == senhas.get(dep_escolhido):
                    st.session_state.autenticado = True
                    st.session_state.departamento_ativo = dep_escolhido
                    st.session_state.mostrar_popup_login = False
                    st.success("Autenticado com sucesso!")
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
        with pop_c4:
            st.write("")
            st.write("")
            if st.button("✖ Fechar", use_container_width=True):
                st.session_state.mostrar_popup_login = False
                st.rerun()
        st.divider()

# 7. FILTROS E LÓGICA DE GAVETA
if "filtro_pc_val" not in st.session_state:
    st.session_state.filtro_pc_val = ""
if "filtro_sc_val" not in st.session_state:
    st.session_state.filtro_sc_val = ""
if "filtro_cc_val" not in st.session_state:
    st.session_state.filtro_cc_val = ""
if "filtro_status_val" not in st.session_state:
    st.session_state.filtro_status_val = "Todos"
if "filtro_data_val" not in st.session_state:
    st.session_state.filtro_data_val = ()

rotulo_seta = "Filtros Avançados ▲" if st.session_state.gaveta_aberta else "Filtros Avançados ▼"

with st.expander(rotulo_seta, expanded=st.session_state.gaveta_aberta):
    with st.form("form_filtros", clear_on_submit=False):
        f1, f2, f3, f4, f5 = st.columns(5)
        
        with f1:
            filtro_pc = st.text_input("Pedido (PC):", value=st.session_state.filtro_pc_val, placeholder="Nº do PC...")
        with f2:
            filtro_sc = st.text_input("Solicitação (SC):", value=st.session_state.filtro_sc_val, placeholder="Nº da SC...")
        with f3:
            filtro_cc = st.text_input("Centro de Custo:", value=st.session_state.filtro_cc_val, placeholder="Centro de custo...")
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
        
        _, b1, b2, b3 = st.columns([4, 1.2, 1.2, 1.2])
        with b1:
            btn_pesquisar = st.form_submit_button("🔍 Pesquisar", use_container_width=True)
            if btn_pesquisar:
                st.session_state.filtro_pc_val = filtro_pc
                st.session_state.filtro_sc_val = filtro_sc
                st.session_state.filtro_cc_val = filtro_cc
                st.session_state.filtro_status_val = filtro_status
                st.session_state.filtro_data_val = filtro_data
                st.session_state.gaveta_aberta = False  
                st.rerun()

        with b2:
            btn_limpar = st.form_submit_button("❌ Limpar", use_container_width=True)
            if btn_limpar:
                st.session_state.filtro_pc_val = ""
                st.session_state.filtro_sc_val = ""
                st.session_state.filtro_cc_val = ""
                st.session_state.filtro_status_val = "Todos"
                st.session_state.filtro_data_val = ()
                st.session_state.gaveta_aberta = True  
                st.rerun()
                
        with b3:
            btn_atualizar = st.form_submit_button("🔄 Atualizar Banco", use_container_width=True)
            if btn_atualizar:
                st.session_state.dados_globais = carregar_dados_seguros()
                st.session_state.gaveta_aberta = True
                st.rerun()

# 8. DICIONÁRIO MAPEADO RIGOROSAMENTE COM AS SUAS COLUNAS EXATAS
DICIONARIO_COLUNAS_EXATAS = [
    {"planilha": ["STATUS"], "tela": "Status", "tipo": "texto"},
    {"planilha": ["CENTRO DE CUSTO"], "tela": "Centro De Custo", "tipo": "texto"},
    {"planilha": ["SOLICITAÇÃO", "SOLICITACAO"], "tela": "Solicitação", "tipo": "texto"},
    {"planilha": ["PEDIDO"], "tela": "Pedido", "tipo": "pedido"},   
    {"planilha": ["CONDIÇÃO PAGAMENTO"], "tela": "Condição Pagamento", "tipo": "texto"},
    {"planilha": ["DATA PEDIDO"], "tela": "Emissão", "tipo": "data"},
    {"planilha": ["DATA LIBERAÇÃO", "DATA LIBERACAO"], "tela": "Aprovação", "tipo": "data"},
    {"planilha": ["ENVIO"], "tela": "Envio", "tipo": "data"},
    {"planilha": ["PAGAMENTO"], "tela": "Pagamento", "tipo": "texto"}, 
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
    {"planilha": ["LOGISTICA"], "tela": "Logística", "tipo": "logistica"}
]

def converter_para_numerico(valor):
    if not valor or str(valor).lower() == 'nan' or str(valor).strip() == '':
        return 0.0
    dado = str(valor).strip().replace('R$', '').replace('$', '').replace(' ', '')
    try:
        if ',' in dado and '.' in dado:
            dado = dado.replace('.', '').replace(',', '.')
        elif ',' in dado:
            dado = dado.replace(',', '.')
        val_float = float(dado)
        return round(val_float, 2)
    except:
        return 0.0

def formatar_para_dd_mm_aaaa(valor):
    txt = str(valor).strip()
    if txt == "" or txt.lower() in ["nan", "none", "0", "n/a"]:
        return txt
    try:
        dt = pd.to_datetime(txt, errors='coerce', format='mixed', dayfirst=True)
        if pd.isna(dt):
            return txt
        return dt.strftime('%d/%m/%Y')
    except:
        return txt

# 9. MOTOR DE BUSCA CASCATA
tem_busca_ativa = st.session_state.filtro_pc_val or st.session_state.filtro_sc_val or st.session_state.filtro_cc_val or st.session_state.filtro_status_val != "Todos" or bool(st.session_state.filtro_data_val)

if tem_busca_ativa:
    if df_pc.empty:
        st.markdown('<div class="custom-error-red">⚠️ Base de dados vazia. Clique em "🔄 Atualizar Banco" nos Filtros Avançados.</div>', unsafe_allow_html=True)
    else:
        df_final = df_pc.copy()
        colunas_normalizadas = {c.upper().strip().replace('Í', 'I').replace('Ã', 'A'): c for c in df_final.columns}

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
            cc_termo = st.session_state.filtro_cc_val.strip().lower()
            col_cc = colunas_normalizadas.get("CENTRO DE CUSTO")
            if col_cc:
                df_final = df_final[df_final[col_cc].astype(str).str.lower().str.contains(cc_termo, na=False)]

        col_status_verificacao = colunas_normalizadas.get("STATUS")
        if st.session_state.filtro_status_val != "Todos" and col_status_verificacao:
            df_final = df_final[df_final[col_status_verificacao].astype(str).str.strip() == st.session_state.filtro_status_val]

        if st.session_state.filtro_data_val and len(st.session_state.filtro_data_val) == 2:
            if st.session_state.filtro_data_val[0] is not None and st.session_state.filtro_data_val[1] is not None:
                col_emissao_original = colunas_normalizadas.get("DATA PEDIDO")
                if col_emissao_original:
                    datas_convertidas = pd.to_datetime(df_final[col_emissao_original], errors='coerce', format='mixed', dayfirst=True).dt.date
                    df_final = df_final[(datas_convertidas >= st.session_state.filtro_data_val[0]) & (datas_convertidas <= st.session_state.filtro_data_val[1])]

        try:
            if not df_final.empty:
                df_painel = pd.DataFrame(index=df_final.index)
                
                for col_config in DICIONARIO_COLUNAS_EXATAS:
                    nome_exibicao_tela = col_config["tela"]
                    tipo_campo = col_config["tipo"]
                    
                    col_real = None
                    for alt in col_config["planilha"]:
                        alt_clean = alt.upper().strip().replace('Í', 'I').replace('Ã', 'A')
                        for c_up in colunas_normalizadas:
                            c_up_clean = c_up.replace('Í', 'I').replace('Ã', 'A')
                            if c_up_clean == alt_clean:
                                col_real = colunas_normalizadas[c_up]
                                break
                        if col_real:
                            break

                    if col_real:
                        valores_originais = df_final[col_real]
                        if tipo_campo == "data":
                            df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).str.strip().replace(['nan', 'NONE', '', '0'], '')
                        elif tipo_campo == "pedido":
                            df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                        elif tipo_campo == "produto":
                            df_painel[nome_exibicao_tela] = valores_originais.apply(lambda val: str(val).split('.')[0].strip().zfill(10) if str(val).strip() and str(val).lower() != 'nan' else "")
                        elif tipo_campo in ["moeda", "numero"]:
                            df_painel[nome_exibicao_tela] = valores_originais.apply(converter_para_numerico)
                        else:
                            df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '').str.strip()
                    else:
                        df_painel[nome_exibicao_tela] = ""

                # Associa a linha física exata da planilha
                df_painel["_row_idx"] = [idx + 2 for idx in df_final.index]

                col_status_tela = colunas_normalizadas.get("STATUS")
                if col_status_tela:
                    termos_excecao = ["SERVIÇO", "CANCELADO PELO SOLICITANTE", "REJEITADO PELO APROVADOR", "COMPRA DIRETA"]
                    mask_status = df_painel["Status"].astype(str).str.upper().apply(
                        lambda s: any(t in s for t in termos_excecao)
                    )
                    for col_nome in ["Previsão De Entrega", "Entrega"]:
                        if col_nome in df_painel.columns:
                            df_painel.loc[mask_status, col_nome] = "N/A"

                if "Previsão De Entrega" in df_painel.columns and "Entrega" in df_painel.columns:
                    mascara_vazia = (df_painel["Previsão De Entrega"] == "") | (df_painel["Previsão De Entrega"].isna())
                    df_painel.loc[mascara_vazia, "Previsão De Entrega"] = df_painel.loc[mascara_vazia, "Entrega"]

                if "Pagamento" in df_painel.columns and "Condição Pagamento" in df_painel.columns:
                    condicao_normalizada = df_painel["Condição Pagamento"].astype(str).str.upper().str.strip()
                    mascara_na = (
                        (~condicao_normalizada.str.contains("A VISTA", na=False)) & 
                        (~condicao_normalizada.str.contains("ENT", na=False)) & 
                        (~condicao_normalizada.str.contains("VENCIDO", na=False)) & 
                        (~condicao_normalizada.str.contains("PAGO", na=False))
                    )
                    df_painel.loc[mascara_na, "Pagamento"] = "N/A"

                colunas_para_formatar = ["Envio", "Pagamento", "Previsão De Entrega", "Entrega", "Emissão", "Aprovação"]
                for col_data in colunas_para_formatar:
                    if col_data in df_painel.columns:
                        df_painel[col_data] = df_painel[col_data].apply(
                            lambda x: x if str(x).upper() == "N/A" else formatar_para_dd_mm_aaaa(x)
                        )

                df_painel = df_painel.dropna(how='all')

                if not df_painel.empty:
                    txt_status = f"🔍 Registros Localizados ({len(df_painel)} itens)"
                    st.markdown(f'<div class="status-card">{txt_status}</div>', unsafe_allow_html=True)
                    
                    # BOTÕES LADO A LADO ACIMA DA TABELA
                    c_down1, c_down2 = st.columns([2.2, 2.2])
                    
                    with c_down1:
                        out = BytesIO()
                        df_excel_export = df_painel.drop(columns=["_row_idx"], errors="ignore")
                        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: 
                            df_excel_export.to_excel(wr, index=False, sheet_name="Relatório")
                            workbook  = wr.book
                            worksheet = wr.sheets["Relatório"]
                            formato_moeda = workbook.add_format({'num_format': 'R$ #,##0.00'})
                            for idx, col_config in enumerate(DICIONARIO_COLUNAS_EXATAS):
                                if col_config["tipo"] == "moeda":
                                    worksheet.set_column(idx, idx, 22, formato_moeda)

                        st.download_button(
                            label="📥 Baixar Relatório",
                            data=out.getvalue(),
                            file_name=f"Relatorio_Compras_Filtro.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

                    with c_down2:
                        if st.session_state.autenticado:
                            btn_salvar_dados = st.button("💾 Salvar Alterações", use_container_width=True)
                        else:
                            btn_salvar_dados = False

                    configuracao_colunas_tela = {}
                    
                    status_existentes = [str(x).strip() for x in df_pc[col_status_verificacao].unique() if str(x).strip() != ""] if col_status_verificacao else []
                    status_oficiais = [
                        "ENVIADO AO FORNECEDOR",
                        "ENVIADO AO FINANCEIRO",
                        "PAGO",
                        "CANCELADO PELO SOLICITANTE",
                        "FORNECEDOR DECLINOU",
                        "RECEBIDO NA SEDE",
                        "RECEBIDO PARCIAL",
                        "RECEBIDO DIRETO NA OBRA",
                        "SERVIÇO",
                        "COMPRA DIRETA",
                        "CORREÇÃO DE PROCESSO"
                    ]
                    lista_historico_status = sorted(list(set(status_existentes + status_oficiais)))

                    opcoes_logistica = [
                        "Retirado do Almoxarifado Sede",
                        "Entregue no PEA",
                        "A caminho da Obra",
                        "Entregue na obra"
                    ]

                    for col_config in DICIONARIO_COLUNAS_EXATAS:
                        nome_tela = col_config["tela"]
                        tipo_campo = col_config["tipo"]
                        
                        if st.session_state.autenticado:
                            dep = st.session_state.departamento_ativo
                            if dep == "logistica":
                                if nome_tela == "Logística":
                                    configuracao_colunas_tela[nome_tela] = st.column_config.SelectboxColumn(
                                        nome_tela, options=opcoes_logistica, required=False
                                    )
                                else:
                                    configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, disabled=True)
                            else:
                                campos_permitidos_compras = ["Status", "Envio", "Pagamento", "Previsão De Entrega", "Entrega", "NF Remessa"]
                                if nome_tela in campos_permitidos_compras:
                                    if nome_tela == "Status":
                                        configuracao_colunas_tela[nome_tela] = st.column_config.SelectboxColumn(
                                            nome_tela, options=lista_historico_status, required=True
                                        )
                                    else:
                                        configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, disabled=False)
                                else:
                                    configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, disabled=True)
                        else:
                            if nome_tela == "Status":
                                configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, alignment="center")
                            elif tipo_campo == "moeda":
                                configuracao_colunas_tela[nome_tela] = st.column_config.NumberColumn(nome_tela, format="R$ %.2f", alignment="right")
                            elif tipo_campo == "numero":
                                configuracao_colunas_tela[nome_tela] = st.column_config.NumberColumn(nome_tela, alignment="right")
                            else:
                                configuracao_colunas_tela[nome_tela] = st.column_config.Column(nome_tela, disabled=True)

                    configuracao_colunas_tela["_row_idx"] = None

                    if st.session_state.autenticado:
                        if "df_original_cache" not in st.session_state or st.session_state.get("atualizar_cache_editor", True):
                            st.session_state.df_original_cache = df_painel.copy()
                            st.session_state.atualizar_cache_editor = False

                        edited_df = st.data_editor(
                            df_painel, 
                            use_container_width=True, 
                            hide_index=True, 
                            column_config=configuracao_colunas_tela,
                            key="editor_painel_compras"
                        )
                        
                        # SALVAMENTO PROCV COM MAPA RIGOROSO
                        if btn_salvar_dados:
                            if "df_original_cache" in st.session_state:
                                df_orig = st.session_state.df_original_cache
                                alteracoes_detectadas = 0
                                
                                try:
                                    scope = [
                                        "https://www.googleapis.com/auth/spreadsheets",
                                        "https://www.googleapis.com/auth/drive"
                                    ]
                                    creds_dict = dict(st.secrets["gcp_service_account"])
                                    email_servico = creds_dict.get("client_email", "desconhecido")
                                    
                                    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                                    client = gspread.authorize(creds)
                                    
                                    spreadsheet = client.open_by_key(FILE_ID)
                                    try:
                                        worksheet = spreadsheet.worksheet("Pedidos")
                                    except:
                                        worksheet = spreadsheet.get_worksheet(0)
                                    
                                    dados_planilha = worksheet.get_all_values()
                                    cabecalho_bruto = dados_planilha[0]
                                    cabecalho_map = {c.upper().strip().replace('Í', 'I').replace('Ã', 'A'): i + 1 for i, c in enumerate(cabecalho_bruto)}
                                    
                                    for idx in edited_df.index:
                                        linha_planilha = int(edited_df.loc[idx, "_row_idx"])
                                        for col in edited_df.columns:
                                            if col == "_row_idx":
                                                continue
                                            
                                            valor_antigo = str(df_orig.loc[idx, col])
                                            valor_novo = str(edited_df.loc[idx, col])
                                            
                                            if valor_antigo != valor_novo:
                                                col_config_item = next((item for item in DICIONARIO_COLUNAS_EXATAS if item["tela"] == col), None)
                                                if col_config_item:
                                                    col_index = None
                                                    for alt in col_config_item["planilha"]:
                                                        alt_clean = alt.upper().strip().replace('Í', 'I').replace('Ã', 'A')
                                                        col_index = cabecalho_map.get(alt_clean)
                                                        if col_index:
                                                            break
                                                    
                                                    if col_index:
                                                        worksheet.update_cell(linha_planilha, col_index, valor_novo)
                                                        alteracoes_detectadas += 1
                                                        
                                    if alteracoes_detectadas > 0:
                                        st.success(f"✅ {alteracoes_detectadas} alteração(ões) gravada(s) com sucesso na planilha!")
                                        st.session_state.df_original_cache = edited_df.copy()
                                        st.cache_data.clear()
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
                    st.markdown('<div class="custom-error-red">⚠️ Nenhum registro correspondente encontrado com os filtros informados.</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="custom-error-red">⚠️ Nenhum registro correspondente encontrado.</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="custom-error-red">⚠️ Erro ao processar os dados da busca: {e}</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="custom-welcome-salutation">👋 Olá! Seja bem-vindo ao Portal de Gestão de Compras. Utilize os Filtros Avançados acima para pesquisar.</div>', unsafe_allow_html=True)

# 10. RODAPÉ INSTITUCIONAL
st.markdown("<div class=\"custom-footer-block\"><p style='color:#64748b; font-size:13px; font-weight:600; margin:0;'>Parente Andrade | Coordenação de Suprimentos</p></div>", unsafe_allow_html=True)

# 11. MARCA D'ÁGUA FIXA EXCLUSIVA DA AUTORIA
st.markdown('<div class="signature-fixed">Created by SS.</div>', unsafe_allow_html=True)
