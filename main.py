import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Suprimentos | Parente Andrade", layout="wide")

# 2. FUNÇÃO PARA CONECTAR AO GOOGLE SHEETS (ESCRITA)
def conectar_google_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Puxa as credenciais que você salvou nos Secrets
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    # Abre a planilha pelo ID (extraído da sua URL)
    return client.open_by_key("1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP")

# 3. CARREGAMENTO DE DADOS
@st.cache_data(ttl=60)
def carregar_dados_gsheets():
    sh = conectar_google_sheets()
    worksheet = sh.get_worksheet(0) # Pega a primeira aba
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Padronização de códigos (Zeros à esquerda)
    if 'Produto' in df.columns:
        df['Produto'] = df['Produto'].astype(str).str.zfill(10)
    if 'N° da SC' in df.columns:
        df['N° da SC'] = df['N° da SC'].astype(str).str.zfill(7)
        
    return df

# 4. INTERFACE
st.subheader("🏗️ Gestão de Suprimentos - Parente Andrade")
busca = st.text_input("🔍 Pesquisar...")

df = carregar_dados_gsheets()

if not df.empty:
    # Ordem das colunas conforme solicitado
    col_v = [
        "STATUS", "N° da SC", "N° PC", "CC", "Nome Fornecedor", "Produto", 
        "Descricao", "UM", "QNT", " Prc Unitario", " Vlr.Total", 
        "Data Emissao", "Dt Liberacao", "DT Envio", "CONDIÇÃO PGO", 
        "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega "
    ]
    cols = [c for c in col_v if c in df.columns]
    
    df_display = df[cols].copy()
    if busca:
        mask = df_display.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_display = df_display[mask]

    # EDITOR DE DADOS
    st.info("💡 Altere as datas abaixo e clique em 'GRAVAR NA PLANILHA' para salvar.")
    df_editado = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=True,
        disabled=[c for c in cols if c not in ["DT Pgo (AVISTA)", "DT entrega "]]
    )

    # BOTÃO DE SALVAR
    if st.button("💾 GRAVAR NA PLANILHA"):
        try:
            sh = conectar_google_sheets()
            worksheet = sh.get_worksheet(0)
            
            # Atualiza a planilha original com os novos dados editados
            # Nota: Esta abordagem subscreve os dados editados na aba
            df_final = df.copy()
            df_final.update(df_editado)
            
            # Converte de volta para lista e envia
            dados_para_salvar = [df_final.columns.values.tolist()] + df_final.values.tolist()
            worksheet.update('A1', dados_para_salvar)
            
            st.success("✅ Datas atualizadas com sucesso na Planilha Mãe!")
            st.cache_data.clear() # Limpa o cache para mostrar o dado novo
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
