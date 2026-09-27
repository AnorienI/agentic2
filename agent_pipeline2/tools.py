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
    """Executa uma consulta SQL no CurrenFlux e exporta em Excel.
    Se file_path não for informado, usa 'currenflux_report.xlsx' como padrão."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query_sql, conn)
    conn.close()

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="CurrenFlux", index=False)

    return f"Relatório exportado em: {file_path}"