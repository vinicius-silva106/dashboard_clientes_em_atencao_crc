"""
Dashboard Executivo – Clientes em Atenção (CRC)
================================================
Execute com:  streamlit run app.py
"""

import pandas as pd
import streamlit as st

from data.gsheets_reader import load_raw_data
from data.processor import (
    process,
    get_week_labels,
    filter_by_week,
    filter_escalations,
    filter_lentidao,
    filter_tributaria,
    filter_lentidao_glosa,
)
from viz.charts import (
    donut_eventos,
    bar_regionais,
    bar_produtos,
    mapa_brasil,
    style_table,
)
from utils.report_pdf import generate_pdf_report
from utils.report_pptx import generate_pptx_report

@st.cache_data(show_spinner=False)
def get_cached_pdf(kpis, escalations, tributaria):
    return generate_pdf_report(kpis, escalations, tributaria)

@st.cache_data(show_spinner=False)
def get_cached_pptx(kpis, escalations, tributaria):
    return generate_pptx_report(kpis, escalations, tributaria)


# ---------------------------------------------------------------------------
# Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CRC – Clientes em Atenção",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Estado da Sessão - Filtros de Gráficos
# ---------------------------------------------------------------------------
if "sel_chart_evento" not in st.session_state: st.session_state.sel_chart_evento = None
if "sel_chart_regional" not in st.session_state: st.session_state.sel_chart_regional = None
if "sel_chart_prod" not in st.session_state: st.session_state.sel_chart_prod = None
if "pdf_data" not in st.session_state: st.session_state.pdf_data = None

