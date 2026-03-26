"""
Módulo de processamento e transformação dos dados brutos do CRC.
Aplica limpeza, renomeações, derivações de colunas e filtros de semana.
"""

import re
import pandas as pd


# ---------------------------------------------------------------------------
# Mapeamento de colunas brutas -> nomes curtos
# ---------------------------------------------------------------------------
COLUMN_MAP = {
    "Carimbo de data/hora": "Carimbo",
    "Endereço de e-mail": "Email",
    "Código do Cliente": "Codigo",
    "Nome do Cliente ( 50 caracteres )": "Cliente",
    "Status atual (300 caracteres)": "Status",
    "Regional": "Regional",
    "Fábrica relacionada": "Produto",
    "Evento Motivador": "Evento",
    "Versão": "Versao",
    "Última Atualização": "Ultima_Atualizacao",
    "Total de Tickets Abertos no Período": "Total_Tickets",
    "Saldo": "Saldo",
    "Quantidade de Dúvidas Abertas no Período": "Qtd_Duvidas",
}

# Colunas que podem ter quebras de linha no cabeçalho original
FUZZY_COLUMNS = {
    "aging": "Aging",
    "sla 1": "SLA_1_Atendimento",
    "sla finalizado": "SLA_Finalizado",
    "satisfa": "Satisfacao",
    "healthscore": "HealthScore",
}

GLOSA_KEYWORDS = ["glosa"]

ESCALATION_EVENTS = ["escalation cliente"]
LENTIDAO_EVENTS = ["lentidão", "lentidao"]
TRIB_EVENTS = ["ref. tributária", "ref. tributaria", "onepass"]


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def _normalize_header(col: str) -> str:
    """Remove quebras de linha e espaços extras dos nomes de colunas."""
    return re.sub(r"\s+", " ", str(col).strip())


def _fuzzy_rename(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas com palavras-chave fuzzy (cabeçalhos com quebra de linha)."""
    rename = {}
    for col in df.columns:
        col_lower = col.lower()
        for key, new_name in FUZZY_COLUMNS.items():
            if key in col_lower and new_name not in df.columns and col not in rename.values():
                rename[col] = new_name
                break
    return df.rename(columns=rename)


def _apply_glosa(status_series: pd.Series) -> pd.Series:
    """Retorna Series 'Sim'/'Não' baseada em palavras-chave no Status."""
    pattern = "|".join(GLOSA_KEYWORDS)
    mask = status_series.astype(str).str.contains(pattern, case=False, na=False)
    return mask.map({True: "Sim", False: "Não"})


def _parse_healthscore(series: pd.Series) -> pd.Series:
    """Converte HealthScore para numérico, tratando vírgulas e texto."""
    return pd.to_numeric(
        series.astype(str).str.replace(",", ".", regex=False).str.extract(r"([\d.]+)")[0],
        errors="coerce",
    )


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def process(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe o DataFrame bruto e devolve o DataFrame tratado, com:
      - Colunas renomeadas
      - Colunas derivadas: Semana, Glosa_Aplicada
      - Tipos corretos
    """
    if df.empty:
        return df

    # 1. Normalizar cabeçalhos (remover quebras de linha)
    df.columns = [_normalize_header(c) for c in df.columns]

    # 2. Renomear colunas fixas
    df = df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in df.columns})

    # 3. Renomear colunas fuzzy (Aging, SLA, HealthScore…)
    df = _fuzzy_rename(df)

    # 3.1 Garantir nomes de colunas únicos (evita Erros de "label is not unique")
    cols = pd.Series(df.columns)
    for i, col in enumerate(cols):
        if (cols == col).sum() > 1:
            # Encontra as ocorrências e adiciona sufixo
            mask = cols == col
            cols[mask] = [f"{col}_{j}" if j > 0 else col for j in range(mask.sum())]
    df.columns = cols

    # 4. Parse de datas
    if "Carimbo" in df.columns:
        df["Carimbo"] = pd.to_datetime(df["Carimbo"], dayfirst=True, errors="coerce")
        df["Semana"] = df["Carimbo"].dt.isocalendar().week.astype("Int64")

    # 5. Glosa Aplicada
    if "Status" in df.columns:
        df["Glosa_Aplicada"] = _apply_glosa(df["Status"])
    else:
        df["Glosa_Aplicada"] = "Não"

    # 6. HealthScore numérico
    if "HealthScore" in df.columns:
        df["HealthScore"] = _parse_healthscore(df["HealthScore"])

    # 7. Limpeza de strings
    for col in ["Cliente", "Regional", "Produto", "Evento", "Status"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().replace("nan", "")

    # 8. Remover linhas sem evento motivador
    if "Evento" in df.columns:
        df = df[df["Evento"].notna() & (df["Evento"] != "")]

    df.reset_index(drop=True, inplace=True)
    return df


# ---------------------------------------------------------------------------
# Helpers de semana
# ---------------------------------------------------------------------------

def get_week_labels(df: pd.DataFrame):
    """Retorna (semana_atual, semana_anterior) como inteiros."""
    if "Semana" not in df.columns or df["Semana"].isna().all():
        return None, None
    semanas = sorted(df["Semana"].dropna().unique(), reverse=True)
    atual = int(semanas[0]) if len(semanas) >= 1 else None
    anterior = int(semanas[1]) if len(semanas) >= 2 else None
    return atual, anterior


def filter_by_week(df: pd.DataFrame, semana: int) -> pd.DataFrame:
    if semana is None or "Semana" not in df.columns:
        return df
    return df[df["Semana"] == semana].copy()


def filter_escalations(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["Evento"].str.lower().isin(ESCALATION_EVENTS)
    return df[mask]


def filter_lentidao(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["Evento"].str.lower().isin(LENTIDAO_EVENTS)
    return df[mask]


def filter_tributaria(df: pd.DataFrame) -> pd.DataFrame:
    pattern = "|".join(TRIB_EVENTS)
    mask = df["Evento"].str.contains(pattern, case=False, na=False)
    return df[mask]


def filter_lentidao_glosa(df: pd.DataFrame) -> pd.DataFrame:
    mask_lent = df["Evento"].str.lower().isin(LENTIDAO_EVENTS)
    mask_glosa = df.get("Glosa_Aplicada", pd.Series("Não", index=df.index)) == "Sim"
    return df[mask_lent | mask_glosa]
