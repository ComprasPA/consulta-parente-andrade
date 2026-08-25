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
    .custom-footer-block { text-align: center !important; margin-top: 60px !important; border-top: 1px solid #e2e8f0 !important; padding-top: 24px !important; padding-bottom: 24px !important; position: static !important; clear: both !important; width: 100% !important; display: block !important; }
    .signature-fixed { position: fixed; bottom: 12px; left: 20px; color: #94a3b8; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; z-index: 999999; pointer-events: none; }
    </style>
    """, unsafe_allow_html=True)

FILE_ID = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"

# 4. CARREGAMENTO COM ESTADO
def carregar_dados_seguros():
    URL_CSV = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv&gid=0"
    try:
        df = pd.read_csv(URL_CSV, dtype=str).fillna('')
        if "<html" in str(df.columns[0]).lower():
            raise ValueError("O Google retornou bloqueio HTML.")
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e_csv:
        try:
            URL_XLSX = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=xlsx"
            excel = pd.ExcelFile(URL_XLSX, engine='openpyxl')
            aba = "Pedidos_App" if "Pedidos_App" in excel.sheet_names else ("Pedidos" if "Pedidos" in excel.sheet_names else excel.sheet_names[0])
            df = pd.read_excel(excel, sheet_name=aba, dtype=str).fillna('')
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception as e_xlsx:
            st.session_state.erro_tecnico = f"CSV: {str(e_csv)} | XLSX: {str(e_xlsx)}"
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

if st.session_state.autenticado:
    st.info(f"🟢 Sessão Ativa: Operador **{st.session_state.departamento_ativo.upper()}** (Modo Edição Liberado)")

# 7. FILTROS E LÓGICA DE GAVETA (Ordem: Pedido, Solicitação, Centro de Custo, Status e Data)
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
                lista_status = ["Todos"] + sorted([str(x).strip() for x in df_pc[col_status_verificacao].unique() if str(x).strip() != ""])
            else:
                lista_status = ["Todos"]
            idx_padrao = lista_status.index(st.session_state.filtro_status_val) if st.session_state.filtro_status_val in lista_status else 0
            filtro_status = st.selectbox("Status:", options=lista_status, index=idx_padrao)
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

# 8. MAPEAMENTO EXATO DAS COLUNAS
DICIONARIO_COLUNAS_EXATAS = [
    {"planilha": "STATUS", "tela": "STATUS", "tipo": "texto"},
    {"planilha": "CENTRO DE CUSTO", "tela": "Centro de Custo", "tipo": "texto"},
    {"planilha": "SOLICITAÇÃO", "tela": "Solicitação", "tipo": "texto"},
    {"planilha": "PEDIDO", "tela": "Pedidos", "tipo": "pedido"},   
    {"planilha": "CONDIÇÃO PAGAMENTO", "tela": "Condição Pagamento", "tipo": "texto"},
    {"planilha": "EMISSÃO", "tela": "Emissão", "tipo": "data"},
    {"planilha": "APROVAÇÃO", "tela": "Aprovação", "tipo": "data"},
    {"planilha": "ENVIO", "tela": "Envio", "tipo": "data"},
    {"planilha": "PAGAMENTO", "tela": "Pagamento", "tipo": "texto"}, 
    {"planilha": "PREVISÃO DE ENTREGA", "tela": "Previsão de entrega", "tipo": "data"},
    {"planilha": "ENTREGA", "tela": "Entrega", "tipo": "data"},
    {"planilha": "FORNECEDOR", "tela": "Fornecedor", "tipo": "texto"},
    {"planilha": "GRUPO", "tela": "Grupo", "tipo": "texto"},
    {"planilha": "PRODUTO", "tela": "Produto", "tipo": "produto"},                 
    {"planilha": "DESCRIÇÃO", "tela": "Descrição", "tipo": "texto"},
    {"planilha": "UM", "tela": "UM", "tipo": "texto"},
    {"planilha": "QTD", "tela": "Qtd", "tipo": "numero"},
    {"planilha": "PREÇO UNITÁRIO", "tela": "Preço Unitário", "tipo": "moeda"},
    {"planilha": "VALOR TOTAL", "tela": "Valor Total", "tipo": "moeda"},
    {"planilha": "NF REMESSA", "tela": "NF Remessa", "tipo": "texto"}
]

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

# 9. MOTOR DE BUSCA ROBUSTO E FLEXÍVEL
tem_busca_ativa = st.session_state.filtro_pc_val or st.session_state.filtro_sc_val or st.session_state.filtro_cc_val or st.session_state.filtro_status_val != "Todos" or bool(st.session_state.filtro_data_val)

if tem_busca_ativa:
    if df_pc.empty:
        st.markdown('<div class="custom-error-red">⚠️ Base de dados vazia. Clique em "🔄 Atualizar Banco" nos Filtros Avançados.</div>', unsafe_allow_html=True)
    else:
        df_final = df_pc.copy()
        
        # Filtro Robusto para Pedido (PC) - Converte para string limpa sem casas decimais ou zeros excedentes para garantir o match
        if st.session_state.filtro_pc_val:
            pc_termo = str(st.session_state.filtro_pc_val).strip()
            col_pc = next((c for c in df_final.columns if "PEDIDO" in c.upper() or "PEDIDOS" in c.upper()), None)
            if col_pc and col_pc in df_final.columns:
                df_final = df_final[df_final[col_pc].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.contains(pc_termo, na=False)]

        # Filtro Robusto para Solicitação (SC)
        if st.session_state.filtro_sc_val:
            sc_termo = str(st.session_state.filtro_sc_val).strip()
            col_sc = next((c for c in df_final.columns if "SOLICITA" in c.upper()), None)
            if col_sc and col_sc in df_final.columns:
                df_final = df_final[df_final[col_sc].astype(str).str.replace(r'\.0$', '', regex=True).str.strip().str.contains(sc_termo, na=False)]

        # Filtro de Centro de Custo
        if st.session_state.filtro_cc_val:
            cc_termo = st.session_state.filtro_cc_val.strip().lower()
            col_cc = next((c for c in df_final.columns if "CUSTO" in c.upper() or "CC" in c.upper()), None)
            if col_cc and col_cc in df_final.columns:
                df_final = df_final[df_final[col_cc].astype(str).str.lower().str.contains(cc_termo, na=False)]

        # Filtro de Status
        col_status_verificacao = next((c for c in df_pc.columns if "STATUS" in c.upper()), None)
        if st.session_state.filtro_status_val != "Todos" and col_status_verificacao:
            df_final = df_final[df_final[col_status_verificacao].astype(str).str.strip() == st.session_state.filtro_status_val]

        # Filtro de Data de Emissão
        if st.session_state.filtro_data_val and len(st.session_state.filtro_data_val) == 2:
            if st.session_state.filtro_data_val[0] is not None and st.session_state.filtro_data_val[1] is not None:
                col_emissao_original = next((c for c in df_pc.columns if "EMISSAO" in c.upper() or "EMISSÃO" in c.upper()), None)
                if col_emissao_original:
                    datas_convertidas = pd.to_datetime(df_final[col_emissao_original], errors='coerce', format='mixed', dayfirst=True).dt.date
                    df_final = df_final[(datas_convertidas >= st.session_state.filtro_data_val[0]) & (datas_convertidas <= st.session_state.filtro_data_val[1])]

        try:
            if not df_final.empty:
                df_painel = pd.DataFrame(index=df_final.index)
                
                for col_config in DICIONARIO_COLUNAS_EXATAS:
                    nome_alvo = col_config["planilha"].strip().upper()
                    nome_exibicao_tela = col_config["tela"]
                    tipo_campo = col_config["tipo"]
                    
                    col_real = None
                    for c in df_final.columns:
                        c_up = c.strip().upper()
                        if c_up == nome_alvo or c_up.replace("Ã", "A").replace("Ç", "C").replace("Õ", "O") == nome_alvo.replace("Ã", "A").replace("Ç", "C").replace("Õ", "O"):
                            col_real = c
                            break
                    
                    if not col_real:
                        for c in df_final.columns:
                            c_up = c.strip().upper()
                            if nome_alvo in c_up or c_up in nome_alvo:
                                col_real = c
                                break

                    if col_real:
                        valores_originais = df_final[col_real]
                        if tipo_campo == "data":
                            df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).str.strip().replace(['nan', 'NONE', '', '0'], '')
                        elif tipo_campo == "pedido":
                            df_painel[nome_exibicao_tela] = valores_originais.apply(lambda val: str(val).split('.')[0].strip().zfill(6) if str(val).strip() and str(val).lower() != 'nan' else "")
                        elif tipo_campo == "produto":
                            df_painel[nome_exibicao_tela] = valores_originais.apply(lambda val: str(val).split('.')[0].strip().zfill(10) if str(val).strip() and str(val).lower() != 'nan' else "")
                        elif tipo_campo in ["moeda", "numero"]:
                            df_painel[nome_exibicao_tela] = valores_originais.apply(converter_para_numerico)
                        else:
                            df_painel[nome_exibicao_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '').str.strip()
                    else:
                        df_painel[nome_exibicao_tela] = ""

                col_status_tela = next((c for c in df_painel.columns if "STATUS" in c.upper()), None)
                if col_status_tela:
                    termos_excecao = ["SERVIÇO", "CANCELADO PELO SOLICITANTE", "REJEITADO PELO APROVADOR", "COMPRA DIRETA"]
                    mask_status = df_painel[col_status_tela].astype(str).str.upper().apply(
                        lambda s: any(t in s for t in termos_excecao)
                    )
                    for col_nome in ["Previsão de entrega", "Entrega"]:
                        if col_nome in df_painel.columns:
                            df_painel.loc[mask_status, col_nome] = "N/A"

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
                        df_painel[col_data] = df_painel[col_data].apply(
                            lambda x: x if str(x).upper() == "N/A" else formatar_para_dd_mm_aaaa(x)
                        )

                df_painel = df_painel.dropna(how='all')

                if not df_painel.empty:
                    txt_status = f"🔍 Registros Localizados ({len(df_painel)} itens)"
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
                            file_name=f"Relatorio_Compras_Filtro.xlsx",
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

                    if st.session_state.autenticado:
                        st.info(f"✏️ Modo Operador Ativo ({st.session_state.departamento_ativo.upper()}): Edite os campos e clique em 'Salvar Alterações'.")
                        
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
                        
                        if st.button("💾 Salvar Alterações"):
                            try:
                                scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                                creds_dict = dict(st.secrets["gcp_service_account"])
                                creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                                client = gspread.authorize(creds)
                                
                                spreadsheet = client.open_by_key(FILE_ID)
                                worksheet = spreadsheet.get_worksheet(0)
                                
                                dados_planilha = worksheet.get_all_values()
                                cabecalho = dados_planilha[0]
                                
                                alteracoes_realizadas = 0
                                df_orig = st.session_state.df_original_cache
                                
                                for idx in edited_df.index:
                                    for col in edited_df.columns:
                                        valor_antigo = str(df_orig.loc[idx, col])
                                        valor_novo = str(edited_df.loc[idx, col])
                                        
                                        if valor_antigo != valor_novo:
                                            linha_planilha = int(df_final.index[idx]) + 2
                                            col_config_item = next((item for item in DICIONARIO_COLUNAS_EXATAS if item["tela"] == col), None)
                                            if col_config_item:
                                                nome_col_planilha = col_config_item["planilha"]
                                                if nome_col_planilha in cabecalho:
                                                    col_index = cabecalho.index(nome_col_planilha) + 1
                                                    worksheet.update_cell(linha_planilha, col_index, valor_novo)
                                                    alteracoes_realizadas += 1

                                if alteracoes_realizadas > 0:
                                    st.success(f"✅ {alteracoes_realizadas} alteração(ões) salva(s) com sucesso na planilha do Google Sheets!")
                                    st.session_state.atualizar_cache_editor = True
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.info("ℹ️ Nenhuma alteração foi detectada para salvar.")
                                    
                            except Exception as e:
                                st.error(f"❌ Erro ao salvar no Google Sheets: {e}")
                    else:
                        st.success("👁️ Modo Usuário Ativo: Visualização somente leitura.")
                        st.dataframe(
                            df_painel, 
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
