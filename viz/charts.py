"""
Módulo de visualizações Plotly para o dashboard CRC.
"""

import json
import urllib.request
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ---------------------------------------------------------------------------
# Paleta de cores corporativa (Diretoria/Premium)
# ---------------------------------------------------------------------------
COLORS = {
    "navy": "#254B62",      # Navy Profundo (Identidade Sigma)
    "teal": "#059669",      # Emerald/Teal (Identidade Sigma)
    "accent": "#457B9D",    # Azul Médio
    "neutral": "#E0E1DD",   # Texto/Contraste
    "success": "#059669",   # Verde Emerald
    "warning": "#E9C46A",   # Amarelo Atenção
    "danger": "#D62828",    # Vermelho Intenso
    "critical": "#9B2226",  # Vermelho Profundo
}

# Gradientes para escalas
GRADIENT_BLUE_RED = ["#1B263B", "#415A77", "#778DA9", "#E76F51", "#9B2226"]
GRADIENT_HEALTH = ["#9B2226", "#E76F51", "#E9C46A", "#2A9D8F"]


# ---------------------------------------------------------------------------
# Donut – Eventos Motivadores
# ---------------------------------------------------------------------------

def donut_eventos(df: pd.DataFrame) -> go.Figure:
    if df.empty or "Evento" not in df.columns:
        return go.Figure()

    # Garante que temos uma Series se houver duplicatas residuais
    evento_series = df["Evento"]
    if isinstance(evento_series, pd.DataFrame):
        evento_series = evento_series.iloc[:, 0]

    counts = evento_series.value_counts()
    fig = go.Figure(
        go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.6,
            textinfo="percent",  # Percentual fixo
            textfont=dict(size=14, color="white"),
            hovertemplate="<b>%{label}</b><br>Volume: %{value}<br>Representação: %{percent}<extra></extra>",
            marker=dict(colors=[COLORS["teal"], COLORS["navy"], "#457B9D", "#1D3557", "#006D77", "#83C5BE", "#EDF6F9"]),
        )
    )
    fig.update_layout(
        title_text="Distribuição por Evento Motivador",
        title_x=0,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.1),
        margin=dict(t=50, b=10, l=10, r=100),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["neutral"]),
        autosize=True,
    )
    return fig


# ---------------------------------------------------------------------------
# Barras horizontais – Regionais
# ---------------------------------------------------------------------------

def bar_regionais(df: pd.DataFrame) -> go.Figure:
    if df.empty or "Regional" not in df.columns:
        return go.Figure()

    # Garante que temos uma Series
    reg_series = df["Regional"]
    if isinstance(reg_series, pd.DataFrame):
        reg_series = reg_series.iloc[:, 0]

    counts = reg_series.value_counts().reset_index()
    counts.columns = ["Regional", "Casos"]
    counts = counts.sort_values("Casos", ascending=True)
    total = counts["Casos"].sum()
    counts["Percentual"] = (counts["Casos"] / total * 100).round(0).astype(int).astype(str) + "%"

    # Lógica de Cores: Vibrante para alto volume, Neutro (Cinza) para baixo volume
    # Define threshold (ex: top 3 ou acima da média)
    cutoff = counts["Casos"].quantile(0.6) if len(counts) > 2 else 0
    bar_colors = ["#0a415a" if val >= cutoff else "#D1D5DB" for val in counts["Casos"]]

    fig = go.Figure(
        go.Bar(
            x=counts["Casos"],
            y=counts["Regional"],
            orientation="h",
            text=[f"{c} ({p})" for c, p in zip(counts["Casos"], counts["Percentual"])],
            textposition="outside",
            marker=dict(
                color=bar_colors,
                showscale=False,
            ),
            textfont=dict(color="black"), # Texto preto para legibilidade
            hovertemplate="<b>%{y}</b><br>Total: %{x} casos<extra></extra>",
        )
    )
    fig.update_layout(
        title_text="Ranking por Regional",
        title_x=0,
        xaxis_title="",
        yaxis_title="",
        margin=dict(t=50, b=30, l=10, r=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["neutral"]),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        autosize=True,
    )
    return fig


def bar_produtos(df: pd.DataFrame) -> go.Figure:
    """Gráfico de barras horizontais por Fábrica Relacionada (Vertical)."""
    if df.empty or "Produto" not in df.columns:
        return go.Figure()

    prod_series = df["Produto"]
    if isinstance(prod_series, pd.DataFrame):
        prod_series = prod_series.iloc[:, 0]

    counts = prod_series.value_counts().reset_index()
    counts.columns = ["Produto", "Casos"]
    counts = counts.sort_values("Casos", ascending=True)
    total = counts["Casos"].sum()
    counts["Percentual"] = (counts["Casos"] / total * 100).round(0).astype(int).astype(str) + "%"
    
    # Lógica: Verde apenas para as 3 primeiras (maiores), demais cinza.
    # O dataframe 'counts' está classificado em ordem crescente (ascending=True), então as maiores estão no fim.
    prod_colors = ["#D1D5DB"] * max(0, len(counts) - 3) + ["#0a415a"] * min(3, len(counts))

    fig = go.Figure(
        go.Bar(
            x=counts["Casos"],
            y=counts["Produto"],
            orientation="h",
            text=[f"{c} ({p})" for c, p in zip(counts["Casos"], counts["Percentual"])],
            textposition="outside",
            marker=dict(
                color=prod_colors,
                showscale=False,
            ),
            textfont=dict(color="black"), # Texto preto
            hovertemplate="<b>%{y}</b><br>Volume: %{x}<extra></extra>",
        )
    )
    fig.update_layout(
        title_text="Vertical por Produto",
        title_x=0,
        xaxis_title="",
        yaxis_title="",
        margin=dict(t=50, b=30, l=10, r=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=COLORS["neutral"]),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        autosize=True,
    )
    return fig


