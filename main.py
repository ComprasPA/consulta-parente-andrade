import streamlit as st
import pandas as pd
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. CSS PARA LAYOUT SUPERIOR E ESTILO
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Busca */
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 5px 15px !important;
        border-radius: 10px;
        border: 1px solid #478c3b;
    }

    /* Alertas */
    div.stAlert > div {
        background-color: #d4edda !important;
        color: #155724 !important;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CABEÇALHO LADO A LADO
col_logo, col_busca = st.columns([1, 4])

with col_logo:
    try:
        st.image("logo", width=150)
    except:
        st.subheader("PARENTE ANDRADE")

with col_busca:
    busca = st.text_input(
        "", 
        placeholder="🔍 Pesquisar por SC, Produto, Fornecedor ou CC...",
        label_visibility="collapsed"
    )

st.markdown("<div style='height: 3px; background-color: #f2a933; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 4. CARREGAMENTO E LIMPEZA
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        df_raw = pd.read_csv(url_csv, dtype=str)
        df_raw = df_raw.fillna('')
        
        if 'Produto' in df_raw.columns:
            df_raw['Produto'] = df_raw['Produto'].apply(
                lambda x: str(x).strip().zfill(10) if x != '' else x
            )
        return df_raw
    except:
        return None

df = carregar_dados()

if df is not None:
    # Definindo a configuração da tabela conforme solicitado
    colunas_visiveis = [
        "STATUS", "DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", 
        "DT entrega ", "CONDIÇÃO PGO", "N° da SC", "N° PC", "Fornecedor", 
        "Nome Fornecedor", "CC", "Produto", "Descricao", "UM", "QNT", 
        " Prc Unitario", " Vlr.Total", "Data Emissao", "Dt Liberacao"
    ]
    colunas_existentes = [col for col in colunas_visiveis if col in df.columns]

    if busca:
        mask = df.apply(lambda row: row.astype(str).str.contains(busca, case=False).any(), axis=1)
        resultado = df[mask][colunas_existentes]
        
        if not resultado.empty:
            # Layout para Mensagem e Botão de Download
            c_msg, c_down = st.columns([3, 1])
            with c_msg:
                st.success(f"✅ {len(resultado)} item(s) encontrado(s)")
            
            with c_down:
                # FUNÇÃO PARA GERAR EXCEL REAL (XLSX) - Resolve o erro de uma única célula
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    resultado.to_excel(writer, index=False, sheet_name='Consulta')
                
                st.download_button(
                    label="📥 Baixar em Excel",
                    data=output.getvalue(),
                    file_name="Consulta_Suprimentos_PA.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            st.dataframe(resultado, use_container_width=True, hide_index=True)
        else:
            st.warning(f"⚠️ Nenhum registro encontrado para '{busca}'.")
    else:
        st.info("💡 Digite acima para iniciar a consulta.")
else:
    st.error("Erro na base de dados.")

st.markdown("<p style='text-align: center; color: #666; font-size: 12px; margin-top: 30px;'>PARENTE ANDRADE LTDA</p>", unsafe_allow_html=True)
