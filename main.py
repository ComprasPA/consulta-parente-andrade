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
    busca = st.text_input("", placeholder="🔍 Digite o número da SC...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# 5. ESTRUTURA DE COLUNAS REORGANIZADA (NOVA ORDEM)
# ==========================================
DICIONARIO_COLUNAS_EXATAS = [
    {"planilha": "STATUS", "tela": "STATUS", "tipo": "texto"},
    {"planilha": "Centro de Custo (CC)", "tela": "Centro de Custo (CC)", "tipo": "texto"},
    {"planilha": "Nº Solicitação (SC)", "tela": "Nº Solicitação (SC)", "tipo": "texto"},
    {"planilha": "Nº Pedido (PC)", "tela": "Nº Pedido (PC)", "tipo": "pedido"},   
    {"planilha": "Condição Pagamento", "tela": "Condição Pagamento", "tipo": "texto"},
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
    {"planilha": "Valor Total", "tela": "Valor Total", "tipo": "moeda"},
    {"planilha": "Data Emissao", "tela": "Data Emissão", "tipo": "data"},
    {"planilha": "Data Liberação", "tela": "Data Liberação", "tipo": "data"}
]

# Formata strings numéricas limpando flutuantes .0 do Excel e preenchendo zeros à esquerda
def ajustar_zeros_protheus(valor, tamanho_alvo):
    val_limpo = str(valor).split('.')[0].strip()
    if val_limpo and val_limpo.lower() != 'nan' and val_limpo != '0':
        return val_limpo.zfill(tamanho_alvo)
    return val_limpo

# Converte strings de preço/valores para float numérico válido
def converter_para_numerico(valor):
    if not valor or str(valor).lower() == 'nan':
        return 0.0
    dado = str(valor).replace('.', '').replace(',', '.').strip()
    try:
        return float(dado)
    except:
        return 0.0

# Formata qualquer string ou objeto de data estritamente para DD/MM/AA
def formatar_para_dd_mm_aa(valor):
    txt = str(valor).strip()
    if txt == "" or txt.lower() in ["nan", "none", "0", "n/a"]:
        return txt
    try:
        return pd.to_datetime(txt, errors='coerce', format='mixed').strftime('%d/%m/%y')
    except:
        return txt

@st.cache_data(ttl=60)
def carregar_dados_seguros():
    URL = "https://docs.google.com/spreadsheets/d/1_wdQoseqhvB_upb5psRLPCN2SPaZKCHP/export?format=xlsx"
    try:
        excel = pd.ExcelFile(URL, engine='openpyxl')
        
        # Carrega a primeira aba (Pedidos / PC)
        df_pc = pd.read_excel(excel, sheet_name=0, dtype=str).fillna('')
        df_pc.columns = [str(c).strip() for c in df_pc.columns]
        
        # Carrega a segunda aba (Solicitações / SC)
        aba_sc_nome = next((s for s in excel.sheet_names if "SC" in s.upper() and s != excel.sheet_names[0]), None)
        df_sc = pd.read_excel(excel, sheet_name=aba_sc_nome, dtype=str).fillna('') if aba_sc_nome else pd.DataFrame()
        df_sc.columns = [str(c).strip() for c in df_sc.columns]
        
        return df_pc, df_sc
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

df_pc, df_sc = carregar_dados_seguros()


# ==========================================
# 6. LÓGICA DE PROCV ROBUSTA (PC -> SC)
# ==========================================
if busca:
    # Higieniza o termo buscado removendo decimais flutuantes se houver
    t = busca.lower().split('.')[0].strip()
    
    # Prepara os padrões de texto comuns para a busca do Protheus
    t_puro = str(int(t)) if t.isdigit() else t
    t_6 = t.zfill(6) if t.isdigit() else t
    t_10 = t.zfill(10) if t.isdigit() else t
    
    df_final = pd.DataFrame()
    origem = ""
    
    # ---- 1º PASSO: PROCV NA PLANILHA DE PEDIDOS (PC) ----
    if not df_pc.empty and "Nº Solicitação (SC)" in df_pc.columns:
        # Normaliza a coluna limpando resíduos de .0 e espaços antes da varredura
        col_sc_pc_limpa = df_pc["Nº Solicitação (SC)"].astype(str).str.split('.').str[0].str.lower().str.strip()
        
        # Executa o filtro contido tolerante
        res_pc = df_pc[(col_sc_pc_limpa == t) | (col_sc_pc_limpa == t_puro) | (col_sc_pc_limpa == t_6) | (col_sc_pc_limpa == t_10)]
        
        if not res_pc.empty:
            df_final = res_pc.copy()
            origem = "Planilha de Pedidos (PC) - Registro Localizado"

    # ---- 2º PASSO: FALLBACK PARA A PLANILHA DE SOLICITAÇÕES (SC) ----
    if df_final.empty and not df_sc.empty:
        # Identifica dinamicamente se a coluna chama "Nº Solicitação (SC)" ou "SCM"
        col_busca_sc = "Nº Solicitação (SC)" if "Nº Solicitação (SC)" in df_sc.columns else (next((c for c in df_sc.columns if "SCM" in c.upper()), None))
        
        if col_busca_sc:
            col_sc_real_limpa = df_sc[col_busca_sc].astype(str).str.split('.').str[0].str.lower().str.strip()
            res_sc = df_sc[(col_sc_real_limpa == t) | (col_sc_real_limpa == t_puro) | (col_sc_real_limpa == t_6) | (col_sc_real_limpa == t_10)]
            
            if not res_sc.empty:
                df_final = res_sc.copy()
                origem = "Planilha de Solicitações (SC) - Registro Localizado"

    # ---- MONTAGEM DA LISTA TRATADA PARA EXIBIÇÃO ----
    if not df_final.empty:
        df_painel = pd.DataFrame(index=df_final.index)
        
        for col_config in DICIONARIO_COLUNAS_EXATAS:
            nome_original_planilha = col_config["planilha"]
            nome_exibicao_tela = col_config["tela"]
            tipo_campo = col_config["tipo"]
            
            col_real = nome_original_planilha
            if nome_original_planilha not in df_final.columns:
                if "SOLICITACAO" in nome_original_planilha.upper() or "SC" in nome_original_planilha.upper():
                    col_real = next((c for c in df_final.columns if "SCM" in c.upper() or "SC" in c.upper()), nome_original_planilha)

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
                if nome_exibicao_tela == "Nº Solicitação (SC)":
                    df_painel[nome_exibicao_tela] = ajustar_zeros_protheus(busca, 6) if busca.strip().isdigit() else busca.strip()
                elif tipo_campo in ["moeda", "numero"]:
                    df_painel[nome_exibicao_tela] = 0.0
                else:
                    df_painel[nome_exibicao_tela] = ""

        # REGRA ATIVADA: Se os dados vierem da aba de Solicitações (SC), o status assume obrigatoriamente "EM COTAÇÃO"
        if origem.startswith("Planilha de Solicitações") and "STATUS" in df_painel.columns:
            df_painel["STATUS"] = "EM COTAÇÃO"

        # ==========================================
        # REGRAS OPERACIONAIS INTER-COLUNAS
        # ==========================================
        
        # REGRA 1: Replicar Entrega para Previsão se Previsão estiver vazia
        if "Previsão de entrega" in df_painel.columns and "Entrega" in df_painel.columns:
            mascara_vazia = (df_painel["Previsão de entrega"] == "") | (df_painel["Previsão de entrega"].isna())
            df_painel.loc[mascara_vazia, "Previsão de entrega"] = df_painel.loc[mascara_vazia, "Entrega"]

        # REGRA 2: Forçar N/A em Pagamento baseado no critério excludente
        if "Pagamento" in df_painel.columns and "Condição Pagamento" in df_painel.columns:
            condicao_normalizada = df_painel["Condição Pagamento"].astype(str).str.upper().str.strip()
            mascara_na = (
                (~condicao_normalizada.str.contains("A VISTA", na=False)) & 
                (~condicao_normalizada.str.contains("ENT", na=False)) & 
                (~condicao_normalizada.str.contains("VENCIDO", na=False)) & 
                (~condicao_normalizada.str.contains("PAGO", na=False))
            )
            df_painel.loc[mascara_na, "Pagamento"] = "N/A"

        # ==========================================
        # FORMATAÇÃO COMPACTA UNIFICADA (DD/MM/AA)
        # ==========================================
        colunas_para_formatar = ["Envio", "Pagamento", "Previsão de entrega", "Entrega", "Data Emissão", "Data Liberação"]
        for col_data in colunas_para_formatar:
            if col_data in df_painel.columns:
                df_painel[col_data] = df_painel[col_data].apply(formatar_para_dd_mm_aa)

        df_painel = df_painel.dropna(how='all')

        st.markdown(f'<div class="status-box">🟢 {origem}</div>', unsafe_allow_html=True)
        st.write("")
        
        # Preparação do arquivo final para extração local
        out = BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: 
            df_painel.to_excel(wr, index=False)
        
        st.download_button(
            label="📥 DESCARREGAR RELATÓRIO",
            data=out.getvalue(),
            file_name="Portal_Compras_Parente.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # ==========================================
        # 7. CONFIGURAÇÃO VISUAL DE ALINHAMENTO E MOEDA
        # ==========================================
        configuracao_colunas_tela = {}
        
        for col_config in DICIONARIO_COLUNAS_EXATAS:
            nome_tela = col_config["tela"]
            tipo_campo = col_config["tipo"]
            
            if tipo_campo == "moeda":
                configuracao_colunas_tela[nome_tela] = st.column_config.NumberColumn(
                    nome_tela,
                    format="R$ %.2f",
                    alignment="right"
                )
            elif tipo_campo == "numero":
                configuracao_colunas_tela[nome_tela] = st.column_config.NumberColumn(
                    nome_tela,
                    alignment="right"
                )
            else:
                if nome_tela in ["Fornecedor", "Descrição"]:
                    configuracao_colunas_tela[nome_tela] = st.column_config.TextColumn(
                        nome_tela,
                        alignment="left"
                    )
                else:
                    configuracao_colunas_tela[nome_tela] = st.column_config.TextColumn(
                        nome_tela,
                        alignment="right"
                    )
        
        # Renderização final na tela
        st.dataframe(
            df_painel, 
            use_container_width=True, 
            hide_index=True,
            column_config=configuracao_colunas_tela
        )
    else:
        st.warning(f"⚠️ Nenhuma informação localizada para a SC: '{busca}' nas planilhas do sistema.")
else:
    st.info("💡 Digite o número da SC para iniciar. O motor buscará o histórico completo em Pedidos (PC) antes de recorrer às Solicitações (SC).")

st.markdown("<p style='text-align:center; color:#478c3b; font-weight:bold; margin-top:30px;'>Parente Andrade | Setor de Suprimentos</p>", unsafe_allow_html=True)
