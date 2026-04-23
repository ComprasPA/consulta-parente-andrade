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

# 2. CSS PARA LAYOUT DE PRODUÇÃO E ESTILO PA
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    .block-container { padding-top: 1rem !important; }

    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 5px 15px !important;
        border-radius: 10px;
        border: 2px solid #478c3b;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    div.stAlert > div {
        background-color: #d4edda !important;
        color: #155724 !important;
        font-weight: bold;
        border: 1px solid #c3e6cb !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. CABEÇALHO LADO A LADO
col_logo, col_busca = st.columns([1, 4])

with col_logo:
    try:
        st.image("logo", width=140)
    except:
        st.subheader("PARENTE ANDRADE")

with col_busca:
    busca = st.text_input(
        "", 
        placeholder="🔍 Pesquisar por SC, Produto, Fornecedor ou Centro de Custo...",
        label_visibility="collapsed"
    )

st.markdown("<div style='height: 3px; background-color: #f2a933; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 4. CARREGAMENTO E TRATAMENTO DE DADOS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        df_raw = pd.read_csv(url_csv, dtype=str)
        df_raw = df_raw.fillna('')

        # --- PADRONIZAÇÃO DE DATAS (CORREÇÃO DE MÊS/DIA/ANO PARA DIA/MÊS/ANO) ---
        colunas_data = ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]
        
        for col in colunas_data:
            if col in df_raw.columns:
                # Primeiro, converte assumindo que o dado original pode estar no formato Mês/Dia/Ano (Americano)
                # O dayfirst=False e o errors='coerce' ajudam a tratar strings estranhas
                temp_date = pd.to_datetime(df_raw[col], errors='coerce')
                
                # Formata para o padrão brasileiro solicitado: DD/MM/AA
                # O .dt.strftime('%d/%m/%y') gera exatamente "14/04/26"
                df_raw[col] = temp_date.dt.strftime('%d/%m/%y').fillna(df_raw[col])
                
                # Limpa resíduos de conversão falha
                df_raw[col] = df_raw[col].replace(['NaT', 'nan'], '')

        if 'Produto' in df_raw.columns:
            df_raw['Produto'] = df_raw['Produto'].apply(
                lambda x: str(x).strip().zfill(10) if (x != '' and str(x).lower() != 'nan') else ''
            )
        
        return df_raw
    except Exception as e:
        st.error(f"⚠️ Erro ao acessar a base: {e}")
        return None

df = carregar_dados()

# 5. EXIBIÇÃO E FILTROS
if df is not None:
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
            c_msg, c_down = st.columns([3, 1])
            with c_msg:
                st.success(f"✅ Encontrado(s) {len(resultado)} registro(s)")
            
            with c_down:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    resultado.to_excel(writer, index=False, sheet_name='Consulta_PA')
                
                st.download_button(
                    label="📥 Exportar Excel",
                    data=output.getvalue(),
                    file_name="Consulta_Parente_Andrade.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            st.dataframe(resultado, use_container_width=True, hide_index=True)
        else:
            st.warning(f"🔎 Nenhum resultado para: '{busca}'")
    else:
        st.info("👋 Digite o termo de busca no topo para visualizar os dados.")
else:
    st.error("❌ Não foi possível carregar as informações.")

st.markdown("<p style='text-align: center; color: #999; font-size: 12px; margin-top: 50px;'>PARENTE ANDRADE LTDA<br>Setor de Suprimentos - Gestão de Pedidos</p>", unsafe_allow_html=True)
