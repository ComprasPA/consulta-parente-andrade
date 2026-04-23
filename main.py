import streamlit as st
import pandas as pd
import base64
from io import BytesIO

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Suprimentos | Parente Andrade",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. FUNÇÃO PARA CONVERTER IMAGEM LOCAL PARA BASE64 (PARA O CSS)
@st.cache_data(ttl=600) # Faz cache da logo codificada para economizar processamento
def get_base64_logo(image_path="logo"):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return None

base64_logo = get_base64_logo()

# 3. CSS PARA MARCA D'ÁGUA E CORES DA IDENTIDADE PA
st.markdown("""
    <style>
    /* Esconder menus padrão */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}

    /* Fundo da Página (Cinza Suave) */
    .stApp {
        background-color: #f0f2f6;
    }

    /* CONTAINER PRINCIPAL: ADICIONANDO MARCA D'ÁGUA */
    .stApp > div > div > div > div > section > div {
        background-image: url("data:image/png;base64,""" + str(base64_logo) + """");
        background-size: 350px; /* Tamanho da logo no fundo */
        background-position: center 250px; /* Alinhamento central e vertical */
        background-repeat: no-repeat;
        background-attachment: fixed; /* A marca d'água não rola com o scroll */
        opacity: 0.06; /* BAIXA OPACIDADE PARA NÃO ATRALHAR A LEITURA */
        z-index: -1; /* Garante que fique atrás de todos os elementos */
    }

    /* Container Principal */
    .block-container { 
        padding-top: 1.5rem !important; 
        background-color: transparent !important; /* Deve ser transparente para mostrar o fundo */
    }

    /* Estilo da Barra de Busca com borda Verde PA */
    div[data-testid="stVerticalBlock"] > div:has(input) {
        background-color: #ffffff;
        padding: 8px 15px !important;
        border-radius: 12px;
        border: 2px solid #478c3b;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }

    /* Customização do Botão de Download (Amarelo PA) */
    .stDownloadButton button {
        background-color: #f2a933 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        width: 100%;
    }
    .stDownloadButton button:hover {
        background-color: #d6952d !important;
        color: white !important;
    }

    /* Tabela de Dados com bordas arredondadas */
    .stDataFrame {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }

    /* Mensagens de Alerta (Verde PA) */
    div.stAlert > div {
        background-color: #478c3b !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        border: none !important;
    }
    
    /* Texto do rodapé */
    .footer-text {
        text-align: center;
        color: #478c3b;
        font-size: 13px;
        margin-top: 50px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. CABEÇALHO LADO A LADO
col_logo, col_busca = st.columns([1, 4])

with col_logo:
    try:
        # Mantendo a logo principal visível no topo
        st.image("logo", width=160)
    except:
        st.markdown("<h2 style='color:#478c3b; margin:0;'>PARENTE ANDRADE</h2>", unsafe_allow_html=True)

with col_busca:
    busca = st.text_input(
        "", 
        placeholder="🔍 O que você deseja consultar hoje? (SC, Produto, Fornecedor...)",
        label_visibility="collapsed"
    )

# Divisor Amarelo Vivo
st.markdown("<div style='height: 5px; background-color: #f2a933; margin-bottom: 25px; border-radius: 5px;'></div>", unsafe_allow_html=True)

# 5. CARREGAMENTO E TRATAMENTO DE DADOS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/1Qgv6YSQ8XGx1RagMfYcTOOT_a_TQ2RoVGNIk7fY4kf0/edit?usp=sharing"

def preparar_url_google(url):
    return url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data(ttl=300)
def carregar_dados():
    try:
        url_csv = preparar_url_google(URL_PLANILHA)
        df_raw = pd.read_csv(url_csv, dtype=str)
        df_raw = df_raw.fillna('')

        # Padronização de datas (DD/MM/AA)
        colunas_data = ["DT Envio", "DT Pgo (AVISTA)", "DT Prev de Entrega", "DT entrega ", "Data Emissao", "Dt Liberacao"]
        for col in colunas_data:
            if col in df_raw.columns:
                temp_date = pd.to_datetime(df_raw[col], errors='coerce')
                df_raw[col] = temp_date.dt.strftime('%d/%m/%y').fillna(df_raw[col])
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

# 6. EXIBIÇÃO E FILTROS
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
                st.success(f"📦 Encontramos {len(resultado)} registro(s) para sua busca.")
            
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
            st.warning(f"🔎 Nenhum resultado encontrado para: '{busca}'")
    else:
        st.info("💡 Digite o termo de busca acima para visualizar os dados atualizados.")
else:
    st.error("❌ Erro técnico ao carregar a base de dados.")

# 7. RODAPÉ COM CORES DA MARCA
st.markdown(f"<p class='footer-text'>PARENTE ANDRADE LTDA<br><span style='color: #f2a933;'>Setor de Suprimentos - Gestão Eficiente</span></p>", unsafe_allow_html=True)
