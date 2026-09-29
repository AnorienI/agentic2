# 🤖 Agentic2 

(Agentic Currenflux)
An intelligent, agentic data pipeline for tracking macroeconomic indicators, central bank interest rates, exchange rates, and international trade balance (Comex). Built with **LangChain**, **Ollama**, **SQLite**, **Pandas**, and **OpenPyXL**.

---

## 🏗 Architecture & Tooling

Unlike the deterministic pipeline, Agentic CurrenFlux uses an autonomous agent loop orchestrated by LangChain. The agent inspects the database schema, handles data loading, and dynamically invokes custom tools to generate consolidated reports.

* **Agent LLM:** `gemma4:e4b` (for tool selection and execution)
* **SQL Coder LLM:** `qwen2.5-coder:3b` (for schema understanding & query toolkit)
* **Database:** SQLite (`currenflux.db`)
* **Export Engine:** `openpyxl` & `pandas`

---

## 🚀 Requirements & Setup

### 1. Prerequisites
* **Python:** 3.9+
* **Ollama:** Installed and running locally with the following models:
  ```bash
  ollama pull gemma4:e4b
  ollama pull qwen2.5-coder:3b

 ### 2. Dependencies

Install required Python packages:

pip install pandas requests openpyxl langchain langchain-community langchain-core langchain-ollama sqlite3

## 💻 Execution
Run the main agentic pipeline from the project directory:

python agent_run2.py

## What happens under the hood:

Data Ingestion: Calls fetch_and_load_currenflux_data to pull live FX rates, central bank interest rates, and trade data into SQLite (currenflux.db).

History Versioning: Automatically loads versioned historical files (cb_rates_*.csv, trade_data_*.csv) into SQLite tables.

Agent Orchestration: The agent receives the user prompt and selects the best tool for report generation.

Deterministic Consolidation: Executes generate_consolidated_spreadsheet to build a single .xlsx file with an Overview / Summary sheet plus detailed historical tabs.

## 📊 Output & Consolidated Report
The primary output is currenflux_consolidated.xlsx, which includes:

Resumo Consolidado (Overview Sheet): A unified snapshot table featuring:

Exchange Rates: USD/BRL, EUR/BRL, GBP/BRL, CNY/BRL, JPY/BRL

Central Bank Rates: Selic Target (BCB), Fed Funds Rate (FED), Deposit Facility Rate (ECB)

Comex Balance: Exports, Imports, and Trade Balance (in US$ Millions)

Detailed Sheets: Full individual historical tables (Fx Dashboard, Cb Rates, Trade Data).

Compatible with ONLYOFFICE, LibreOffice Calc, and Microsoft Excel.

## 🛠 Available Tools (tools.py)
fetch_and_load_currenflux_data(): Fetches fresh macroeconomic data and updates SQLite tables.

generate_consolidated_spreadsheet(): Generates the multi-sheet Excel report deterministically without manual SQL queries.

export_query_to_excel(query_sql): Executes custom SQL queries against currenflux.db and exports the result.

## 💡 Roadmap Ideas
[ ] Apply visual formatting (custom headers, column auto-fit, number formatting via openpyxl).

[ ] Add dynamic charts (line graphs for FX trends, bar charts for trade balance).

[ ] Expand enrichment data (inflation metrics, additional central banks).

[ ] Integrate automated Google Sheets export via Agent API.


---

### Principais alterações em relação ao README da versão determinística:

1. **Requisitos do Ollama:** Adiciona os dois modelos locais (`gemma4:e4b` e `qwen2.5-coder:3b`) e as novas dependências Python (`langchain`, `sqlite3`, `openpyxl`).
2. **Comando de execução:** Atualiza o comando para `python agent_run2.py`.
3. **Explicação da arquitetura:** Explica explicitamente como o agente opera com as ferramentas do `tools.py` e com o banco SQLite `currenflux.db`[cite: 1, 2].
4. **Descrição da Planilha Consolidada:** Destaque para a aba **Resumo Consolidado** com o suporte ao ONLYOFFICE no Linux[cite: 3, 4].