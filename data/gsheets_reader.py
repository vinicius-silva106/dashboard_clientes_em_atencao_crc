"""
Módulo de leitura do Google Sheets.
Usa pandas + URL de export CSV do Google Sheets (sem dependência de service account
para planilhas públicas/com acesso por link).
Fallback: leitura via gspread para planilhas privadas configuradas no secrets.toml.
"""

import urllib.parse
import pandas as pd
import streamlit as st

# Nome da aba na planilha
WORKSHEET_NAME = "Clientes em Atenção 2026"

# TTL de cache: 10 minutos
CACHE_TTL = 600


def _build_csv_url(spreadsheet_url: str, worksheet_name: str) -> str:
    """
    Constrói a URL de export CSV a partir da URL da planilha e do nome da aba.
    Usa o endpoint /gviz/tq que aceita o nome da aba sem precisar do gid numérico.
    """
    # Extrai o ID da planilha
    # Formato: https://docs.google.com/spreadsheets/d/<ID>/edit...
    parts = spreadsheet_url.split("/")
    try:
        d_index = parts.index("d")
        sheet_id = parts[d_index + 1].split("?")[0]
    except (ValueError, IndexError):
        raise ValueError(f"Não foi possível extrair o ID da planilha da URL: {spreadsheet_url}")

    # Codifica o nome da aba corretamente
    encoded_name = urllib.parse.quote(worksheet_name)

    # Endpoint gviz/tq exporta como CSV e aceita nomes de aba com acentos
    url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        f"/gviz/tq?tqx=out:csv&sheet={encoded_name}"
    )
    return url


@st.cache_data(ttl=CACHE_TTL, show_spinner="Carregando dados do Google Sheets…")
def load_raw_data(worksheet: str = WORKSHEET_NAME) -> pd.DataFrame:
    """
    Lê a planilha e devolve um DataFrame bruto.

    Pré-requisito (em .streamlit/secrets.toml):
        [connections.gsheets]
        spreadsheet = "https://docs.google.com/spreadsheets/d/<ID>/edit"
    """
    try:
        spreadsheet_url: str = st.secrets["connections"]["gsheets"]["spreadsheet"]
    except KeyError:
        st.error(
            "❌ Configuração ausente: adicione `[connections.gsheets] spreadsheet = ...` "
            "no arquivo `.streamlit/secrets.toml`."
        )
        return pd.DataFrame()

    try:
        csv_url = _build_csv_url(spreadsheet_url, worksheet)
        df = pd.read_csv(
            csv_url,
            header=0,
            dtype=str,          # lê tudo como string para evitar conversões erradas
            keep_default_na=False,
        )
        # Substitui strings vazias por NaN para facilitar o processamento
        df.replace("", pd.NA, inplace=True)
        # Remove linhas completamente vazias
        df.dropna(how="all", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    except Exception as exc:
        st.error(f"❌ Erro ao carregar dados do Google Sheets: {exc}")
        return pd.DataFrame()
