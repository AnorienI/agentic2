import sqlite3
import sys
import os
import glob
import pandas as pd
from langchain_core.tools import tool

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from modules import fetch_fx_a2, fetch_cb_rates_a2, fetch_trade_a2

DB_PATH = "currenflux.db"

def _load_versioned_history(base_name: str) -> pd.DataFrame:
    files = sorted(glob.glob(f"{base_name}_*.csv"))
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True) if files else pd.DataFrame()

@tool
def fetch_and_load_currenflux_data() -> str:
    """Coleta dados reais de câmbio, taxas de Bancos Centrais e Comex,
    e carrega o histórico completo nas tabelas fx_dashboard, cb_rates e trade_data no SQLite."""
    results = []
    conn = sqlite3.connect(DB_PATH)

    fetch_fx_a2.run()
    fx_df = pd.read_csv("fx_dashboard.csv")
    fx_df.to_sql("fx_dashboard", conn, if_exists="replace", index=False)
    results.append(f"fx_dashboard: {len(fx_df)} linha(s)")

    fetch_cb_rates_a2.run()
    cb_df = _load_versioned_history("cb_rates")
    if not cb_df.empty:
        cb_df.to_sql("cb_rates", conn, if_exists="replace", index=False)
        results.append(f"cb_rates: {len(cb_df)} linha(s) (histórico completo)")

    fetch_trade_a2.run()
    trade_df = _load_versioned_history("trade_data")
    if not trade_df.empty:
        trade_df.to_sql("trade_data", conn, if_exists="replace", index=False)
        results.append(f"trade_data: {len(trade_df)} linha(s) (histórico completo)")

    conn.close()
    return "Dados atualizados: " + " | ".join(results)

@tool
def export_query_to_excel(query_sql: str, file_path: str = "currenflux_report.xlsx") -> str:
    """Executa uma consulta SQL no CurrenFlux e exporta em Excel."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query_sql, conn)
    conn.close()

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="CurrenFlux", index=False)

    return f"Relatório exportado em: {file_path}"

@tool
def generate_consolidated_spreadsheet(file_path: str = "currenflux_consolidated.xlsx") -> str:
    """USE ESTA FERRAMENTA para gerar o relatório consolidado em Excel. 
    NÃO pergunte o caminho ao usuário; use 'currenflux_consolidated.xlsx' como padrão no diretório atual."""
    conn = sqlite3.connect(DB_PATH)
    
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        # 1. Carrega dados mais recentes de cada fonte
        fx_df = pd.read_sql_query("SELECT * FROM fx_dashboard ORDER BY data DESC LIMIT 1", conn) if os.path.exists("fx_dashboard.csv") else pd.DataFrame()
        cb_df = pd.read_sql_query("SELECT * FROM cb_rates", conn)
        trade_df = pd.read_sql_query("SELECT * FROM trade_data ORDER BY date_updated DESC LIMIT 1", conn)

        # 2. Monta a lista do Resumo Consolidado
        summary_rows = []

        # Câmbio
        if not fx_df.empty:
            for col in ["USDBRL", "EURBRL", "GBPBRL", "CNYBRL", "JPYBRL"]:
                if col in fx_df.columns:
                    summary_rows.append({
                        "Categoria": "Taxa de Câmbio",
                        "Indicador / Par": col,
                        "Valor": fx_df[col].iloc[0],
                        "Data / Referência": fx_df["data"].iloc[0] if "data" in fx_df.columns else ""
                    })

        # Taxas de Juros dos Bancos Centrais
        if not cb_df.empty:
            latest_cb = cb_df.sort_values("date_updated").groupby("central_bank").last().reset_index()
            for _, row in latest_cb.iterrows():
                summary_rows.append({
                    "Categoria": f"Juros ({row.get('central_bank', '')})",
                    "Indicador / Par": row.get("rate_name", ""),
                    "Valor": f"{row.get('rate_value', '')}%",
                    "Data / Referência": row.get("effective_date", row.get("date_updated", ""))
                })

        # Comércio Exterior
        if not trade_df.empty:
            latest_trade = trade_df.iloc[0]
            ref_period = latest_trade.get("reference_period", "")
            summary_rows.append({
                "Categoria": "Comex (Brasil)",
                "Indicador / Par": "Exportações (US$ Mi)",
                "Valor": latest_trade.get("exports_usd_millions", ""),
                "Data / Referência": ref_period
            })
            summary_rows.append({
                "Categoria": "Comex (Brasil)",
                "Indicador / Par": "Importações (US$ Mi)",
                "Valor": latest_trade.get("imports_usd_millions", ""),
                "Data / Referência": ref_period
            })
            summary_rows.append({
                "Categoria": "Comex (Brasil)",
                "Indicador / Par": "Saldo Comercial (US$ Mi)",
                "Valor": latest_trade.get("trade_balance_usd_millions", ""),
                "Data / Referência": ref_period
            })

        # Escreve a aba principal "Resumo Consolidado"
        if summary_rows:
            summary_df = pd.DataFrame(summary_rows)
            summary_df.to_excel(writer, sheet_name="Resumo Consolidado", index=False)

        # 3. Exporta as abas detalhadas de cada tabela do banco
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
        for table_name in tables:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            sheet_title = table_name.replace("_", " ").title()[:31]
            df.to_excel(writer, sheet_name=sheet_title, index=False)
            
    conn.close()
    return f"Relatório consolidado gerado com sucesso em: {file_path}"