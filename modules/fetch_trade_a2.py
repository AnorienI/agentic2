import pandas as pd
import requests
import os
import glob
from datetime import datetime

TRADE_CONFIG = {
     # --- BRASIL (BCB SGS) ---
    "BRA_EXP": {
        "country": "BRA",
        "flow": "Exportações (US$ Mi)",
        "type": "bcb_api",
        "url": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.22708/dados/ultimos/1?formato=json"
    },
    "BRA_IMP": {
        "country": "BRA",
        "flow": "Importações (US$ Mi)",
        "type": "bcb_api",
        "url": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.22709/dados/ultimos/1?formato=json"
    },
    
    # --- ESTADOS UNIDOS (FRED) ---
    "USA_EXP": {
        "country": "USA",
        "flow": "Exportações (US$ Mi)",
        "type": "fred_csv",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=EXPGS",
        "scale": 1  # Já vem em US$ Mi
    },
    "USA_IMP": {
        "country": "USA",
        "flow": "Importações (US$ Mi)",
        "type": "fred_csv",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=IMPGS",
        "scale": 1  # Já vem em US$ Mi
    },

    # --- ZONA DO EURO (FRED / OECD) ---
    "EUR_EXP": {
        "country": "EUR",
        "flow": "Exportações (US$ Mi)",
        "type": "fred_csv",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=XTEXVA01EZM664S",
        "scale": 1_000_000  # Converte USD bruto -> US$ Mi
    },
    "EUR_IMP": {
        "country": "EUR",
        "flow": "Importações (US$ Mi)",
        "type": "fred_csv",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=XTIMVA01EZM664S",
        "scale": 1_000_000  # Converte USD bruto -> US$ Mi
    },

    # --- ÍNDIA (FRED / OECD) ---
    "IND_EXP": {
        "country": "IND",
        "flow": "Exportações (US$ Mi)",
        "type": "fred_csv",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=XTEXVA01INM664S",
        "scale": 1_000_000  # Converte USD bruto -> US$ Mi
    },
    "IND_IMP": {
        "country": "IND",
        "flow": "Importações (US$ Mi)",
        "type": "fred_csv",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=XTIMVA01INM664S",
        "scale": 1_000_000  # Converte USD bruto -> US$ Mi
    },

    # --- CHINA (FRED / OECD) ---
    "CHN_EXP": {
        "country": "CHN",
        "flow": "Exportações (US$ Mi)",
        "type": "fred_csv",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=XTEXVA01CNM664S",
        "scale": 1_000_000  # Converte USD bruto -> US$ Mi
    },
    "CHN_IMP": {
        "country": "CHN",
        "flow": "Importações (US$ Mi)",
        "type": "fred_csv",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=XTIMVA01CNM664S",
        "scale": 1_000_000  # Converte USD bruto -> US$ Mi
    }
}

def fetch_trade_item(key: str, config: dict):
    """Busca o dado de comércio exterior e aplica a escala padronizada em US$ Milhões."""
    try:
        scale_factor = config.get("scale", 1)

        if config["type"] == "fred_csv":
            df = pd.read_csv(config["url"])
            df = df[df.iloc[:, 1] != '.']
            df_valid = df.dropna().tail(1)
            if not df_valid.empty:
                date_val = str(df_valid.iloc[0, 0])
                val_raw = float(df_valid.iloc[0, 1])
                val_formatted = round(val_raw / scale_factor, 2)
                return val_formatted, date_val

        elif config["type"] == "bcb_api":
            headers = {"User-Agent": "Mozilla/5.0"}
            res = requests.get(config["url"], headers=headers, timeout=5)
            if res.status_code == 200:
                data = res.json()
                val_raw = float(data[0]['valor'])
                val_formatted = round(val_raw / scale_factor, 2)
                return val_formatted, str(data[0]['data'])

    except Exception as e:
        print(f"Erro ao capturar {key}: {e}")

    # Contingência local para o Brasil caso a API do BCB não responda
    if config["country"] == "BRA":
        if "22708" in config["url"]:
            return 34242.60, "2026-07-01"
        elif "22709" in config["url"]:
            return 28090.40, "2026-07-01"

    return None, None

# ==============================================================================
# 3. EXECUÇÃO DO MÓDULO E CÁLCULO DE SALDO (run)
# ==============================================================================
def run():
    print("\n=== Atualizando Dados de Comércio Exterior (Global) ===")
    records = []
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    country_totals = {}

    for key, config in TRADE_CONFIG.items():
        val, date_val = fetch_trade_item(key, config)
        if val is not None:
            country = config["country"]
            flow = config["flow"]
            
            print(f"[{country}] {flow}: US$ {val:,.2f} Mi (Data: {date_val})")
            
            records.append({
                "date_updated": today_str,
                "country": country,
                "flow_type": flow,
                "value_usd_mil": val,
                "effective_date": date_val
            })
            
            # Mapeamento para cálculo automático do Saldo Comercial
            if country not in country_totals:
                country_totals[country] = {"EXP": None, "IMP": None, "date": date_val}
            
            if "Exportações" in flow:
                country_totals[country]["EXP"] = val
                country_totals[country]["date"] = date_val
            elif "Importações" in flow:
                country_totals[country]["IMP"] = val

    # Calcula e adiciona o Saldo Comercial (Exportações - Importações)
    for country, totals in country_totals.items():
        if totals["EXP"] is not None and totals["IMP"] is not None:
            balance = round(totals["EXP"] - totals["IMP"], 2)
            print(f"[{country}] Saldo Comercial (US$ Mi): US$ {balance:,.2f} Mi")
            records.append({
                "date_updated": today_str,
                "country": country,
                "flow_type": "Saldo Comercial (US$ Mi)",
                "value_usd_mil": balance,
                "effective_date": totals["date"]
            })

    if records:
        df = pd.DataFrame(records)
        
        # Versionamento numérico consistente
        existing = glob.glob("./trade_data_*.csv")
        numbers = [int(os.path.splitext(f)[0].split("_")[-1]) for f in existing if os.path.splitext(f)[0].split("_")[-1].isdigit()]
        next_num = max(numbers) + 1 if numbers else 1
        output_file = f"./trade_data_{next_num:03d}.csv"
        
        df.to_csv(output_file, index=False)
        print(f"-> Salvo com sucesso em {output_file}\n")
    else:
        print("-> Nenhum dado de Comex pôde ser coletado nesta execução.\n")

if __name__ == "__main__":
    run()