# ---------------------------------------------------------------------------
# Mapa do Brasil – Choropleth por Regional
# ---------------------------------------------------------------------------

# Mapeamento Regional -> estados ISO (simplificado)
REGIONAL_TO_STATES = {
    "São Paulo": ["SP"],
    "Sul": ["RS", "SC", "PR"],
    "Nordeste": ["BA", "SE", "AL", "PE", "PB", "RN", "CE", "PI", "MA"],
    "Norte": ["AM", "PA", "AC", "RO", "RR", "AP", "TO"],
    "Centro-Oeste": ["MT", "MS", "GO", "DF"],
    "Sudeste": ["RJ", "MG", "ES", "SP"],
    "Minas Gerais": ["MG"],
    "Rio de Janeiro": ["RJ"],
    "Espírito Santo": ["ES"],
    "Bahia": ["BA"],
    "Goiás": ["GO"],
}

GEOJSON_URL = (
    "https://raw.githubusercontent.com/codeforamerica/click_that_hood/"
    "master/public/data/brazil-states.geojson"
)


@st.cache_data(ttl=3600, show_spinner=False)
def _load_geojson():
    try:
        with urllib.request.urlopen(GEOJSON_URL, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def _expand_regional(df: pd.DataFrame) -> pd.DataFrame:
    """Expande cada Regional nos estados que ela representa."""
    rows = []
    # Garante que temos Series para as colunas principais
    reg_series = df["Regional"]
    if isinstance(reg_series, pd.DataFrame):
        reg_series = reg_series.iloc[:, 0]
    
    counts = reg_series.value_counts()
    total = counts.sum()

    # Para o groupby, pegamos apenas as colunas necessárias de forma explícita
    # Se houver duplicatas, iloc[:, 0] resolve para as colunas individuais
    evento_by_regional = (
        df.groupby(["Regional", "Evento"]).size().reset_index(name="n")
    )
    # Se o groupby falhar por duplicatas, tratamos aqui:
    if isinstance(evento_by_regional["Regional"], pd.DataFrame):
        # caso raro onde o groupby manteve colunas duplicadas
        evento_by_regional = evento_by_regional.loc[:, ~evento_by_regional.columns.duplicated()]
    for regional, qtd in counts.items():
        states = REGIONAL_TO_STATES.get(regional, [])
        breakdown = (
            evento_by_regional[evento_by_regional["Regional"] == regional]
            .set_index("Evento")["n"]
            .to_dict()
        )
        breakdown_str = "<br>".join(f"  {k}: {v}" for k, v in breakdown.items())
        for st_code in states:
            rows.append(
                {
                    "Estado": st_code,
                    "Regional": regional,
                    "Casos": qtd,
                    "Percentual": round(qtd / total * 100, 1),
                    "Breakdown": breakdown_str,
                }
            )
    return pd.DataFrame(rows)


def mapa_brasil(df: pd.DataFrame) -> go.Figure:
    if df.empty or "Regional" not in df.columns:
        return go.Figure()

    geojson = _load_geojson()
    if geojson is None:
        fig = go.Figure()
        fig.add_annotation(
            text="Visualização Geográfica indisponível",
            showarrow=False,
            font=dict(size=14, color=COLORS["danger"]),
        )
        return fig

    expanded = _expand_regional(df)
    if expanded.empty:
        return go.Figure()

    fig = px.choropleth(
        expanded,
        geojson=geojson,
        locations="Estado",
        featureidkey="properties.sigla",
        color="Casos",
        color_continuous_scale=["#0D1B2A", "#1B263B", "#0a415a", "#00E5FF", "#B900FF"], # Neon style
        hover_name="Regional",
        hover_data={"Casos": True, "Percentual": True, "Estado": False, "Breakdown": True},
        title="Concentração Regional Escala Neon",
        labels={"Casos": "Nº Casos", "Percentual": "%", "Breakdown": "Motivos"},
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(
        title_x=0,
        margin=dict(t=50, b=0, l=0, r=0),
        paper_bgcolor="rgba(0,0,0,0)",
        coloraxis_colorbar=dict(title="Volume"),
        font=dict(family="Inter, sans-serif", color=COLORS["neutral"]),
        autosize=True,
    )
    return fig


# ---------------------------------------------------------------------------
# Estilização de tabelas com pandas Styler
# ---------------------------------------------------------------------------

def style_table(df: pd.DataFrame) -> object:
    """Aplica colorização por HealthScore e retorna o Styler."""
    display_cols = [c for c in ["Cliente", "Regional", "Produto", "HealthScore", "Status"] if c in df.columns]
    sub = df[display_cols].copy()

    if "HealthScore" in sub.columns:
        sub["HealthScore"] = pd.to_numeric(sub["HealthScore"], errors="coerce").fillna(0)

    def _color_health(val):
        try:
            v = float(val)
            if v >= 90: return f"color: {COLORS['success']}; font-weight: bold;"
            if v >= 75: return f"color: {COLORS['warning']}; font-weight: bold;"
            if v >= 50: return f"color: {COLORS['danger']}; font-weight: bold;"
            return f"color: {COLORS['critical']}; font-weight: bold;"
        except: return ""

    styler = sub.style
    if "HealthScore" in sub.columns:
        styler = styler.format({"HealthScore": "{:.1f}%"})
        styler = styler.applymap(_color_health, subset=["HealthScore"])

    return styler
