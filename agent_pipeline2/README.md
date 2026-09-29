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