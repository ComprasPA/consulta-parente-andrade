import streamlit as st
import pandas as pd
import base64
import re
from datetime import datetime, timedelta
from io import BytesIO

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
    except: return None

base64_logo = get_base64_logo()

# 3. CSS MODERNIZADO
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    div[data-testid="stElementToolbar"] {{ display: none !important; }}
    .stApp {{ background-color: #f8fafc; font-family: 'Inter', sans-serif; }}
    .header-modern {{ background: #ffffff; padding: 16px 24px; border-radius: 12px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .portal-title {{ color: #1e293b !important; font-size: 38px !important; font-weight: 800 !important; margin: 0 auto !important; }}
    .status-card {{ background: #ffffff; padding: 16px 24px; border-radius: 8px; font-weight: 600; border-left: 5px solid #478c3b; margin-bottom: 16px; width: 100%; }}
    .custom-error-red {{ background-color: #fee2e2 !important; color: #991b1b !important; padding: 16px 24px; border-radius: 8px; font-weight: 600; border-left: 5px solid #ef4444; margin-bottom: 16px; width: 100%; }}
    .custom-info-blue {{ background-color: #e0f2fe !important; color: #0369a1 !important; padding: 16px 24px; border-radius: 8px; font-weight: 600; border-left: 5px solid #0284c7; margin-bottom: 16px; width: 100%; }}
    .custom-footer-block {{ text-align: center !important; margin-top: 60px !important; border-top: 1px solid #e2e8f0 !important; padding: 24px !important; }}
    .signature-fixed {{ position: fixed; bottom: 12px; left: 20px; color: #94a3b8; font-size: 11px; font-weight: 700; }}
    </style>
    """, unsafe_allow_html=True)

# 4. ENGENHARIA DE INGESTÃO (Conexão direta corrigida para arquivos .xlsx)
@st.cache_data(ttl=10)
def carregar_dados_seguros():
    # ID do seu arquivo extraído do link
    file_id = "1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP"
    # URL de download direto para arquivos não-nativos do Google Sheets
    URL_DIRETA = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    try:
        excel = pd.ExcelFile(URL_DIRETA, engine='openpyxl')
        
        # Procura inteligentemente a guia que contém "PEDIDO" no nome
        aba_alvo = excel.sheet_names[0]
        for aba in excel.sheet_names:
            if "PEDIDO" in aba.upper():
                aba_alvo = aba
                break
                
        df = pd.read_excel(excel, sheet_name=aba_alvo, dtype=str).fillna('')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        # Fallback caso a URL direta falhe, tenta a URL antiga do Sheets
        try:
            URL_ALT = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"
            excel = pd.ExcelFile(URL_ALT, engine='openpyxl')
            aba_alvo = excel.sheet_names[0]
            for aba in excel.sheet_names:
                if "PEDIDO" in aba.upper():
                    aba_alvo = aba
                    break
            df = pd.read_excel(excel, sheet_name=aba_alvo, dtype=str).fillna('')
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception as e2:
            st.session_state.erro_drive = str(e2)
            return pd.DataFrame()

df_pc = carregar_dados_seguros()

# Identificação Dinâmica de Colunas (Evita falhas se o Excel tiver espaços extras no título)
col_cc = next((c for c in df_pc.columns if "CENTRO" in c.upper() or "CC" in c.upper()), "Centro de Custo")
col_ped = next((c for c in df_pc.columns if "PEDIDO" in c.upper()), "Pedido")
col_sol = next((c for c in df_pc.columns if "SOLICITACAO" in c.upper() or "SC" in c.upper()), "Solicitação")
col_stat = next((c for c in df_pc.columns if "STATUS" in c.upper()), None)

# CABEÇALHO
st.markdown('<div class="header-modern">', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.5, 6.5, 2.0])
with c2: st.markdown('<div class="center-title-container"><p class="portal-title">Portal Gestão de Compras</p></div>', unsafe_allow_html=True)
with c3: busca = st.text_input("", placeholder="🔍 Rastrear SC, PC ou CC...")
st.markdown('</div>', unsafe_allow_html=True)

# Exibe o erro do Drive se houver falha de conexão (Apenas para nós sabermos o que está bloqueando)
if df_pc.empty and "erro_drive" in st.session_state:
    st.markdown(f'<div class="custom-error-red">⚠️ O Google Drive bloqueou o download do arquivo Excel. Detalhe técnico: {st.session_state.erro_drive}</div>', unsafe_allow_html=True)

# GAVETA DE FILTROS 
if "filtro_status_val" not in st.session_state: st.session_state.filtro_status_val = "Todos"
with st.expander("Filtros Avançados ▼"):
    with st.form("form_filtros"):
        col1, col2 = st.columns([1, 1])
        opcoes_status = ["Todos"] + sorted(list(set(df_pc[col_stat].astype(str)))) if col_stat and not df_pc.empty else ["Todos"]
        filtro_status = col1.selectbox("Status", opcoes_status)
        if col2.form_submit_button("Pesquisar"):
            st.session_state.filtro_status_val = filtro_status
            st.rerun()

# 6. MOTOR DE BUSCA INDUSTRIAL
if busca:
    termo = busca.strip()
    df_final = pd.DataFrame()
    modo_cc = len(termo) == 4 and termo.isdigit()
    
    try:
        if not df_pc.empty:
            # A) Busca por Centro de Custo
            if modo_cc:
                if col_cc in df_pc.columns:
                    df_final = df_pc[df_pc[col_cc].astype(str).str.contains(termo, na=False)].copy()
            
            # B) Busca por Pedido ou Solicitação
            else:
                termo_limpo = re.sub(r'[^0-9]', '', termo)
                if termo_limpo and (col_ped or col_sol):
                    val = int(termo_limpo)
                    if val >= 170000:
                        df_final = df_pc[df_pc[col_ped].astype(str).str.replace(r'\.0$', '', regex=True).str.strip() == termo_limpo].copy() if col_ped in df_pc.columns else df_final
                    else:
                        df_final = df_pc[df_pc[col_sol].astype(str).str.replace(r'\.0$', '', regex=True).str.strip() == termo_limpo].copy() if col_sol in df_pc.columns else df_final
            
            # Filtro de Status
            if not df_final.empty and st.session_state.filtro_status_val != "Todos" and col_stat:
                df_final = df_final[df_final[col_stat] == st.session_state.filtro_status_val]

            # Exibição
            if not df_final.empty:
                st.markdown(f'<div class="status-card">🔍 Resultados encontrados: {termo}</div>', unsafe_allow_html=True)
                st.dataframe(df_final, use_container_width=True)
            else:
                if modo_cc: st.markdown(f'<div class="custom-error-red">⚠️ Nenhum registro encontrado para o Centro de Custo: {termo}</div>', unsafe_allow_html=True)
                elif termo.isdigit() and int(re.sub(r'[^0-9]', '', termo)) >= 170000: st.markdown(f'<div class="custom-error-red">⚠️ Pedido {termo} não localizado.</div>', unsafe_allow_html=True)
                else: st.markdown('<div class="custom-info-blue">⏳ Solicitação em cotação ou não localizada.</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro no motor de busca: {e}")

# RODAPÉ
st.markdown("<div class=\"custom-footer-block\"><p style='color:#64748b; font-size:13px;'>Parente Andrade | Coordenação de Suprimentos</p></div>", unsafe_allow_html=True)
st.markdown('<div class="signature-fixed">Created by SS.</div>', unsafe_allow_html=True)