# CSS global - Paleta Sigma (Teal & Navy) + Suporte a Temas
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --teal: #059669;
        --navy-bg: #0D1B2A;
        --navy-card: #1B263B;
        --navy-light: #415A77;
        --text-dark: #E0E1DD;
        --text-light: #1D3557;
        --danger: #D62828;
        --success: #059669;
    }

    /* Ajuste para Tema Claro/Escuro Automático */
    @media (prefers-color-scheme: light) {
        .main { background-color: #F8F9FA !important; }
        .stMarkdown, .stCaption, h1, h2, h3 { color: var(--text-light) !important; }
        .kpi-card { background-color: white !important; border: 1px solid #E0E0E0 !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important; color: #1D3557 !important; }
        .kpi-value { color: #1D3557 !important; }
        .kpi-label { color: #555 !important; }
        .kpi-previous { color: #666 !important; }
        .action-block { background-color: #FFF5F5 !important; border-left: 5px solid var(--danger) !important; }
    }

    @media (prefers-color-scheme: dark) {
        .main { background-color: var(--navy-bg) !important; }
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: var(--navy-bg); color: var(--text-dark); }
        .kpi-card { background-color: var(--navy-card) !important; border: 1px solid var(--navy-light) !important; color: white !important; }
        .kpi-value { color: white !important; }
        .action-block { background-color: rgba(214, 40, 40, 0.1) !important; border-left: 5px solid var(--danger) !important; }
    }

    /* KPI Cards Layout */
    .kpi-card {
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 20px;
        min-height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: transform 0.2s;
    }
    .kpi-card:hover { transform: translateY(-3px); }
    .kpi-label { font-size: 0.8rem; text-transform: uppercase; font-weight: 600; margin-bottom: 8px; }
    .kpi-value { font-size: 2.2rem; font-weight: 700; margin-bottom: 4px; }
    .kpi-delta { font-size: 0.85rem; font-weight: 500; }
    .delta-up { color: var(--danger); }
    .delta-down { color: var(--success); }
    .kpi-previous { font-size: 0.75rem; opacity: 0.7; margin-top: 4px; }

    /* Headers and Titles */
    h1 { font-weight: 800; font-size: 2.2rem; margin-bottom: 0.5rem; }
    h2 { border-bottom: 2px solid var(--teal); padding-bottom: 10px; margin-top: 2.5rem; font-size: 1.5rem; font-weight: 700; }
    
    .stButton>button { background-color: var(--teal) !important; color: white !important; border-radius: 8px !important; }
    
    .action-title { font-weight: 700; color: var(--danger); margin-bottom: 5px; text-transform: uppercase; font-size: 0.85rem; }
    
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.markdown("# Dashboard Executivo | Status CRC")
st.markdown("### Gestão de Clientes em Atenção")
st.caption("Monitoramento analítico e suporte à decisão em tempo real")
st.divider()

# O indíce flutuante antigo foi substituído por abas st.tabs()

# ---------------------------------------------------------------------------
# Carregamento e processamento
# ---------------------------------------------------------------------------
raw_df = load_raw_data()
df_all = process(raw_df)

if df_all.empty:
    st.error("⚠️ Nenhum dado disponível. Verifique a conexão com o Google Sheets.")
    st.stop()

with st.sidebar:
    st.markdown("## Filtros")
    
    # Filtro de Semana Dinâmico (Multiselect ou Comparação)
    semanas_disp = sorted(df_all["Semana"].dropna().unique().tolist(), reverse=True) if "Semana" in df_all.columns else []
    if semanas_disp:
        semanas_selecionadas = st.multiselect(
            "Período (Semana) - Selecione um ou mais",
            options=semanas_disp,
            default=[semanas_disp[0]],
            format_func=lambda x: f"Semana {int(x)}"
        )
        if len(semanas_selecionadas) == 2:
            # Comparação explícita de duas semanas
            semanas_ord = sorted(semanas_selecionadas, reverse=True)
            semana_atual = int(semanas_ord[0])
            semana_anterior = int(semanas_ord[1])
            df_atual = filter_by_week(df_all, semana_atual)
            df_ant = filter_by_week(df_all, semana_anterior)
        else:
            # Intervalo ou semana única
            df_atual = df_all[df_all["Semana"].isin(semanas_selecionadas)] if semanas_selecionadas else pd.DataFrame()
            oldest = int(min(semanas_selecionadas)) if semanas_selecionadas else (int(semanas_disp[0]) if semanas_disp else 0)
            semana_anterior = oldest - 1
            df_ant = filter_by_week(df_all, semana_anterior)
            semana_atual_str = ", ".join(map(str, sorted([int(s) for s in semanas_selecionadas], reverse=True)))
            semana_atual = oldest # for fallback
    else:
        semana_atual, semana_anterior = get_week_labels(df_all)
        df_atual = filter_by_week(df_all, semana_atual)
        df_ant = filter_by_week(df_all, semana_anterior)

with st.sidebar:
    st.markdown("### Regional")
    regionais_disp = sorted(df_atual["Regional"].dropna().unique().tolist()) if not df_atual.empty else []
    sel_regional = st.multiselect("Regionais", options=regionais_disp, default=regionais_disp, label_visibility="collapsed")

    st.divider()
    st.markdown("### Vertical / Produto")
    produtos_disp = sorted(df_atual["Produto"].dropna().unique().tolist()) if not df_atual.empty and "Produto" in df_atual.columns else []
    sel_produto = st.multiselect("Vertical / Produto", options=produtos_disp, default=produtos_disp, label_visibility="collapsed")

    st.divider()
    st.markdown("### Evento Motivador")
    eventos_disp = sorted(df_atual["Evento"].dropna().unique().tolist()) if not df_atual.empty else []
    sel_evento = st.multiselect("Evento Motivador", options=eventos_disp, default=eventos_disp, label_visibility="collapsed")

    st.divider()
    if st.button("🔄 Sincronizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Mapeamento de Rótulos para Eventos Reais (Bi-direcional)
MAPPING = {
    "Escalation Cliente": ["Escalation Cliente"],
    "Escalations": ["Escalation Cliente"],
    "Lentidão": ["Lentidão", "Lentidão recorrente"],
    "Lentidão recorrente": ["Lentidão", "Lentidão recorrente"],
    "Ref. Tributária": ["Ref. Tributária/OnePass"],
    "Ref. Tributária/OnePass": ["Ref. Tributária/OnePass"],
    "Glosas": ["Glosa"],
    "Glosa": ["Glosa"]
}

# Filtros globais aplicados à base atual para os KPIs
mask = (
    df_atual["Regional"].isin(sel_regional)
    & df_atual["Evento"].isin(sel_evento)
)
if "Produto" in df_atual.columns and sel_produto:
    mask &= df_atual["Produto"].isin(sel_produto)

# Filtros vindos da seleção nos gráficos (Session State)
if st.session_state.sel_chart_evento:
    target = MAPPING.get(st.session_state.sel_chart_evento, [st.session_state.sel_chart_evento])
    mask &= (df_atual["Evento"].isin(target))

if st.session_state.sel_chart_regional:
    mask &= (df_atual["Regional"] == st.session_state.sel_chart_regional)
if st.session_state.sel_chart_prod:
    mask &= (df_atual["Produto"] == st.session_state.sel_chart_prod)

df = df_atual[mask].copy()

# Se houver filtro secundário ativo, mostrar botão para limpar
if st.session_state.sel_chart_evento or st.session_state.sel_chart_regional or st.session_state.sel_chart_prod:
    if st.button("✖ Limpar Filtros Selecionados", type="secondary"):
        st.session_state.sel_chart_evento = None
        st.session_state.sel_chart_regional = None
        st.session_state.sel_chart_prod = None
        st.rerun()

# ---------------------------------------------------------------------------
# TAB VIEW E CÁLCULOS
# ---------------------------------------------------------------------------

def kpi_card(title, current, previous, is_critical=False, is_pct=False):
    delta = current - previous
    delta_pct = (delta / previous * 100) if previous else 0
    delta_str = f"{'+' if delta >= 0 else ''}{float(round(delta_pct, 1))}%"
    delta_class = "delta-up" if (delta > 0 and not is_pct) else "delta-down"
    if is_pct: delta_class = "delta-down" if delta < 0 else "delta-up"

    css_class = "kpi-card kpi-critical" if is_critical else "kpi-card"
    curr_fmt = f"{current}%" if is_pct else str(current)
    prev_fmt = f"{previous}%" if is_pct else str(previous)
    
    st.markdown(
        f"""
        <div class="{css_class}">
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{curr_fmt}</div>
            <div class="kpi-delta {delta_class}">{delta_str} vs semana ant.</div>
            <div class="kpi-previous">Semana Anterior: {prev_fmt}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Cálculos KPIs
total_atual = len(df)
total_ant = len(df_ant) if not df_ant.empty else 0

esc_df = filter_escalations(df)
esc_ant = filter_escalations(df_ant)
n_esc = len(esc_df)
n_esc_ant = len(esc_ant)
pct_esc = float(round(n_esc / total_atual * 100, 1)) if total_atual else 0.0

lent_df = filter_lentidao(df)
lent_ant = filter_lentidao(df_ant)
n_lent = len(lent_df)
n_lent_ant = len(lent_ant)

trib_df = filter_tributaria(df)
trib_ant = filter_tributaria(df_ant)
n_trib = len(trib_df)
n_trib_ant = len(trib_ant)

glosa_df = df[df["Glosa_Aplicada"] == "Sim"]
glosa_ant = df_ant[df_ant["Glosa_Aplicada"] == "Sim"] if not df_ant.empty else pd.DataFrame()
n_glosa = len(glosa_df)
n_glosa_ant = len(glosa_ant)

# Ordenação Dinâmica dos KPIs
kpi_data = [
    {"label": "Escalations", "current": n_esc, "prev": n_esc_ant, "critical": (n_esc > n_esc_ant)},
    {"label": "Lentidão", "current": n_lent, "prev": n_lent_ant, "critical": False},
    {"label": "Ref. Tributária", "current": n_trib, "prev": n_trib_ant, "critical": False},
    {"label": "Glosas", "current": n_glosa, "prev": n_glosa_ant, "critical": (n_glosa > 0)},
]
kpi_data_sorted = sorted(kpi_data, key=lambda x: x["current"], reverse=True)
full_kpi_for_pdf = [{"label": "Volume Total", "current": total_atual, "prev": total_ant}] + kpi_data_sorted

# ---------------------------------------------------------------------------
# RENDERIZAÇÃO DAS ABAS
# ---------------------------------------------------------------------------
tab_geral, tab_detalhes = st.tabs(["Visão Geral", "Detalhamento por Cliente"])

with tab_geral:
    st.markdown("## Indicadores de Performance")
    
    row1_kpi1, row1_kpi2, row1_kpi3, row1_kpi4, row1_kpi5 = st.columns(5)
    
    with row1_kpi1:
        kpi_card("Volume Total", total_atual, total_ant)
    
    rows = [row1_kpi2, row1_kpi3, row1_kpi4, row1_kpi5]
    for col, data in zip(rows, kpi_data_sorted):
        with col:
            kpi_card(data["label"], data["current"], data["prev"], is_critical=data["critical"])
    
    st.divider()

    # ---------------------------------------------------------------------------
    # ANÁLISE EXECUTIVA
    # ---------------------------------------------------------------------------
    st.markdown("## Análise Executiva")
    
    top_eventos = df["Evento"].value_counts()
    maior_risco = top_eventos.index[0] if not top_eventos.empty else "N/D"
    vol_risco = top_eventos.iloc[0] if not top_eventos.empty else 0
    pct_risco = float(round(vol_risco/total_atual*100, 1)) if total_atual else 0.0
    
    top_regionais = df["Regional"].value_counts().head(2).index.tolist()
    reg_str = " e ".join(top_regionais) if top_regionais else "N/D"
    
    variacao_total = 0.0
    if total_ant > 0:
        variacao_total = float(((total_atual - total_ant) / total_ant) * 100)
        variacao_total = float(round(variacao_total, 1))
    
    sinal_var = "Aumento" if variacao_total > 0 else "Queda" if variacao_total < 0 else "Estabilidade"
    
    col_exec1, col_exec2, col_exec3 = st.columns(3)
    with col_exec1:
        st.info(f"📍 **Panorama Geral**\nA semana registra **{total_atual} clientes em atenção**, representando uma **{sinal_var} de {abs(variacao_total)}%** frente à semana anterior.")
    with col_exec2:
        st.warning(f"⚠️ **Concentração de Risco**\nO evento motivador **'{maior_risco}'** é o detrator principal, com **{vol_risco} casos** ({pct_risco}% da base atual).")
    with col_exec3:
        st.error(f"🌐 **Foco Geográfico**\nAs intervenções devem priorizar as regionais **{reg_str}**, que concentram o maior volume de criticidade.")
    
    st.divider()

    # ---------------------------------------------------------------------------
    # VISUALIZAÇÕES E GRÁFICOS
    # ---------------------------------------------------------------------------
    st.markdown("## Distribuições Analíticas")
    
    col_visual_1, col_visual_2 = st.columns([1, 1])
    
    with col_visual_1:
        res_ev = st.plotly_chart(donut_eventos(df), use_container_width=True, on_select="rerun")
        if res_ev and res_ev.get("selection", {}).get("points"):
            st.session_state.sel_chart_evento = res_ev["selection"]["points"][0]["label"]
            st.rerun()
    
    with col_visual_2:
        res_reg = st.plotly_chart(bar_regionais(df), use_container_width=True, on_select="rerun")
        if res_reg and res_reg.get("selection", {}).get("points"):
            st.session_state.sel_chart_regional = res_reg["selection"]["points"][0]["y"]
            st.rerun()
    
    col_visual_3, col_visual_4 = st.columns([1, 1])
    with col_visual_3:
        res_prod = st.plotly_chart(bar_produtos(df), use_container_width=True, on_select="rerun")
        if res_prod and res_prod.get("selection", {}).get("points"):
            st.session_state.sel_chart_prod = res_prod["selection"]["points"][0]["y"]
            st.rerun()
    with col_visual_4:
        res_map = st.plotly_chart(mapa_brasil(df), use_container_width=True, on_select="rerun")
        if res_map and res_map.get("selection", {}).get("points"):
            st.session_state.sel_chart_regional = res_map["selection"]["points"][0]["hovertext"]
            st.rerun()

    st.divider()

with tab_detalhes:

    # ---------------------------------------------------------------------------
    # ESCALATIONS
    # ---------------------------------------------------------------------------
    st.markdown("## Escalations")
    
    if esc_df.empty:
        st.success("✔ Operação normal: Nenhum Escalation registrado.")
    else:
        esc_sorted = esc_df.sort_values("Regional") if "Regional" in esc_df.columns else esc_df
        display_df = esc_sorted[["Cliente", "Regional", "Produto", "HealthScore", "Status"]].copy()
        display_df.rename(columns={"Status": "Status / Causa Raiz"}, inplace=True)
        st.table(style_table(display_df))
        
        # Botão de exportação
        csv_esc = display_df.to_csv(index=False).encode('utf-8')
        st.download_button("🔽 Exportar Escalations (CSV)", data=csv_esc, file_name="escalations.csv", mime="text/csv")
    
        # Bloco de Ação Requerida Reestruturado
        if total_atual and (n_esc > n_esc_ant or (n_esc / total_atual) > 0.30):
            st.error(f"🚨 **AÇÃO REQUERIDA**: Escalations subiram ou representam muito da base. ({n_esc} casos, {pct_esc}%). Revisão executiva imediata necessária.")
        else:
            st.warning("⚠️ **AÇÃO REQUERIDA**: Monitoramento ativo. Casos estáveis, mas requerem acompanhamento.")
    
    st.divider()
    
    # ---------------------------------------------------------------------------
    # REFORMA TRIBUTÁRIA
    # ---------------------------------------------------------------------------
    st.markdown("## Reforma Tributária / OnePass")
    
    if trib_df.empty:
        st.success("✅ Sem pendências ativas de Reforma Tributária.")
    else:
        trib_sorted = trib_df.sort_values("Regional") if "Regional" in trib_df.columns else trib_df
        display_df_trib = trib_sorted[["Cliente", "Regional", "Produto", "HealthScore", "Status"]].copy()
        display_df_trib.rename(columns={"Status": "Status / Causa Raiz"}, inplace=True)
        st.table(style_table(display_df_trib))
    
        st.warning("⚠️ **AÇÃO REQUERIDA: FORÇA-TAREFA PRODUTO** - Manter acompanhamento diário das homologações e reports semanais de progresso.")
    
    st.divider()

    # ---------------------------------------------------------------------------
    # QUADRANTES: GLOSAS E LENTIDÃO
    # ---------------------------------------------------------------------------
    st.markdown("## Monitoramento de Glosas & Performance")
    
    col_glosa, col_lent = st.columns(2)
    
    with col_glosa:
        st.markdown("### Glosas")
        real_glosa_df = df[df["Status"].str.contains("glosa", case=False, na=False)]
        if real_glosa_df.empty:
            st.info("Nenhuma glosa ativa identificada no status.")
        else:
            cols_glosa = [c for c in ["Cliente", "Regional", "Produto", "HealthScore", "Status"] if c in real_glosa_df.columns]
            disp_glosa = real_glosa_df[cols_glosa].copy()
            disp_glosa.rename(columns={"Status": "Evidência de Glosa"}, inplace=True)
            st.table(style_table(disp_glosa))
    
    with col_lent:
        st.markdown("### Lentidão Sistêmica")
        if lent_df.empty:
            st.info("Performance sistêmica dentro dos padrões esperados.")
        else:
            cols_lent = [c for c in ["Cliente", "Regional", "Produto", "HealthScore", "Status"] if c in lent_df.columns]
            disp_lent = lent_df[cols_lent].copy()
            disp_lent.rename(columns={"Status": "Causa Raiz"}, inplace=True)
            st.table(style_table(disp_lent))
    
    st.divider()
    
    # ---------------------------------------------------------------------------
    # RECOMENDAÇÕES E PRÓXIMOS PASSOS
    # ---------------------------------------------------------------------------
    st.markdown("## Recomendações Estratégicas")
    
    acoes = []
    
    if n_lent > 3:
        acoes.append({
            "Estratégia": "Auditoria de Performance Sistêmica",
            "Proprietário": "Lideranças Técnicas",
            "Deadline": "Imediato",
            "Impacto": "Crítico",
        })
    
    if not trib_df.empty:
        acoes.append({
            "Estratégia": "Acompanhamento de Homologação (Tributário)",
            "Proprietário": "Time de Produto",
            "Deadline": "Próxima Reunião",
            "Impacto": "Alto",
        })
    
    if n_glosa > 0:
        acoes.append({
            "Estratégia": "Revisão de SLAs Comerciais",
            "Proprietário": "Diretoria Comercial",
            "Deadline": "Imediato",
            "Impacto": "Crítico",
        })
    
    if acoes:
        df_acoes = pd.DataFrame(acoes)
        st.table(df_acoes)
        # O botão de CSV
        csv_acoes = df_acoes.to_csv(index=False).encode('utf-8')
        st.download_button("🔽 Exportar Recomendações (CSV)", data=csv_acoes, file_name="recomendacoes.csv", mime="text/csv")
    else:
        st.info("Operação estável. Monitorar métricas de saúde preventivamente.")
    
    st.divider()
    st.caption("Dashboard Executivo CRC | Dados consolidados | Atualização Automática")

# ---------------------------------------------------------------------------
# PDF Export (Instigated natively on the sidebar)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.divider()
    st.markdown("### Relatório Executivo")
    try:
        pdf_bytes = get_cached_pdf(full_kpi_for_pdf, esc_df, trib_df)
        st.download_button(
            label="📄 Exportar PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_CRC.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="pdf_export_btn"
        )
        
        pptx_bytes = get_cached_pptx(full_kpi_for_pdf, esc_df, trib_df)
        st.download_button(
            label="📊 Exportar Slides (.pptx)",
            data=pptx_bytes,
            file_name=f"Relatorio_CRC.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            use_container_width=True,
            key="pptx_export_btn"
        )
    except Exception as e:
        st.error(f"Erro ao compilar documento: {e}")

