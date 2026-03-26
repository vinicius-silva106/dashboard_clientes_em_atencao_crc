# Dashboard Executivo – Clientes em Atenção (CRC)

Dashboard interativo em **Streamlit** que lê automaticamente a base de dados do Google Sheets e gera uma visualização executiva completa da semana, substituindo o esforço manual de criação de slides.

---

## Estrutura do Projeto

```
clientes_em_atencao_CRC/
│
├── app.py                          # Aplicação principal (Streamlit)
│
├── data/
│   ├── __init__.py
│   ├── gsheets_reader.py           # Conexão com o Google Sheets
│   └── processor.py                # Transformações e derivações pandas
│
├── viz/
│   ├── __init__.py
│   └── charts.py                   # Gráficos Plotly + estilização de tabelas
│
├── .streamlit/
│   └── secrets.toml.example        # Template de configuração (renomear e preencher)
│
├── requirements.txt
└── README.md
```

---

## Pré-requisitos

- Python 3.9 ou superior
- Conta Google com acesso à planilha **"Clientes em Atenção 2026"**

---

## 1. Instalação

```powershell
# 1. Abra o terminal na pasta do projeto
cd "C:\Users\vinic\Documents\clientes_em_atencao_CRC"

# 2. Crie e ative um ambiente virtual (recomendado)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instale as dependências
pip install -r requirements.txt
```

---

## 2. Configuração do Google Sheets

### Opção A – Planilha pública (mais simples)

1. Abra a planilha no Google Sheets
2. Vá em **Arquivo → Compartilhar → Publicar na web** e confirme
3. Copie a URL completa da planilha (ex: `https://docs.google.com/spreadsheets/d/ABC123/edit`)

### Opção B – Planilha privada (com Service Account)

1. No [Google Cloud Console](https://console.cloud.google.com/), crie uma **Service Account**
2. Ative a **Google Sheets API** e a **Google Drive API** no projeto
3. Baixe o JSON de credenciais da Service Account
4. Compartilhe a planilha com o e-mail da Service Account (papel de **Leitor**)

---

## 3. Configurar o arquivo de segredos

```powershell
# Copie o template e edite com seus dados
Copy-Item .\.streamlit\secrets.toml.example .\.streamlit\secrets.toml
```

Abra `.streamlit/secrets.toml` e preencha:

```toml
[connections.gsheets]
spreadsheet = "https://docs.google.com/spreadsheets/d/SEU_ID_AQUI/edit"
type        = "gsheets"

# Se for planilha privada, adicione os campos da Service Account abaixo
# (consulte o arquivo .example para os campos completos)
```

> ⚠️ **Nunca** suba o arquivo `secrets.toml` para o Git. Ele já está no `.gitignore`.

---

## 4. Executar o Dashboard

```powershell
streamlit run app.py
```

O dashboard abrirá automaticamente no navegador em `http://localhost:8501`.

---

## 5. Funcionalidades

| Seção | Descrição |
|---|---|
| **KPIs** | Total de casos, variação semanal, Escalations, Lentidão, Reforma Tributária, Glosas |
| **Análise Executiva** | Texto gerado automaticamente com panorama, risco e foco regional |
| **Donut Chart** | Distribuição por Evento Motivador |
| **Barras Horizontais** | Ranking de casos por Regional |
| **Mapa do Brasil** | Choropleth interativo com hover de eventos por estado |
| **Tabela Escalations** | Lista filtrada com alerta automático se > 30% do total |
| **Tabela Tributária** | Lista de Reforma Tributária / OnePass com gatilho de força-tarefa |
| **Tabela Lentidão/Glosa** | Casos combinados com formatação condicional |
| **Próximos Passos** | Recomendações geradas por regras lógicas |

---

## 6. Filtros disponíveis (Sidebar)

- **Regional** — filtra por regional de atendimento
- **Produto** — filtra por fábrica/produto relacionado
- **Evento Motivador** — filtra por tipo de evento

---

## 7. Lógica de Derivação de Colunas

| Coluna | Lógica |
|---|---|
| `Semana` | Número ISO da semana extraído de `Carimbo de data/hora` |
| `Glosa_Aplicada` | `"Sim"` se `Status` contém: *glosa, multa, financeiro, faturamento* |

---

## 8. Atualizar dados

Os dados são cacheados por **10 minutos**. Para forçar atualização imediata, clique em **🔄 Recarregar dados** na sidebar.
