import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração da página
st.set_page_config(page_title="VEDA.IA - Diagnóstico Estratégico", layout="wide", initial_sidebar_state="collapsed")

# --- Interface de Design Premium (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #1E293B !important; color: #F8FAFC !important; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    .stMarkdown, p, span, label, .stTextArea label { color: #F8FAFC !important; }
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 20px; border-radius: 12px; color: white !important; margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); border: 1px solid #334155;
    }
    .main-title { font-size: 32px; font-weight: 800; letter-spacing: -0.5px; margin: 0; color: #FFFFFF !important; }
    .subtitle { font-size: 15px; color: #93C5FD !important; margin-top: 5px; opacity: 0.9; }
    .section-box {
        background-color: #334155 !important; padding: 24px; border-radius: 10px;
        border-left: 6px solid #38BDF8; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .section-title { font-size: 18px; font-weight: 700; color: #38BDF8 !important; margin: 0; }
    .stTextArea textarea { background-color: #1E293B !important; color: #FFFFFF !important; border: 1px solid #475569 !important; border-radius: 6px !important; }
    .kpi-card { background: #334155 !important; padding: 20px; border-radius: 8px; border-top: 4px solid #475569; text-align: center; }
    .kpi-value { font-size: 24px; font-weight: 700; margin-top: 5px; }
    .stTabs [data-baseweb="tab"] { background-color: #334155 !important; color: #94A3B8 !important; border-radius: 4px 4px 0px 0px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #38BDF8 !important; color: #0F172A !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Topo Fixo
st.markdown("""
    <div class="main-header" style="margin-bottom: 0px;">
        <div class="main-title">📊 VEDA.IA</div>
        <div class="subtitle">Inteligência Estratégica em Compras • Auditoria de Processos & Strategic Sourcing</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Inicialização de Variáveis e Perfis de Acesso
if 'perfil' not in st.session_state: st.session_state.perfil = None
if 'passo' not in st.session_state: st.session_state.passo = 1
if 'respostas' not in st.session_state: st.session_state.respostas = {}

# --- TELA DE LOGIN / SELEÇÃO DE PERFIL ---
if st.session_state.perfil is None:
    st.markdown('<div class="section-box"><h3 style="color:#38BDF8; margin-top:0;">🔐 Controle de Acesso</h3><p>Selecione o seu perfil para entrar no sistema:</p></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("**👤 VISÃO DO CLIENTE**\nAcesso exclusivo para preencher o diagnóstico operacional.")
        if st.button("Entrar como Cliente", use_container_width=True):
            st.session_state.perfil = 'cliente'
            st.rerun()
            
    with col2:
        st.warning("**💼 VISÃO DO CONSULTOR**\nAcesso total ao Painel de Resultados e PDF (Área Restrita).")
        senha = st.text_input("Senha de Acesso", type="password", placeholder="Digite a senha...")
        if st.button("Entrar como Consultor", use_container_width=True):
            if senha == "vedaadmin": # Senha definida aqui
                st.session_state.perfil = 'consultor'
                st.rerun()
            elif senha != "":
                st.error("Senha incorreta. Tente novamente.")
    st.stop() # Pausa o aplicativo até que um perfil seja escolhido

# --- CABEÇALHO DO USUÁRIO LOGADO ---
col_head1, col_head2 = st.columns([8, 2])
with col_head1:
    passos_totais = 6
    st.progress(st.session_state.passo / passos_totais)
    st.markdown(f"<p style='color: #94A3B8; font-size: 12px;'>Etapa {st.session_state.passo} de {passos_totais}</p>", unsafe_allow_html=True)
with col_head2:
    st.markdown(f"<div style='text-align:right; color:#38BDF8; font-weight:bold;'>Perfil: {st.session_state.perfil.upper()}</div>", unsafe_allow_html=True)
    if st.button("Sair / Trocar Perfil", key="logout"):
        st.session_state.perfil = None
        st.session_state.passo = 1
        st.rerun()

# --- FUNÇÃO PARA GERAR GRÁFICO (Apenas Consultor usa) ---
def gerar_ishikawa_pdf():
    fig, ax = plt.subplots(figsize=(10, 3.5))
    fig.patch.set_facecolor('#FFFFFF'); ax.set_facecolor('#FFFFFF')
    ax.axhline(0, color='#1B365D', linewidth=4)
    ax.annotate('MÉTODO:\nFollow-up manual e reativo', xy=(2.5, 0), xytext=(1.0, 1.2), arrowprops=dict(arrowstyle="->", color='#4A777A', lw=2), fontsize=9, color='black')
    ax.annotate('SISTEMAS:\nRedigitação manual de PDF', xy=(6.5, 0), xytext=(5.0, 1.2), arrowprops=dict(arrowstyle="->", color='#4A777A', lw=2), fontsize=9, color='black')
    ax.annotate('DADOS:\nFalta de Spend Analysis', xy=(3.5, 0), xytext=(2.0, -1.4), arrowprops=dict(arrowstyle="->", color='#4A777A', lw=2), fontsize=9, color='black')
    ax.annotate('MANUTENÇÃO:\nCompras de MRO urgentes', xy=(7.5, 0), xytext=(5.5, -1.4), arrowprops=dict(arrowstyle="->", color='#4A777A', lw=2), fontsize=9, color='black')
    ax.text(10.2, 0, "PERDA DE\nSAVING", fontsize=10, fontweight='bold', color='white', bbox=dict(boxstyle="square,pad=0.5", fc="#A93226", ec="none"))
    ax.set_xlim(0, 12); ax.set_ylim(-2.2, 2.2); ax.axis('off')
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
    img_buffer.seek(0); plt.close(fig)
    return img_buffer

# --- FUNÇÃO PARA GERAR PDF (Apenas Consultor usa) ---
def gerar_pdf(respostas, dados_tabela, ishikawa_buffer):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, textColor=colors.HexColor('#1B365D'), spaceAfter=15)
    h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#4A777A'), spaceBefore=12, spaceAfter=6)
    text_style = ParagraphStyle('TextStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#333333'), spaceAfter=8)
    alert_style = ParagraphStyle('AlertStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#B7950B'), spaceAfter=8, fontName='Helvetica-Bold')
    table_text = ParagraphStyle('TableText', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#333333'))
    table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=10, leading=12, textColor=colors.whitesmoke, fontName='Helvetica-Bold')

    story.append(Paragraph("RELATÓRIO EXECUTIVO DE AUDITORIA - VEDA.IA", title_style))
    story.append(Paragraph("Maturidade Avaliada do Negócio: 5.2 / 10", h2_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("1. DIAGNÓSTICO DOS PILARES", h2_style))
    story.append(Paragraph("<b>Visão & Estratégia:</b> Existe desejo latente de crescimento e saving na diretoria, porém há uma falta crônica de visibilidade analítica estruturada de despesas (Spend Analysis).", text_style))
    story.append(Paragraph("<b>Direcionamento & Ação:</b> Ruído operacional grave detectado. A equipe gasta a maior parte do dia ativa em processos manuais de redigitação de propostas e rotinas reativas.", text_style))
    story.append(Paragraph("2. ENGENHARIA DA QUALIDADE (CAUSA E EFEITO)", h2_style))
    story.append(RLImage(ishikawa_buffer, width=460, height=160))
    story.append(Spacer(1, 15))
    story.append(Paragraph("3. MATRIZ DE DESALINHAMENTO CRÍTICO", h2_style))
    story.append(Paragraph("O desejo corporativo de obter Saving Estratégico (Visão) encontra-se bloqueado pelo sufocamento burocrático na operação (Ação).", alert_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("4. PLANO DE AÇÃO DETALHADO E CRONOGRAMA", h2_style))
    
    headers = [Paragraph("Gargalo (Causa Raiz)", table_header), Paragraph("Ação Corretiva (Descrição do Trabalho)", table_header), Paragraph("Prazo e Tempo Necessário", table_header), Paragraph("Status", table_header)]
    table_data = [headers]
    for i in range(len(dados_tabela["Gargalo (Causa Raiz)"])):
        table_data.append([ Paragraph(dados_tabela["Gargalo (Causa Raiz)"][i], table_text), Paragraph(dados_tabela["Ação Corretiva (Descrição do Trabalho)"][i], table_text), Paragraph(dados_tabela["Prazo e Tempo Necessário"][i], table_text), Paragraph(dados_tabela["Status / Reanálise"][i], table_text) ])
        
    t = Table(table_data, colWidths=[110, 200, 110, 90])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B365D')), ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8), ('TOPPADDING', (0,0), (-1,-1), 8), ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    story.append(t); doc.build(story); buffer.seek(0)
    return buffer

# --- MÓDULOS DE PERGUNTAS (1 A 5) ---
if st.session_state.passo == 1:
    st.markdown('<div class="section-box"><div class="section-title">MÓDULO A: VISÃO ESTRATÉGICA, ANÁLISE DE GASTOS (Spend Analysis) E STRATEGIC SOURCING</div></div>', unsafe_allow_html=True)
    st.session_state.respostas['q_vol_forn'] = st.text_area("1. Qual é o volume médio mensal de requisições de compras e quantos fornecedores ativos a empresa possui hoje?", value=st.session_state.respostas.get('q_vol_forn', ''), height=100)
    st.session_state.respostas['q_kpis'] = st.text_area("2. Quais são os principais KPIs cobrados do setor hoje (ex: Saving, lead time)?", value=st.session_state.respostas.get('q_kpis', ''), height=100)
    st.session_state.respostas['q_perda_tempo'] = st.text_area("3. Onde a gerência sente que perde mais tempo, controle ou dinheiro no processo atual?", value=st.session_state.respostas.get('q_perda_tempo', ''), height=100)
    st.session_state.respostas['q_kraljic'] = st.text_area("4. Como a gestão acompanha a Curva ABC de estoque e o quadrante estratégico dos itens na Matriz de Kraljic?", value=st.session_state.respostas.get('q_kraljic', ''), height=100)
    st.session_state.respostas['q_spend'] = st.text_area("5. Como é feita a visibilidade do Spend Analysis (Análise de Gastos) hoje?", value=st.session_state.respostas.get('q_spend', ''), height=100)
    st.session_state.respostas['q_tail'] = st.text_area("6. Existe controle consolidado de cauda de fornecedores (Tail Spend)?", value=st.session_state.respostas.get('q_tail', ''), height=100)
    st.session_state.respostas['q_tco'] = st.text_area("7. A empresa adota a cultura de avaliar o Custo Total de Propriedade (TCO)?", value=st.session_state.respostas.get('q_tco', ''), height=100)
    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("Avançar Módulo B ➔", use_container_width=True): st.session_state.passo = 2; st.rerun()

elif st.session_state.passo == 2:
    st.markdown('<div class="section-box"><div class="section-title">MÓDULO B: ROTINA DIÁRIA E RITMO DE TRABALHO</div></div>', unsafe_allow_html=True)
    st.session_state.respostas['q_primeira_hora'] = st.text_area("1. Como é a primeira hora do seu dia de trabalho?", value=st.session_state.respostas.get('q_primeira_hora', ''), height=100)
    st.session_state.respostas['q_planilhas_fora'] = st.text_area("2. Quais planilhas de Excel 'por fora' você usa na rotina?", value=st.session_state.respostas.get('q_planilhas_fora', ''), height=100)
    st.session_state.respostas['q_falha_erp'] = st.text_area("3. Por que o ERP atual não atende essa demanda?", value=st.session_state.respostas.get('q_falha_erp', ''), height=100)
    st.session_state.respostas['q_telas_abertas'] = st.text_area("4. Quantas telas ou sistemas diferentes você precisa manter abertos?", value=st.session_state.respostas.get('q_telas_abertas', ''), height=100)
    st.session_state.respostas['q_interrupcoes'] = st.text_area("5. Quantas vezes por dia você precisa interromper suas tarefas?", value=st.session_state.respostas.get('q_interrupcoes', ''), height=100)
    st.session_state.respostas['q_canal_cobranca'] = st.text_area("6. Como eles cobram (WhatsApp, e-mail, presencial)?", value=st.session_state.respostas.get('q_canal_cobranca', ''), height=100)
    st.session_state.respostas['q_tempo_burocracia'] = st.text_area("7. Qual a porcentagem do seu dia gasta em tarefas burocráticas vs. estratégicas?", value=st.session_state.respostas.get('q_tempo_burocracia', ''), height=100)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Voltar", use_container_width=True): st.session_state.passo = 1; st.rerun()
    with col2:
        if st.button("Avançar Módulo C ➔", use_container_width=True): st.session_state.passo = 3; st.rerun()

elif st.session_state.passo == 3:
    st.markdown('<div class="section-box"><div class="section-title">MÓDULO C: CADASTROS, OEM E ACURACIDADE</div></div>', unsafe_allow_html=True)
    st.session_state.respostas['q_resp_tecnico'] = st.text_area("1. Quem é o responsável técnico por fornecer as especificações exatas (OEM)?", value=st.session_state.respostas.get('q_resp_tecnico', ''), height=100)
    st.session_state.respostas['q_erro_req'] = st.text_area("2. O que acontece quando uma informação vem errada na requisição?", value=st.session_state.respostas.get('q_erro_req', ''), height=100)
    st.session_state.respostas['q_fluxo_correcao'] = st.text_area("3. Como é o fluxo de correção e quanto tempo trava?", value=st.session_state.respostas.get('q_fluxo_correcao', ''), height=100)
    st.session_state.respostas['q_acuracidade_fisica'] = st.text_area("4. Como é garantida a acuracidade de estoque no recebimento?", value=st.session_state.respostas.get('q_acuracidade_fisica', ''), height=100)
    st.session_state.respostas['q_leitura_xml'] = st.text_area("5. Existe cruzamento automatizado do pedido com a NF-e via XML?", value=st.session_state.respostas.get('q_leitura_xml', ''), height=100)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Voltar", use_container_width=True): st.session_state.passo = 2; st.rerun()
    with col2:
        if st.button("Avançar Módulo D ➔", use_container_width=True): st.session_state.passo = 4; st.rerun()

elif st.session_state.passo == 4:
    st.markdown('<div class="section-box"><div class="section-title">MÓDULO D: FLUXO DE MANUTENÇÃO (MRO) E CONTRATAÇÃO DE SERVIÇOS</div></div>', unsafe_allow_html=True)
    st.session_state.respostas['q_diff_serv_mat'] = st.text_area("1. Como é diferenciado o fluxo de 'Serviços' vs 'Materiais'?", value=st.session_state.respostas.get('q_diff_serv_mat', ''), height=100)
    st.session_state.respostas['q_regras_validacao'] = st.text_area("2. Os sistemas e contratos possuem regras de validação distintas?", value=st.session_state.respostas.get('q_regras_validacao', ''), height=100)
    st.session_state.respostas['q_validacao_escopo'] = st.text_area("3. Como o time de compras valida o escopo técnico enviado pela Engenharia?", value=st.session_state.respostas.get('q_validacao_escopo', ''), height=100)
    st.session_state.respostas['q_corretiva_urgente'] = st.text_area("4. Em manutenção corretiva urgente, qual é o fluxo rápido adotado?", value=st.session_state.respostas.get('q_corretiva_urgente', ''), height=100)
    st.session_state.respostas['q_impacto_alcadas'] = st.text_area("5. Como isso impacta a governança de alçadas?", value=st.session_state.respostas.get('q_impacto_alcadas', ''), height=100)
    st.session_state.respostas['q_integracao_ppcm'] = st.text_area("6. Existe integração nativa entre as Ordens de Serviço do PPCM e suprimentos?", value=st.session_state.respostas.get('q_integracao_ppcm', ''), height=100)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Voltar", use_container_width=True): st.session_state.passo = 3; st.rerun()
    with col2:
        if st.button("Avançar Módulo E ➔", use_container_width=True): st.session_state.passo = 5; st.rerun()

elif st.session_state.passo == 5:
    st.markdown('<div class="section-box"><div class="section-title">MÓDULO E: FOLLOW-UP E RELACIONAMENTO COM FORNECEDORES</div></div>', unsafe_allow_html=True)
    st.session_state.respostas['q_cobranca_prazos'] = st.text_area("1. Como é feita a cobrança de prazos junto aos fornecedores?", value=st.session_state.respostas.get('q_cobranca_prazos', ''), height=100)
    st.session_state.respostas['q_processo_manual'] = st.text_area("2. É um processo manual ou possui algum tipo de automação?", value=st.session_state.respostas.get('q_processo_manual', ''), height=100)
    st.session_state.respostas['q_atraso_forn'] = st.text_area("3. Se um fornecedor atrasar, como compras descobre? É preventivo ou reativo?", value=st.session_state.respostas.get('q_atraso_forn', ''), height=100)
    st.session_state.respostas['q_cotacao_pdf'] = st.text_area("4. Como as cotações em PDF entram no sistema? Há digitação manual?", value=st.session_state.respostas.get('q_cotacao_pdf', ''), height=100)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Voltar", use_container_width=True): st.session_state.passo = 4; st.rerun()
    with col2:
        # Texto do botão muda dependendo de quem está preenchendo
        btn_label = "Enviar Diagnóstico 🚀" if st.session_state.perfil == 'cliente' else "Gerar Relatório VEDA.IA 🚀"
        if st.button(btn_label, use_container_width=True): st.session_state.passo = 6; st.rerun()

# --- FASE 6: FINALIZAÇÃO (DIVIDIDA POR PERFIL) ---
elif st.session_state.passo == 6:
    
    # ---------------- VISÃO DO CLIENTE ----------------
    if st.session_state.perfil == 'cliente':
        st.markdown('<div class="section-box" style="text-align:center; padding: 50px;">'
                    '<h1 style="color:#10B981; font-size:60px; margin:0;">✅</h1>'
                    '<h2 style="color:#38BDF8;">Auditoria Concluída com Sucesso!</h2>'
                    '<p style="font-size:16px; color:#94A3B8;">Suas respostas foram registradas e enviadas de forma segura para o nosso sistema.</p>'
                    '<p style="font-size:16px; color:#94A3B8;">O seu Consultor Estratégico fará a análise profunda dos dados através da metodologia VEDA.IA e agendará a apresentação do Plano de Ação em breve.</p>'
                    '</div>', unsafe_allow_html=True)
        
    # ---------------- VISÃO DO CONSULTOR ----------------
    elif st.session_state.perfil == 'consultor':
        st.markdown('<h3 style="color:#38BDF8; font-weight:700; margin-top:10px;">📝 Relatório Analítico Consolidado (Visão Restrita)</h3>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.markdown('<div class="kpi-card" style="border-top-color:#E11D48;"><span style="color:#94A3B8; font-size:13px; font-weight:600;">SCORE VEDA</span><div class="kpi-value" style="color:#E11D48;">5.2 / 10</div></div>', unsafe_allow_html=True)
        with col2: st.markdown('<div class="kpi-card" style="border-top-color:#F59E0B;"><span style="color:#94A3B8; font-size:13px; font-weight:600;">SPEND ANALYSIS</span><div class="kpi-value" style="color:#F59E0B;">Incipiente</div></div>', unsafe_allow_html=True)
        with col3: st.markdown('<div class="kpi-card" style="border-top-color:#10B981;"><span style="color:#94A3B8; font-size:13px; font-weight:600;">CADASTRO OEM</span><div class="kpi-value" style="color:#10B981;">Acuracidade Regular</div></div>', unsafe_allow_html=True)
        with col4: st.markdown('<div class="kpi-card" style="border-top-color:#3B82F6;"><span style="color:#94A3B8; font-size:13px; font-weight:600;">FOLLOW-UP</span><div class="kpi-value" style="color:#3B82F6;">100% Manual</div></div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["🔍 Diagnóstico por Pilar", "📊 Engenharia da Qualidade", "📅 Cronograma e Ação (5W2H)"])
        
        with tab1:
            st.markdown("#### Análise Estratégica Baseada em Suprimentos")
            st.write("**Visão & Estratégia:** Existe desejo latente de crescimento e saving na diretoria, porém há uma falta crônica de visibilidade analítica estruturada de despesas (*Spend Analysis*).")
            st.write("**Direcionamento & Ação:** Ruído operacional grave detectado. A equipe gasta a maior parte do dia ativa em processos manuais de redigitação de propostas comerciais recebidas em PDF e rotinas puramente reativas.")
            st.markdown('<div style="background-color:#1E293B; padding:15px; border-radius:6px; border:1px solid #F59E0B; font-size:14px; color:#F59E0B;"><strong>Matriz de Desalinhamento Crítico:</strong> O desejo corporativo de obter Saving Estratégico (Visão) encontra-se totalmente bloqueado pelo sufocamento burocrático na operação (Ação).</div>', unsafe_allow_html=True)
            
        with tab2:
            st.write("#### Diagrama de Causa e Efeito (Ishikawa)")
            fig, ax = plt.subplots(figsize=(11, 3.5))
            fig.patch.set_facecolor('#1E293B'); ax.set_facecolor('#1E293B')
            ax.axhline(0, color='#38BDF8', linewidth=4)
            ax.annotate('MÉTODO:\nFollow-up manual e reativo', xy=(2.5, 0), xytext=(1.0, 1.2), arrowprops=dict(arrowstyle="->", color='#94A3B8', lw=2), fontsize=9, color='#F8FAFC')
            ax.annotate('SISTEMAS:\nRedigitação manual de PDF', xy=(6.5, 0), xytext=(5.0, 1.2), arrowprops=dict(arrowstyle="->", color='#94A3B8', lw=2), fontsize=9, color='#F8FAFC')
            ax.annotate('DADOS:\nFalta de Spend Analysis', xy=(3.5, 0), xytext=(2.0, -1.4), arrowprops=dict(arrowstyle="->", color='#94A3B8', lw=2), fontsize=9, color='#F8FAFC')
            ax.annotate('MANUTENÇÃO:\nCompras de MRO urgentes', xy=(7.5, 0), xytext=(5.5, -1.4), arrowprops=dict(arrowstyle="->", color='#94A3B8', lw=2), fontsize=9, color='#F8FAFC')
            ax.text(10.2, 0, "PERDA DE\nSAVING", fontsize=10, fontweight='bold', color='white', bbox=dict(boxstyle="square,pad=0.5", fc="#E11D48", ec="none"))
            ax.set_xlim(0, 12); ax.set_ylim(-2.2, 2.2); ax.axis('off')
            st.pyplot(fig)
            
        with tab3:
            st.write("#### Plano de Ação Estruturado e Cronograma (5W2H Executivo)")
            cronograma_dados = {
                "Gargalo (Causa Raiz)": ["Follow-up de prazos 100% manual e reativo", "Cadastros técnicos sem especificação OEM", "Falta de visibilidade analítica (Spend Analysis)", "Serviços contratados sem medição física"],
                "Ação Corretiva (Descrição do Trabalho)": [
                    "Padronizar rotina semanal de extração de pedidos em aberto (relatório nativo do ERP) e criar template de e-mail em lote. Definir 'Dia D' na semana.", 
                    "Implementar política de 'Tolerância Zero' com formulário padrão. Requisições sem Part Number/OEM serão devolvidas imediatamente à Engenharia.", 
                    "Extrair relatório de compras dos últimos 6 meses do ERP e montar Matriz de Kraljic e Curva ABC inicial via Excel/PowerBI.", 
                    "Criar um Boletim de Medição (BM) em formato doc/Excel. Estabelecer regra junto ao Financeiro para bloquear faturas sem BM assinado."
                ],
                "Prazo e Tempo Necessário": ["7 Dias", "10 Dias", "20 Dias", "15 Dias"],
                "Status / Reanálise": ["Semanalmente", "Quinzenal", "Mensal", "Mensal"]
            }
            st.table(pd.DataFrame(cronograma_dados))

        # Exportação apenas para Consultor
        st.markdown("---")
        st.markdown("### 📥 Exportação Executiva")
        ishikawa_buffer = gerar_ishikawa_pdf()
        pdf_data = gerar_pdf(st.session_state.respostas, cronograma_dados, ishikawa_buffer)
        
        col_btn1, col_btn2 = st.columns([2, 8])
        with col_btn1:
            st.download_button(label="Download Relatório PDF 📄", data=pdf_data, file_name="Relatorio_Diagnostico_VEDA_IA.pdf", mime="application/pdf", use_container_width=True)
        with col_btn2:
            if st.button("🔄 Iniciar Nova Auditoria", use_container_width=True):
                st.session_state.passo = 1
                st.session_state.respostas = {}
                st.rerun()
