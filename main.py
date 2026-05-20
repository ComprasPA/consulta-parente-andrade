import streamlit as st
import pandas as pd
import base64
import re
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

# 3. CSS MODERNIZADO (Visual Clean, Cores Harmonizadas e Efeitos Suaves)
st.markdown(f"""
    <style>
    /* Ocultar elementos padrão do Streamlit */
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    
    /* Fondo geral suave para descanso visual */
    .stApp {{ background-color: #f8fafc; }}
    
    /* Topo moderno sem bordas grossas */
    .header-modern {{
        background: #ffffff;
        padding: 24px 32px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-top: 5px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03);
    }}
    .portal-title {{ 
        color: #1e293b !important; 
        font-size: 30px !important; 
        font-weight: 700 !important; 
        margin: 0 !important;
        letter-spacing: -0.5px;
    }}
    .portal-subtitle {{
        color: #64748b;
        font-size: 14px;
        margin: 4px 0 0 0 !important;
    }}
    
    /* Customização fina para campos de input e botões */
    div[data-testid="stVerticalBlock"] > div:has(input) {{
        background-color: #ffffff; 
        padding: 2px 6px !important; 
        border-radius: 8px; 
        border: 1px solid #e2e8f0 !important;
        box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.02);
        transition: border-color 0.2s;
    }}
    div[data-testid="stVerticalBlock"] > div:has(input):focus-within {{
        border-color: #478c3b !important;
    }}
    
    /* Estilização padrão para mensagens de status internas */
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
    }}
    
    /* Ajustes na visualização das tabelas para acompanhar o design */
    div[data-testid="stDataFrame"] {{
        background: #ffffff;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }}
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO REESTRUTURADO (Layout Limpo e Alinhado)
st.markdown('<div class="header-modern">', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns([1.1, 4.6, 1.4, 2.3])
with c1:
    if base64_logo: 
        st.markdown(f'<img src="data:image/png;base64,{base64_logo}" style="width:130px; margin-top:2px;">', unsafe_allow_html=True)
with c2:
    st.markdown('<p class="portal-title">Portal Gestão de Compras</p>', unsafe_allow_html=True)
    st.markdown('<p class="portal-subtitle">Parente Andrade | Diretoria de Suprimentos e Logística</p>', unsafe_allow_html=True)
with c3:
    # Botão com visual em linha, focado no topo
    if st.button("🔄 Sincronizar Base", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
with c4:
    busca = st.text_input("", placeholder="🔍 Localizar SC ou Pedido...", label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)


# ==========================================
# 5. ESTRUTURA DE COLUNAS MANTIDA CONGELADA
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
# 6. MOTOR DE BUSCA MANTER LÓGICA CONGELADA
# ==========================================
if busca:
    termo_busca = busca.strip()
    termo_numerico = re.sub(r'[^0-9]', '', termo_busca)
    valor_numerico_inteiro = int(termo_numerico) if termo_numerico else 0
    
    if termo_numerico:
        padrao_regex = f"^{int(termo_numerico)}(\\.0)?$"
    else:
        padrao_regex = re.escape(termo_busca)
        
    df_final = pd.DataFrame()
    
    if not df_pc.empty:
        if valor_numerico_inteiro >= 170000:
            col_busca_pc = next((c for c in df_pc.columns if "PEDID" in c.upper() or "PC" in c.upper()), None)
        else:
            col_busca_pc = next((c for c in df_pc.columns if "SOLICITACAO" in c.upper() or "SC" in c.upper()), None)
            
        if not col_busca_pc:
            col_busca_pc = next((c for c in df_pc.columns if "SOLICITACAO" in c.upper() or "SC" in c.upper()), df_pc.columns[0])

        res_pc = df_pc[df_pc[col_busca_pc].astype(str).str.strip().str.contains(padrao_regex, flags=re.IGNORECASE, regex=True, na=False)]
        if not res_pc.empty:
            df_final = res_pc.copy()

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
                if nome_exibicao_tela == "Nº Solicitação (SC)" and valor_numerico_inteiro < 170000:
                    df_painel[nome_exibicao_tela] = ajustar_zeros_protheus(busca, 6) if busca.strip().isdigit() else busca.strip()
                elif nome_exibicao_tela == "Nº Pedido (PC)" and valor_numerico_inteiro >= 170000:
                    df_painel[nome_exibicao_tela] = ajustar_zeros_protheus(busca, 6) if busca.strip().isdigit() else busca.strip()
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

        colunas_para_formatar = ["Envio", "Pagamento", "Previsão de entrega", "Entrega", "Data Emissão", "Data Liberação"]
        for col_data in colunas_para_formatar:
            if col_data in df_painel.columns:
                df_painel[col_data] = df_painel[col_data].apply(formatar_para_dd_mm_aa)

        df_painel = df_painel.dropna(how='all')

        # Caixa de status modernizada visualmente por CSS
        st.markdown('<div class="status-card">🔍 Registro Localizado na Base de Pedidos Firme</div>', unsafe_allow_html=True)
        
        # Botão de download posicionado com espaçamento limpo antes da tabela
        c_down, _ = st.columns([2.5, 7.5])
        with c_down:
            out = BytesIO()
            with pd.ExcelWriter(out, engine='xlsxwriter') as wr: 
                df_painel.to_excel(wr, index=False)
            st.download_button(
                label="📥 Extrair Relatório Operacional",
                data=out.getvalue(),
                file_name="Portal_Compras_Parente.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        st.write("")

        # ---- 7. CONFIGURAÇÃO VISUAL DE ALINHAMENTO E MOEDA ----
        configuracao_colunas_tela = {}
        for col_config in DICIONARIO_COLUNAS_EXATAS:
            nome_tela = col_config["tela"]
            tipo_campo = col_config["tipo"]
            
            if tipo_campo == "moeda":
                configuracao_colunas_tela[nome_tela] = st.column_config.NumberColumn(nome_tela, format="R$ %.2f", alignment="right")
            elif tipo_campo == "numero":
                configuracao_colunas_tela[nome_tela] = st.column_config.NumberColumn(nome_tela, alignment="right")
            else:
                if nome_tela in ["Fornecedor", "Descrição"]:
                    configuracao_colunas_tela[nome_tela] = st.column_config.TextColumn(nome_tela, alignment="left")
                else:
                    configuracao_colunas_tela[nome_tela] = st.column_config.TextColumn(nome_tela, alignment="right")
        
        # Plotagem final estável
        st.dataframe(df_painel, use_container_width=True, hide_index=True, column_config=configuracao_colunas_tela)
    else:
        # Mensagens condicionais nativas integradas à nova identidade visual
        if valor_numerico_inteiro >= 170000:
            st.error("⚠️ Seu pedido de compras não foi localizado, entre em contato com o comprador.")
        else:
            st.warning("⏳ Sua Solicitação ainda está em cotação. Logo estaremos finalizando o pedido de compras!")
else:
    # Boas-vindas operacional limpa
    st.info("💡 Insira o número da SC ou do Pedido de Compras no campo superior direito para rastrear o status.")

# Rodapé institucional moderno
st.markdown("<div style='text-align:center; margin-top:40px; border-top:1px solid #e2e8f0; padding-top:20px;'><p style='color:#64748b; font-size:13px; font-weight:600;'>Parente Andrade | Coordenação de Suprimentos</p></div>", unsafe_allow_html=True)
