import streamlit as st
import pandas as pd
import base64
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Suprimentos | Parente Andrade", layout="wide")

# 2. FUNÇÃO LOGO
@st.cache_data(ttl=600)
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

# 3. CARREGAMENTO DOS DADOS (Refeito para evitar Erro 400)
URL_BASE = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP"

@st.cache_data(ttl=300)
def carregar_dados():
    # --- CONFIGURAÇÃO DOS GIDS ---
    # GID 0 costuma ser a aba 'SCM SILVIO' 
    # VOCÊ DEVE CONFIRMAR O GID DA ABA 'Protheus SC (2)' NA URL DO NAVEGADOR
    gid_follow_up = "0" 
    gid_protheus_sc = "1626027376" # <--- TROQUE ESTE NÚMERO PELO GID DA ABA 2

    def fetch_csv(gid):
        url = f"{URL_BASE}/export?format=csv&gid={gid}"
        return pd.read_csv(url, dtype=str).fillna('')

    try:
        # Carrega as abas
        df_pedidos = fetch_csv(gid_follow_up)
        
        try:
            df_sc = fetch_csv(gid_protheus_sc)
        except:
            st.warning("⚠️ Aba 'Protheus SC (2)' não encontrada. Exibindo apenas Follow Up.")
            df_sc = pd.DataFrame()

        # Padronização
        if 'N° da SC' in df_pedidos.columns:
            df_pedidos['N° da SC'] = df_pedidos['N° da SC'].astype(str).str.zfill(7)
        
        # Merge de Cotação
        if not df_sc.empty:
            # Identifica coluna de SC na aba 2
            col_sc2 = 'Numero da SC' if 'Numero da SC' in df_sc.columns else 'Solicitação'
            df_sc[col_sc2] = df_sc[col_sc2].astype(str).str.zfill(7)
            
            # Realiza o PROCV (Merge)
            df_merged = pd.merge(df_pedidos, df_sc[[col_sc2, 'Código Cotação']], 
                                left_on='N° da SC', right_on=col_sc2, 
                                how='left').fillna('')
        else:
            df_merged = df_pedidos

        # Formatação de Datas
        datas = ["Data Emissao", "Dt Liberacao", "DT Envio", "DT entrega "]
        for d in datas:
            if d in df_merged.columns:
                df_merged[d] = pd.to_datetime(df_merged[d], errors='coerce').dt.strftime('%d/%m/%y')

        return df_merged.fillna('-')
    except Exception as e:
        st.error(f"Erro crítico no Google Sheets: {e}")
        return None

# --- INTERFACE ---
df = carregar_dados()

if df is not None:
    busca = st.text_input("🔍 Busca rápida:", placeholder="Digite SC ou Pedido...")
    
    if busca:
        mask = df.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)
        df = df[mask]

    # Colunas em ordem: Status -> SC -> Cotação -> Pedido
    cols_final = [
        "Status", "N° da SC", "Código Cotação", "PC", "CCs", "Solicitante", 
        "Descrição", "Tipo", "Data Emissao", "Dt. Aprovação Cotação"
    ]
    
    # Filtra apenas colunas que realmente existem no DF
    cols_existentes = [c for c in cols_final if c in df.columns]
    
    st.dataframe(df[cols_existentes], use_container_width=True, hide_index=True)
