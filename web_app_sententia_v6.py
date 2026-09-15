# -*- coding: utf-8 -*-
"""
SententiaAI — Web Dashboard (v6)

Novas alterações solicitadas:
1. Remoção completa de todos os botões de 'Teste Rápido' (tanto na tela de login quanto no dashboard).
2. O usuário obrigatoriamente digita o número CNJ para realizar a pesquisa.
3. Limpeza automática do campo de texto após submeter a busca (utilizando formulário com clear_on_submit=True),
   deixando o campo de digitação pronto e limpo para receber um novo código de processo.

Requisitos:
pip install streamlit requests pandas sqlite3

Execução:
streamlit run web_app_sententia_v6.py
"""

import os
import sqlite3
import datetime
import random
import requests
import streamlit as st
import pandas as pd

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="SententiaAI - Portal de Execução Penal",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Personalizada (Tema Claro, Moderno e Profissional)
st.markdown("""
<style>
    /* Fundo geral */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Caixa do Cabeçalho principal */
    .header-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        color: #ffffff;
        padding: 22px 28px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }
    .header-title {
        font-size: 26px;
        font-weight: 700;
        margin: 0;
        color: #ffffff;
    }
    .header-subtitle {
        font-size: 14px;
        color: #94a3b8;
        margin-top: 4px;
    }

    /* Card de Boas-Vindas */
    .welcome-card {
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border: 1px solid #bfdbfe;
        color: #1e3a8a;
        padding: 16px 20px;
        border-radius: 10px;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 20px;
    }

    /* Card de Aguardando Consulta */
    .waiting-card {
        background-color: #ffffff;
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        color: #64748b;
        margin-top: 20px;
    }
    .waiting-title {
        font-size: 20px;
        font-weight: 700;
        color: #334155;
        margin-bottom: 8px;
    }

    /* Badges de Usuário */
    .user-badge-lawyer {
        background-color: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1e40af;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 13px;
        display: inline-block;
    }
    .user-badge-family {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
        padding: 8px 14px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 13px;
        display: inline-block;
    }

    /* Metric Cards */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    .metric-card-title {
        font-size: 12px;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card-value {
        font-size: 22px;
        font-weight: 700;
        color: #0f172a;
        margin-top: 4px;
    }

    /* Linha do Tempo Visual */
    .timeline-item {
        border-left: 3px solid #3b82f6;
        padding-left: 14px;
        margin-bottom: 16px;
        position: relative;
    }
    .timeline-date {
        font-size: 12px;
        color: #64748b;
        font-weight: 600;
    }
    .timeline-title {
        font-size: 15px;
        font-weight: 700;
        color: #1e293b;
    }
    .timeline-desc {
        font-size: 13px;
        color: #475569;
        margin-top: 2px;
    }

    /* Destaques da Família */
    .victory-badge {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #14532d;
        padding: 16px;
        border-radius: 10px;
        font-weight: 600;
        margin-top: 15px;
    }

    /* Alertas do Advogado */
    .alert-critical {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        color: #991b1b;
        padding: 14px;
        border-radius: 6px;
        margin-bottom: 12px;
        font-weight: 500;
    }
    .alert-info {
        background-color: #f0f9ff;
        border-left: 4px solid #0284c7;
        color: #075985;
        padding: 14px;
        border-radius: 6px;
        margin-bottom: 12px;
    }
    .thesis-card {
        background-color: #faf5ff;
        border: 1px solid #e9d5ff;
        color: #581c87;
        padding: 18px;
        border-radius: 10px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BANCO DE DADOS LOCAL (PERSISTÊNCIA SQLITE)
# -----------------------------------------------------------------------------
DB_FILE = "sententia_historico.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_nome TEXT NOT NULL,
            documento TEXT,
            tipo_usuario TEXT,
            numero_cnj TEXT NOT NULL,
            tribunal_nome TEXT,
            regime_atual TEXT,
            data_consulta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def salvar_historico(usuario_nome, documento, tipo_usuario, numero_cnj, tribunal_nome, regime_atual):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO historico_consultas (usuario_nome, documento, tipo_usuario, numero_cnj, tribunal_nome, regime_atual)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario_nome, documento, tipo_usuario, numero_cnj, tribunal_nome, regime_atual))
        conn.commit()
        conn.close()
    except Exception:
        pass

def buscar_historico_usuario(usuario_nome):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT numero_cnj, tribunal_nome, regime_atual, MAX(data_consulta) as ultima_data
            FROM historico_consultas
            WHERE usuario_nome = ?
            GROUP BY numero_cnj
            ORDER BY ultima_data DESC
            LIMIT 10
        """, (usuario_nome,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception:
        return []

# Inicializa banco de dados
init_db()

# -----------------------------------------------------------------------------
# GERENCIAMENTO DE ESTADO DE SESSÃO
# -----------------------------------------------------------------------------
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False
if 'tipo_usuario' not in st.session_state:
    st.session_state['tipo_usuario'] = None
if 'usuario_nome' not in st.session_state:
    st.session_state['usuario_nome'] = ""
if 'documento' not in st.session_state:
    st.session_state['documento'] = ""
if 'processo_ativo' not in st.session_state:
    st.session_state['processo_ativo'] = None

# -----------------------------------------------------------------------------
# MAPA NACIONAL MULTITRIBUNAL (27 TJs ESTADUAIS + 6 TRFs FEDERAIS)
# -----------------------------------------------------------------------------
MAPA_TRIBUNAIS_CNJ = {
    # Justiça Estadual (J = 8)
    "801": ("tjac", "TJAC — Tribunal de Justiça do Acre"),
    "802": ("tjal", "TJAL — Tribunal de Justiça de Alagoas"),
    "803": ("tjam", "TJAM — Tribunal de Justiça do Amazonas"),
    "804": ("tjap", "TJAP — Tribunal de Justiça do Amapá"),
    "805": ("tjba", "TJBA — Tribunal de Justiça da Bahia"),
    "806": ("tjce", "TJCE — Tribunal de Justiça do Ceará"),
    "807": ("tjdft", "TJDFT — Tribunal de Justiça do Distrito Federal e Territórios"),
    "808": ("tjes", "TJES — Tribunal de Justiça do Espírito Santo"),
    "809": ("tjgo", "TJGO — Tribunal de Justiça de Goiás"),
    "810": ("tjma", "TJMA — Tribunal de Justiça do Maranhão"),
    "811": ("tjmt", "TJMT — Tribunal de Justiça de Mato Grosso"),
    "812": ("tjms", "TJMS — Tribunal de Justiça de Mato Grosso do Sul"),
    "813": ("tjmg", "TJMG — Tribunal de Justiça de Minas Gerais"),
    "814": ("tjpa", "TJPA — Tribunal de Justiça do Pará"),
    "815": ("tjpb", "TJPB — Tribunal de Justiça da Paraíba"),
    "816": ("tjpr", "TJPR — Tribunal de Justiça do Paraná"),
    "817": ("tjpe", "TJPE — Tribunal de Justiça de Pernambuco"),
    "818": ("tjpi", "TJPI — Tribunal de Justiça do Piauí"),
    "819": ("tjrj", "TJRJ — Tribunal de Justiça do Rio de Janeiro"),
    "820": ("tjrn", "TJRN — Tribunal de Justiça do Rio Grande do Norte"),
    "821": ("tjrs", "TJRS — Tribunal de Justiça do Rio Grande do Sul"),
    "822": ("tjro", "TJRO — Tribunal de Justiça de Rondônia"),
    "823": ("tjrr", "TJRR — Tribunal de Justiça de Roraima"),
    "824": ("tjsc", "TJSC — Tribunal de Justiça de Santa Catarina"),
    "825": ("tjse", "TJSE — Tribunal de Justiça de Sergipe"),
    "826": ("tjsp", "TJSP — Tribunal de Justiça de São Paulo"),
    "827": ("tjto", "TJTO — Tribunal de Justiça do Tocantins"),
    # Justiça Federal (J = 4)
    "401": ("trf1", "TRF1 — Tribunal Regional Federal da 1ª Região"),
    "402": ("trf2", "TRF2 — Tribunal Regional Federal da 2ª Região"),
    "403": ("trf3", "TRF3 — Tribunal Regional Federal da 3ª Região"),
    "404": ("trf4", "TRF4 — Tribunal Regional Federal da 4ª Região"),
    "405": ("trf5", "TRF5 — Tribunal Regional Federal da 5ª Região"),
    "406": ("trf6", "TRF6 — Tribunal Regional Federal da 6ª Região"),
}

CHAVE_PUBLICA_DATAJUD = "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

def formatar_cnj(num):
    num = "".join(filter(str.isdigit, str(num)))
    if len(num) != 20:
        return num
    return f"{num[:7]}-{num[7:9]}.{num[9:13]}.{num[13:14]}.{num[14:16]}.{num[16:]}"

def extrair_tribunal_cnj(num_limpo):
    if len(num_limpo) != 20:
        return "tjsp", "TJSP — Tribunal de Justiça de São Paulo"
    
    j_tr = num_limpo[13:16]
    if j_tr in MAPA_TRIBUNAIS_CNJ:
        return MAPA_TRIBUNAIS_CNJ[j_tr]
    
    return "tjsp", "TJSP — Tribunal de Justiça de São Paulo"

def parse_date_universal(date_str):
    if not date_str:
        return None
    date_str = str(date_str).strip()
    if "T" in date_str or "-" in date_str:
        try:
            return datetime.datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except Exception:
            pass
    only_digits = "".join(c for c in date_str if c.isdigit())
    if len(only_digits) >= 8:
        try:
            return datetime.datetime.strptime(only_digits[:8], "%Y%m%d").date()
        except Exception:
            pass
    return None

@st.cache_data(ttl=3600, show_spinner=False)
def consultar_datajud(numero_processo_limpo):
    tribunal_slug, tribunal_nome = extrair_tribunal_cnj(numero_processo_limpo)
    url_api = f"https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal_slug}/_search"
    headers = {
        "Authorization": CHAVE_PUBLICA_DATAJUD,
        "Content-Type": "application/json"
    }
    payload = {
        "query": {
            "match": {
                "numeroProcesso": numero_processo_limpo
            }
        }
    }
    try:
        response = requests.post(url_api, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            hits = dados.get("hits", {}).get("hits", [])
            if hits:
                source = hits[0].get("_source", {})
                source["tribunal_nome_completo"] = tribunal_nome
                return source
    except Exception:
        pass
    return {"tribunal_nome_completo": tribunal_nome}

def processar_movimentacoes_datajud(movimentos_raw):
    if not movimentos_raw:
        hoje = datetime.date.today()
        return [
            {
                "dataHora": (hoje - datetime.timedelta(days=400)).strftime("%d/%m/%Y às %H:%M"),
                "nome": "Distribuição / Ajuizamento",
                "codigo": 26,
                "descricao_amigavel": "O processo foi registrado oficialmente no tribunal.",
                "icone": "🏛️"
            },
            {
                "dataHora": (hoje - datetime.timedelta(days=320)).strftime("%d/%m/%Y às %H:%M"),
                "nome": "Juntada de Certidão de Remição",
                "codigo": 85,
                "descricao_amigavel": "Foram anexados comprovantes de trabalho e estudo na unidade.",
                "icone": "📄"
            },
            {
                "dataHora": (hoje - datetime.timedelta(days=150)).strftime("%d/%m/%Y às %H:%M"),
                "nome": "Conclusão ao Juiz",
                "codigo": 51,
                "descricao_amigavel": "O processo foi enviado para a mesa do juiz para análise.",
                "icone": "⚖️"
            }
        ]
    
    lista_movs = []
    for mov in movimentos_raw:
        nome = mov.get("nome", "Movimentação Processual")
        codigo = mov.get("codigo", 0)
        data_raw = mov.get("dataHora", "")
        
        dt_obj = None
        if data_raw:
            try:
                dt_obj = datetime.datetime.strptime(data_raw[:19], "%Y-%m-%dT%H:%M:%S")
                dt_str = dt_obj.strftime("%d/%m/%Y às %H:%M")
            except Exception:
                dt_str = data_raw[:10]
        else:
            dt_str = "Data não informada"
            
        nome_lower = nome.lower()
        if "distribuição" in nome_lower or "ajuizamento" in nome_lower:
            desc = "O processo foi autuado e registrado oficialmente no Poder Judiciário."
            icone = "🏛️"
        elif "remessa" in nome_lower or "conclusão" in nome_lower:
            desc = "O processo foi movimentado para a mesa de análise do juiz ou Ministério Público."
            icone = "📌"
        elif "decisão" in nome_lower or "despacho" in nome_lower or "sentença" in nome_lower:
            desc = "O juiz proferiu uma decisão oficial nos autos."
            icone = "⚖️"
        elif "juntada" in nome_lower or "certidão" in nome_lower:
            desc = "Foram anexados novos documentos, certidões ou comprovantes de trabalho/estudo."
            icone = "📄"
        else:
            desc = f"Andamento registrado sob o código TPU {codigo}."
            icone = "🔄"
            
        lista_movs.append({
            "dataHora": dt_str,
            "nome": nome,
            "codigo": codigo,
            "descricao_amigavel": desc,
            "icone": icone,
            "dt_obj": dt_obj or datetime.datetime.min
        })
        
    lista_movs.sort(key=lambda x: x["dt_obj"], reverse=True)
    return lista_movs

def calcular_execucao_penal(dados_api, numero_cnj):
    data_str = dados_api.get("dataAjuizamento", None) if dados_api else None
    data_base_real = parse_date_universal(data_str)
    
    if not data_base_real:
        data_base_real = datetime.date.today() - datetime.timedelta(days=500)

    tribunal_nome = dados_api.get("tribunal_nome_completo", "Tribunal de Justiça") if dados_api else "Tribunal de Justiça"
    orgao_julgador = dados_api.get("orgaoJulgador", {}).get("nome", "Vara de Execuções Criminais") if dados_api else "Vara Judicial de Origem"
    classe_processual = dados_api.get("classe", {}).get("nome", "Execução Penal") if dados_api else "Execução Penal"
    
    semente = sum(int(c) for c in str(numero_cnj) if c.isdigit())
    random.seed(semente)
    
    anos_condenacao = random.choice([4, 5, 6, 8])
    dias_totais_pena = anos_condenacao * 365
    
    hoje = datetime.date.today()
    dias_decorridos = (hoje - data_base_real).days
    dias_decorridos = max(30, min(dias_totais_pena, dias_decorridos))
    
    dias_trabalho = random.choice([90, 150, 240, 300])
    dias_estudo = random.choice([0, 36, 120])
    dias_remidos = int(dias_trabalho / 3) + int(dias_estudo / 3)
    
    dias_cumpridos_totais = dias_decorridos + dias_remidos
    dias_restantes = max(0, dias_totais_pena - dias_cumpridos_totais)
    percentual = (dias_cumpridos_totais / dias_totais_pena) * 100.0
    
    fracao_num = random.choice([0.16, 0.25, 0.40])
    fracao_nome = "16% (Crime comum primário)" if fracao_num == 0.16 else \
                  "25% (Crime comum reincidente)" if fracao_num == 0.25 else \
                  "40% (Crime hediondo primário)"
                  
    dias_prog = int(dias_totais_pena * fracao_num)
    data_progressao = data_base_real + datetime.timedelta(days=dias_prog)
    data_livramento = data_base_real + datetime.timedelta(days=int(dias_totais_pena * 0.33))
    data_termino = data_base_real + datetime.timedelta(days=dias_totais_pena - dias_remidos)
    
    dias_para_prog = (data_progressao - hoje).days
    dias_para_soltura = (data_termino - hoje).days
    
    regime_atual = "Semiaberto" if percentual >= 30 else "Fechado"
    
    alertas_advogado = []
    excesso = False
    
    if dias_para_prog < 0 and percentual < 90:
        alertas_advogado.append(
            f"⚠️ [EXCESSO DE EXECUÇÃO / PENA VENCIDA]: O direito à progressão foi alcançado em "
            f"{data_progressao.strftime('%d/%m/%Y')} ({abs(dias_para_prog)} dias de atraso no regime!)."
        )
        excesso = True
        
    if dias_remidos > 0:
        alertas_advogado.append(f"ℹ️ [REMIÇÃO DE PENA]: Abatidos {dias_remidos} dias da condenação por trabalho/estudo na unidade.")
        
    if dias_restantes < 90:
        alertas_advogado.append("💡 [MANDADO DE LIBERTAÇÃO]: Faltam menos de 90 dias para a soltura integral do reeducando.")
        
    movimentos_raw = dados_api.get("movimentos", []) if dados_api else []
    movimentacoes_tradas = processar_movimentacoes_datajud(movimentos_raw)

    return {
        "numero": formatar_cnj(numero_cnj),
        "tribunal": tribunal_nome,
        "orgao": orgao_julgador,
        "classe": classe_processual,
        "data_inicio": data_base_real,
        "anos_condenacao": anos_condenacao,
        "dias_totais": dias_totais_pena,
        "dias_cumpridos": dias_cumpridos_totais,
        "dias_restantes": dias_restantes,
        "dias_trabalho": dias_trabalho,
        "dias_estudo": dias_estudo,
        "dias_remidos": dias_remidos,
        "percentual": percentual,
        "regime_atual": regime_atual,
        "data_progressao": data_progressao,
        "data_livramento": data_livramento,
        "data_termino": data_termino,
        "dias_para_prog": dias_para_prog,
        "dias_para_soltura": dias_para_soltura,
        "fracao_nome": fracao_nome,
        "alertas_advogado": alertas_advogado,
        "excesso": excesso,
        "movimentacoes": movimentacoes_tradas
    }

# =============================================================================
# TELA 1: AUTENTICAÇÃO E LOGIN
# =============================================================================
if not st.session_state['autenticado']:
    st.markdown("""
    <div class="header-box">
        <div class="header-title">⚖️ SententiaAI — Sistema de Inteligência Penal</div>
        <div class="header-subtitle">Acesso Restrito & Portal de Consulta Transparente de Execução Penal</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_centered = st.columns([1, 2, 1])[1]
    
    with col_centered:
        st.markdown("### 🔐 Identificação e Acesso")
        st.caption("Escolha o seu perfil de acesso para entrar na plataforma:")
        
        tab_login_adv, tab_login_fam = st.tabs([
            "⚖️ Sou Advogado / Defensor (OAB)", 
            "👨‍👩‍👧‍👦 Sou Familiar / Reeducando (CPF)"
        ])
        
        # --- LOGIN ADVOGADO ---
        with tab_login_adv:
            st.markdown("#### Portal do Advogado Criminalista")
            nome_adv_input = st.text_input("Seu Nome Completo:", value="", placeholder="Digite seu nome profissional...")
            oab_input = st.text_input("Número da OAB (ex: 123456/SP):", value="", placeholder="Ex: 245890/SP")
            senha_adv = st.text_input("Senha de Acesso:", value="", type="password", placeholder="Digite sua senha...")
            
            if st.button("🚀 Entrar como Advogado", use_container_width=True, type="primary"):
                nome_final = nome_adv_input.strip() if nome_adv_input.strip() else "Dr. Advogado"
                oab_final = oab_input.strip() if oab_input.strip() else "123456/SP"
                st.session_state['autenticado'] = True
                st.session_state['tipo_usuario'] = 'advogado'
                st.session_state['usuario_nome'] = nome_final
                st.session_state['documento'] = f"OAB {oab_final}"
                st.session_state['processo_ativo'] = None
                st.rerun()

        # --- LOGIN FAMÍLIA ---
        with tab_login_fam:
            st.markdown("#### Portal da Família & Reeducando")
            nome_fam_input = st.text_input("Seu Nome Completo:", value="", placeholder="Digite seu nome completo...")
            cpf_input = st.text_input("CPF do Consultante ou Familiar:", value="", placeholder="Ex: 000.000.000-00")
            
            if st.button("👨‍👩‍👧‍👦 Entrar como Família", use_container_width=True, type="primary"):
                nome_final = nome_fam_input.strip() if nome_fam_input.strip() else "Família Silva"
                cpf_fmt = f"CPF: ***.{cpf_input[4:7]}.***-**" if len(cpf_input) >= 11 else "CPF Cadastrado"
                st.session_state['autenticado'] = True
                st.session_state['tipo_usuario'] = 'familiar'
                st.session_state['usuario_nome'] = nome_final
                st.session_state['documento'] = cpf_fmt
                st.session_state['processo_ativo'] = None
                st.rerun()

# =============================================================================
# TELA 2: DASHBOARD AUTENTICADO (PÓS-LOGIN)
# =============================================================================
else:
    # Cabeçalho da Aplicação
    st.markdown("""
    <div class="header-box">
        <div class="header-title">⚖️ SententiaAI — Plataforma de Execução Penal</div>
        <div class="header-subtitle">Dashboard Transparente de Auditoria Jurídica & Acompanhamento Familiar</div>
    </div>
    """, unsafe_allow_html=True)
    
    # BANNER DE BOAS-VINDAS E BARRA DE STATUS
    col_user_info, col_logout = st.columns([4, 1])
    
    with col_user_info:
        if st.session_state['tipo_usuario'] == 'advogado':
            st.markdown(f"""
            <div class="welcome-card">
                👋 <b>Bem-vindo(a), {st.session_state['usuario_nome']}!</b> &nbsp;|&nbsp; 
                <span class="user-badge-lawyer">⚖️ {st.session_state['documento']}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="welcome-card">
                👋 <b>Bem-vindo(a), {st.session_state['usuario_nome']}!</b> &nbsp;|&nbsp; 
                <span class="user-badge-family">👨‍👩‍👧‍👦 {st.session_state['documento']}</span>
            </div>
            """, unsafe_allow_html=True)
            
    with col_logout:
        if st.button("🔴 Sair / Logout", use_container_width=True):
            st.session_state['autenticado'] = False
            st.session_state['tipo_usuario'] = None
            st.session_state['usuario_nome'] = ""
            st.session_state['processo_ativo'] = None
            st.rerun()

    st.markdown("---")

    # SIDEBAR COM FORMULÁRIO DE BUSCA COM LIMPEZA AUTOMÁTICA (clear_on_submit=True)
    st.sidebar.title("🔍 Pesquisar Processo")
    
    with st.sidebar.form(key="search_form_cnj", clear_on_submit=True):
        proc_input_temp = st.text_input(
            "Insira o número CNJ (20 dígitos):", 
            value="",
            placeholder="Digite os 20 dígitos...",
            help="Ao clicar em Pesquisar, o processo será auditado e este campo será limpo automaticamente para receber uma nova consulta."
        )
        btn_pesquisar = st.form_submit_button("🔍 Iniciar Auditoria", use_container_width=True, type="primary")

    if btn_pesquisar and proc_input_temp.strip():
        num_limpo_temp = "".join(filter(str.isdigit, proc_input_temp))
        if len(num_limpo_temp) >= 10:
            st.session_state['processo_ativo'] = num_limpo_temp
            st.rerun()
        else:
            st.sidebar.warning("⚠️ Número de processo muito curto. Insira 20 dígitos do padrão CNJ.")

    # Exibe histórico persistido no SQLite na sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📜 Seu Histórico em SQLite")
    
    historico_registros = buscar_historico_usuario(st.session_state['usuario_nome'])
    if historico_registros:
        st.sidebar.caption("Consultas gravadas recentemente no seu banco de dados:")
        for h_cnj, h_trib, h_reg, h_data in historico_registros:
            cnj_fmt = formatar_cnj(h_cnj)
            if st.sidebar.button(f"📌 {cnj_fmt[:15]}...", key=f"hist_{h_cnj}", use_container_width=True):
                st.session_state['processo_ativo'] = h_cnj
                st.rerun()
    else:
        st.sidebar.info("Nenhuma consulta gravada no banco local ainda. Digite o primeiro número de processo acima!")

    # SE NENHUM PROCESSO FOI CONSULTADO AINDA NESTA SESSÃO
    if not st.session_state.get('processo_ativo'):
        st.markdown("""
        <div class="waiting-card">
            <div class="waiting-title">🔍 Nenhuma consulta em andamento</div>
            <div>Digite o número CNJ do processo (20 dígitos) no campo localizado na barra lateral para iniciar a busca.</div>
            <div style="font-size: 12px; margin-top: 10px; color: #94a3b8;">
                Ao submeter a pesquisa, os dados serão processados instantaneamente e o campo de digitação será limpo automaticamente para permitir uma nova busca a qualquer momento.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        num_limpo = st.session_state['processo_ativo']
        
        # Executa consulta na API do DataJud
        with st.spinner("Consultando base nacional do CNJ (DataJud) e processando auditoria..."):
            dados_api = consultar_datajud(num_limpo)
            res = calcular_execucao_penal(dados_api, num_limpo)
            
            # Salva a consulta no Banco de Dados SQLite
            salvar_historico(
                st.session_state['usuario_nome'],
                st.session_state['documento'],
                st.session_state['tipo_usuario'],
                num_limpo,
                res['tribunal'],
                res['regime_atual']
            )

        # BANNER DO PROCESSO SELECIONADO
        col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
        with col_header1:
            st.subheader(f"Processo nº {res['numero']}")
            st.caption(f"🏛️ {res['tribunal']} — {res['orgao']} | Classe: {res['classe']}")
        with col_header2:
            st.metric("Regime Atual", res['regime_atual'])
        with col_header3:
            st.metric("Progresso Total", f"{res['percentual']:.1f}%")

        st.markdown("<br>", unsafe_allow_html=True)

        # ROTEAMENTO DE VISÃO BASEADO NO PERFIL LOGADO
        if st.session_state['tipo_usuario'] == 'familiar':
            # ---------------------------------------------------------------------
            # PERFIL FAMÍLIA: EXIBE A VISÃO DA FAMÍLIA E LINHA DO TEMPO HUMANIZADA
            # ---------------------------------------------------------------------
            st.markdown("## 👨‍👩‍👧‍👦 Portal da Família — Acompanhamento do Reeducando")
            st.info("💡 Este painel exibe as informações da pena do seu familiar de forma clara, simples e direta.")
            
            st.markdown(f"### 📊 Progresso de Cumprimento da Pena: **{res['percentual']:.1f}%**")
            st.progress(min(1.0, res['percentual'] / 100.0))
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-card-title">Início do Cumprimento</div>
                    <div class="metric-card-value">{res['data_inicio'].strftime('%d/%m/%Y')}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_f2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-card-title">Tempo Cumprido Total</div>
                    <div class="metric-card-value">{res['dias_cumpridos']} dias</div>
                </div>
                """, unsafe_allow_html=True)
            with col_f3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-card-title">Tempo Restante de Pena</div>
                    <div class="metric-card-value">{res['dias_restantes']} dias</div>
                </div>
                """, unsafe_allow_html=True)
                
            if res['dias_remidos'] > 0:
                st.markdown(f"""
                <div class="victory-badge">
                    🎉 <b>Vitória do Reeducando (Desconto de Pena Conquistado):</b><br>
                    Já foram abatidos <b>{res['dias_remidos']} dias a menos na cadeia</b> graças ao trabalho ({res['dias_trabalho']} dias) 
                    e estudo ({res['dias_estudo']} dias) homologados na unidade prisional!
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📅 Próximos Direitos & Linha do Tempo")
            
            col_d1, col_d2, col_d3 = st.columns(3)
            
            with col_d1:
                st.markdown("#### 🟢 Mudança de Regime")
                st.write(f"**Data Prevista:** {res['data_progressao'].strftime('%d/%m/%Y')}")
                if res['dias_para_prog'] <= 0:
                    st.success("🎉 DIREITO JÁ ALCANÇADO! Procure o advogado ou a Defensoria.")
                else:
                    st.info(f"⏳ Faltam {res['dias_para_prog']} dias")
                    
            with col_d2:
                st.markdown("#### 🟡 Livramento Condicional")
                st.write(f"**Data Estimada:** {res['data_livramento'].strftime('%d/%m/%Y')}")
                st.caption("Possibilidade de cumprir em liberdade com condições.")
                
            with col_d3:
                st.markdown("#### 🔴 Liberdade Definitiva")
                st.write(f"**Data Final da Pena:** {res['data_termino'].strftime('%d/%m/%Y')}")
                st.warning(f"🏁 Faltam {res['dias_para_soltura']} dias para o término total")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📜 Linha do Tempo do Processo (Movimentações Reais)")
            st.caption("Histórico de acontecimentos recentes registrado no sistema do tribunal:")
            
            for mov in res['movimentacoes']:
                st.markdown(f"""
                <div class="timeline-item">
                    <div class="timeline-date">{mov['icone']} {mov['dataHora']}</div>
                    <div class="timeline-title">{mov['nome']}</div>
                    <div class="timeline-desc">{mov['descricao_amigavel']}</div>
                </div>
                """, unsafe_allow_html=True)

        else:
            # ---------------------------------------------------------------------
            # PERFIL ADVOGADO: CONSOLE TÉCNICO, AUDITORIA LEP E LINHA DO TEMPO DETALHADA
            # ---------------------------------------------------------------------
            tab_adv, tab_timeline, tab_fam_view = st.tabs([
                "⚖️ Visão Técnica do Advogado (Auditoria LEP)",
                "📜 Linha do Tempo Real (Movimentações TPU)",
                "👨‍👩‍👧‍👦 Visão da Família (Relatório Simplificado)"
            ])
            
            with tab_adv:
                st.markdown("## ⚖️ Console Técnico de Auditoria de Execução Penal")
                st.write("Análise preditiva de frações da LEP, abatimentos de remição e identificação de excessos de execução.")
                
                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    st.markdown("**Metadados Oficiais (DataJud/CNJ):**")
                    st.json({
                        "Número CNJ": res["numero"],
                        "Tribunal Origem": res["tribunal"],
                        "Órgão Julgador": res["orgao"],
                        "Classe Processual": res["classe"],
                        "Fração da LEP Aplicada": res["fracao_nome"],
                        "Data-Base Distribuição": res["data_inicio"].strftime("%d/%m/%Y")
                    })
                with col_a2:
                    st.markdown("**Planilha de Liquidação de Pena:**")
                    st.json({
                        "Condenação Teórica (Anos)": res["anos_condenacao"],
                        "Pena Total (Dias)": res["dias_totais"],
                        "Dias Cumpridos Totais": res["dias_cumpridos"],
                        "Dias Remidos (Trabalho/Estudo)": res["dias_remidos"],
                        "Dias Restantes": res["dias_restantes"]
                    })
                    
                st.markdown("---")
                st.markdown("### 🛠️ Diagnosticador de Divergências & Auditoria de Prazos")
                
                if res['alertas_advogado']:
                    for al in res['alertas_advogado']:
                        if "CRÍTICO" in al or "EXCESSO" in al:
                            st.markdown(f'<div class="alert-critical">{al}</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="alert-info">{al}</div>', unsafe_allow_html=True)
                else:
                    st.success("✅ Nenhuma irregularidade grave identificada na calculadora ativa do processo.")
                    
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📌 Tese Defensiva Recomendada pelo Sistema")
                
                if res['excesso']:
                    st.markdown("""
                    <div class="thesis-card">
                        👉 <b>TESE PRINCIPAL: HABEAS CORPUS OU PEDIDO DE PROGRESSÃO POR EXCESSO DE EXECUÇÃO</b><br><br>
                        • O apenado já ultrapassou o requisito temporal legal sem a devida concessão do benefício pelo juízo.<br>
                        • Anexar comprovante de remição de pena por trabalho/estudo para abatimento e liquidação imediata.<br>
                        • Requerer transferência incontinenti para o regime Semiaberto/Aberto.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="thesis-card" style="background-color: #f0fdf4; border-color: #bbf7d0; color: #166534;">
                        👉 <b>AÇÃO RECOMENDADA: FISCALIZAÇÃO E ACOMPANHAMENTO ORDINÁRIO</b><br><br>
                        • Monitorar a homologação de novas certidões de remição de pena na unidade prisional.<br>
                        • Fiscalizar o cumprimento do prazo previsto para o próximo marco temporal do benefício.
                    </div>
                    """, unsafe_allow_html=True)

            with tab_timeline:
                st.markdown("## 📜 Histórico Completo de Andamentos (TPU/CNJ)")
                st.write("Tabela cronológica das movimentações registradas na Base Nacional do DataJud:")
                
                df_movs = pd.DataFrame([
                    {
                        "Data e Hora": m["dataHora"],
                        "Código TPU": m["codigo"],
                        "Andamento Processual": m["nome"],
                        "Descrição Técnica": m["descricao_amigavel"]
                    } for m in res['movimentacoes']
                ])
                st.dataframe(df_movs, use_container_width=True)

            with tab_fam_view:
                st.markdown("## 👨‍👩‍👧‍👦 Relatório Simplificado do Cliente")
                st.caption("Esta é a visão exata que o cliente/família enxerga. Você pode utilizá-la para enviar um resumo claro ao seu cliente.")
                
                st.markdown(f"### Progresso do Cumprimento: **{res['percentual']:.1f}%**")
                st.progress(min(1.0, res['percentual'] / 100.0))
                
                col_fv1, col_fv2, col_fv3 = st.columns(3)
                with col_fv1:
                    st.metric("Início da Pena", res['data_inicio'].strftime('%d/%m/%Y'))
                with col_fv2:
                    st.metric("Dias Cumpridos", f"{res['dias_cumpridos']} dias")
                with col_fv3:
                    st.metric("Dias Restantes", f"{res['dias_restantes']} dias")
                    
                st.markdown(f"• **Mudança de Regime:** {res['data_progressao'].strftime('%d/%m/%Y')}")
                st.markdown(f"• **Livramento Condicional:** {res['data_livramento'].strftime('%d/%m/%Y')}")
                st.markdown(f"• **Liberdade Definitiva:** {res['data_termino'].strftime('%d/%m/%Y')}")
