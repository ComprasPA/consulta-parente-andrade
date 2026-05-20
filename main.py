import streamlit as st
import pandas as pd
import base64
import re
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
    except: 
        return None

base64_logo = get_base64_logo()

# 3. CSS (DESIGN PADRÃO CONGELADO)
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f0f2f6; }}
    .header-wrapper {{
        border: 2px solid #478c3b; border-radius: 10px; padding: 15px 25px;
        background-color: #ffffff; display: flex; align-items: center;
        justify-content: space-between; margin-top: 10px; margin-bottom: 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }}
    .portal-title {{ color: #000000 !important; font-size: 35px !important; font-weight: bold !important; margin: 0 !important; }}
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; padding: 0px 10px !important; 
        border-radius: 8px; border: 2px solid #478c3b !important; margin: 0 !important;
    }}
    .status-box {{ background-color: #478c3b; color: white; padding: 12px 20px; border-radius: 10px; font-weight: bold; font-size: 18px; }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO COM BOTÃO DE ATUALIZAÇÃO FORÇADA
st.markdown('<div class="header-wrapper">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([1.2, 4.5, 1.3, 2.3])
with c1:
    if base64_logo: 
        st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:140px;">', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="portal-title">Portal Gestão de Compras Parente Andrade</p>', unsafe_allow_html=True)
with c3:
    if st.button("🔄 Atualizar Base", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with c4:
    busca = st.text_input("", placeholder="🔍 Digite SC ou Pedido...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# 5. MAPEAMENTO DE POSIÇÃO INDEPENDENTE DE MUDANÇA DE NOME
# ==========================================
# Mapeia o nome amigável diretamente para o índice físico real (Coluna A = 0, Coluna B = 1, etc.)
# Baseado estritamente na sua lista de colunas fornecida.
MAPEAMENTO_POSICIONAL = [
    {"label": "STATUS", "index": 1, "tipo": "texto"},
    {"label": "Data Envio", "index": 2, "tipo": "data"},
    {"label": "Data Pgo (AVISTA)", "index": 3, "tipo": "data"},
    {"label": "Data Prev de Entrega", "index": 4, "tipo": "data"},
    {"label": "Data Entrega Real", "index": 5, "tipo": "data"},
    {"label": "Condição de Pagamento", "index": 6, "tipo": "texto"}, # Corrigido item 1 (Índice 6 = CONDIÇÃO PGO)
    {"label": "Nº Solicitação (SC)", "index": 7, "tipo": "texto"},
    {"label": "Nº Pedido (PC)", "index": 8, "tipo": "pedido"},       # Inteligência de zeros à esquerda (item 3)
    {"label": "Cód. Fornecedor", "index": 9, "tipo": "texto"},
    {"label": "Fornecedor", "index": 10, "tipo": "texto"},          # Item 4 corrigido (Nome Fornece)
    {"label": "Centro Custo", "index": 11, "tipo": "texto"},
    {"label": "Produto", "index": 12, "tipo": "texto"},
    {"label": "Descrição", "index": 13, "tipo": "texto"},
    {"label": "UM", "index": 14, "tipo": "texto"},                   # Item 6 corrigido (Unidade)
    {"label": "Quantidade", "index": 15, "tipo": "texto"},
    {"label": "Preço Unitário", "index": 16, "tipo": "texto"},       # Item 6 corrigido (Prc Unitario)
    {"label": "Valor Total", "index": 17, "tipo": "texto"},          # Item 6 corrigido (Vlr.Total)
    {"label": "Data Emissão", "index": 18, "tipo": "data"},
    {"label": "Data Liberação PC", "index": 19, "tipo": "data"},     # Item 7 corrigido (Dt Lib. PC)
    {"label": "Data Baixa", "index": 30, "tipo": "data"},
    {"label": "Observação", "index": 31, "tipo": "texto"}
]

# Formata o código do pedido preenchendo com zeros à esquerda até atingir 10 dígitos
def formatar_codigo_10_digitos(valor):
    val_limpo = str(valor).split('.')[0].strip() # Remove casas decimais do Excel (.0)
    if val_limpo and val_limpo.lower() != 'nan' and val_limpo != '0':
        return val_limpo.zfill(10)
    return val_limpo

@st.cache_data(ttl=60)
def carregar_dados_seguros():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # Carrega as abas mantendo o tipo original como string, mas sem cabeçalhos rígidos para indexar por número
        df_pc = pd.read_excel(excel, sheet_name=0, header=None, dtype=str).fillna('')
        
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, header=None, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        
        return df_pc, df_sc
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_dados_seguros()


# ==========================================
# 6. LÓGICA DE BUSCA INTEGRADA E PREENCHIMENTO
# ==========================================
if busca:
    t = busca.lower().strip()
    
    # Tratamento da busca do usuário: se for número puro, testa com os zeros à esquerda para casar com os 10 dígitos
    t_10 = t.zfill(10) if t.isdigit() else t
    
    # Executa varredura ampla na aba de Pedidos (PC)
    if not df_pc.empty:
        # Pula a primeira linha (cabeçalho da planilha) na varredura de dados
        dados_corpo_pc = df_pc.iloc[1:]
        res_pc = dados_corpo_pc[dados_corpo_pc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any() or r.astype(str).str.lower().str.contains(t_10, na=False).any(), axis=1)]
    else:
        res_pc = pd.DataFrame()
    
    if not res_pc.empty:
        df_final = res_pc.copy()
        origem = "Planilha de Pedidos (PC)"
    else:
        # Se não localizar na PC, varre a de Solicitações (SC)
        if not df_sc.empty:
            dados_corpo_sc = df_sc.iloc[1:]
            res_sc = dados_corpo_sc[dados_corpo_sc.apply(lambda r: r.astype(str).str.lower().str.contains(t, na=False).any(), axis=1)]
        else:
            res_sc = pd.DataFrame()
            
        if not res_sc.empty:
            df_final = res_sc.copy()
            origem = "Planilha de Solicitações (SC)"
        else:
            df_final = pd.DataFrame()

    if not df_final.empty:
        # Montagem do DataFrame final mapeado por coluna física absoluta
        df_painel = pd.DataFrame(index=df_final.index)
        
        for config in MAPEAMENTO_POSICIONAL:
            nome_coluna_tela = config["label"]
            idx_coluna_planilha = config["index"]
            tipo_dado = config["tipo"]
            
            # Garante que o índice existe no corte da planilha para não estourar erro
            if idx_coluna_planilha < len(df_final.columns):
                valores_originais = df_final.iloc[:, idx_coluna_planilha]
                
                if tipo_dado == "data":
                    # Limpeza agressiva e formatação padrão Brasil (DD/MM/AA)
                    datas_limpas = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    datas_limpas = datas_limpas.replace(['nan', 'NONE', '', '0'], '')
                    df_painel[nome_coluna_tela] = pd.to_datetime(datas_limpas, errors='coerce', format='mixed').dt.strftime('%d/%m/%y').fillna('')
                
                elif tipo_dado == "pedido":
                    # Aplica a regra de 10 dígitos com zeros à esquerda (Item 3)
                    df_painel[nome_coluna_tela] = valores_originais.apply(formatar_codigo_10_digitos)
                
                else:
                    # Texto normal (Limpa resíduos de ponto flutuante do Excel)
                    df_painel[nome_coluna_tela] = valores_originais.astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
            else:
                df_painel[nome_coluna_tela] = ""

        # Força inteligência de status padrão para abas de SC vazias
        if origem == "Planilha de Solicitações (SC)":
            df_painel["STATUS"] = "SC ABERTA"

        st.markdown(f'<div class="status-box">🟢 Dados Vinculados de: {origem}</div>', unsafe_allow_html=True)
        st.write("")
        
        # Download do Excel Tratado
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: 
            df_painel.to_excel(wr, index=False)
        
        st.download_button(
            label="📥 DESCARREGAR RELATÓRIO",
            data=out.getvalue(),
            file_name="Portal_Compras_Parente.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Exibição limpa na tela
        st.dataframe(df_painel, use_container_width=True, hide_index=True)
    else:
        st.warning(f"⚠️ Nenhum registro localizado para: '{busca}'")
else:
    st.info("💡 Digite o número da SC ou Pedido para iniciar. O sistema busca automaticamente considerando zeros à esquerda.")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
