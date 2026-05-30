import streamlit as st
import pandas as pd
import base64
import json
# Bibliotecas necessárias para escrever no Google Sheets
# Instale no terminal: pip install gspread oauth2client
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    HAS_GSPREAD = True
except ImportError:
    HAS_GSPREAD = False

# 1. CONFIGURAÇÃO DA PÁGINA (Interface do Operador)
st.set_page_config(
    page_title="Painel do Operador | Parente Andrade",
    page_icon="⚙️",
    layout="centered" # Layout centralizado para focar no upload
)

# 2. CSS MODERNIZADO E ISOLADO (Com tema mais escuro para diferenciar do painel de compras)
st.markdown(f"""
    <style>
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    .stApp {{ background-color: #f1f5f9; font-family: 'Inter', sans-serif; }}
    
    .header-operator {{
        background: #0f172a; /* Cor escura para diferenciar o ambiente */
        padding: 24px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }}
    .operator-title {{ font-size: 32px; font-weight: 800; margin: 0; letter-spacing: -1px; }}
    .operator-subtitle {{ font-size: 16px; color: #94a3b8; margin-top: 4px; }}
    
    .upload-card {{
        background: #ffffff;
        padding: 32px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }}
    </style>
    """, unsafe_allow_html=True)

# 3. CABEÇALHO DO OPERADOR
st.markdown("""
    <div class="header-operator">
        <p class="operator-title">⚙️ Portal do Operador</p>
        <p class="operator-subtitle">Atualização Direta da Base de Dados (Google Sheets)</p>
    </div>
""", unsafe_allow_html=True)

# 4. PAINEL DE UPLOAD
st.markdown('<div class="upload-card">', unsafe_allow_html=True)
st.markdown("### 📥 Importar Nova Base de Dados")
st.markdown("Faça o upload do ficheiro Excel (.xlsx) atualizado do seu computador. O sistema irá sobrepor a base do Google Sheets automaticamente.")

# Componente de Upload do Streamlit
arquivo_upload = st.file_uploader("Selecione o ficheiro Excel", type=["xlsx"])

if arquivo_upload is not None:
    # Mostra um preview do que está a ser carregado
    try:
        df_novo = pd.read_excel(arquivo_upload, dtype=str).fillna('')
        st.success(f"Ficheiro carregado com sucesso! Encontradas {len(df_novo)} linhas.")
        
        with st.expander("Pré-visualizar Dados a Inserir ▼"):
            st.dataframe(df_novo.head(5)) # Mostra apenas as primeiras 5 linhas

        # Botão de Ação Crítica
        if st.button("🚀 Confirmar e Atualizar Base no Google Sheets", use_container_width=True, type="primary"):
            
            if not HAS_GSPREAD:
                st.error("⚠️ As bibliotecas 'gspread' e 'oauth2client' não estão instaladas. Execute: pip install gspread oauth2client")
            else:
                with st.spinner('A conectar com os servidores da Google e a atualizar a base de dados...'):
                    try:
                        # -------------------------------------------------------------
                        # MOTOR DE ATUALIZAÇÃO GOOGLE SHEETS (Requer credenciais.json)
                        # -------------------------------------------------------------
                        # Define as permissões (Escopos)
                        escopos = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
                        
                        # Carrega o ficheiro de chaves (O SÍLVIO PRECISA DE GERAR ESTE FICHEIRO NA GOOGLE CLOUD)
                        credenciais = ServiceAccountCredentials.from_json_keyfile_name('credenciais.json', escopos)
                        cliente = gspread.authorize(credenciais)
                        
                        # ID da sua planilha destino (A que configurámos no main.py)
                        id_planilha = "1e7pQ512ge5XMnXxsRODEO7V48KgWo6FpKeITFqBSg1o"
                        planilha = cliente.open_by_key(id_planilha)
                        
                        # Aceder à aba "Pedidos"
                        aba_destino = planilha.worksheet("Pedidos")
                        
                        # 1. Limpa a aba atual no Google Sheets
                        aba_destino.clear()
                        
                        # 2. Converte o DataFrame do Pandas numa lista para o Google Sheets
                        # Adiciona o cabeçalho como a primeira linha
                        dados_para_enviar = [df_novo.columns.values.tolist()] + df_novo.values.tolist()
                        
                        # 3. Envia os novos dados
                        aba_destino.update(dados_para_enviar)
                        
                        st.success("✅ Atualização concluída com sucesso! O Painel de Compras já reflete os novos dados.")
                        
                    except FileNotFoundError:
                        st.error("⚠️ Ficheiro 'credenciais.json' não encontrado. É obrigatório criar uma Conta de Serviço na Google Cloud e colocar o ficheiro JSON na mesma pasta deste script.")
                    except Exception as e:
                        st.error(f"⚠️ Erro ao atualizar o Google Sheets: {e}")

    except Exception as e:
        st.error(f"Erro ao ler o ficheiro Excel: {e}")

st.markdown('</div>', unsafe_allow_html=True)
