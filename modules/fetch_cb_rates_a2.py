import pandas as pd
import requests
import os
import glob
from datetime import datetime
from io import StringIO

# ==============================================================================
# 1. DICIONÁRIO DE CONFIGURAÇÃO DOS BANCOS CENTRAIS
# ==============================================================================
CENTRAL_BANKS_CONFIG = {
      "BCB": {
        "country": "BRL",
        "rate_name": "Selic Target",
        "type": "bcb_api",
        "url": "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
    },
    "FED": {
        "country": "USD",
        "rate_name": "Fed Funds Rate",
        "type": "fred_csv",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS"
    },
    "ECB": {
        "country": "EUR",
        "rate_name": "Deposit Facility Rate",
        "type": "fred_csv",
        "url": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=ECBDFR"
    },
        "BOJ": {
        "country": "JPN",
        "rate_name": "Policy Rate",
        "type": "bis_csv",
        "area": "JP"
    },
    "PBOC": {
        "country": "CHN",
        "rate_name": "7D Reverse Repo",
        "type": "bis_csv",
        "area": "CN"
    },
    "RBI": {
        "country": "IND",
        "rate_name": "Repo Rate",
        "type": "bis_csv",
        "area": "IN"
    }
}

# ==============================================================================
# 2. FUNÇÃO GENÉRICA DE COLETA
# ==============================================================================
def fetch_central_bank_rate(bank_code: str, config: dict):
    """Busca a taxa de juros com tratamento específico para fontes ativas."""
    try:
        if config["type"] == "bcb_api":
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            res = requests.get(config["url"], headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                return float(data[0]['valor']), data[0]['data']
            raise Exception(f"HTTP {res.status_code}")

        elif config["type"] == "bcb_csv":
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            }
            res = requests.get(config["url"], headers=headers, timeout=10)
            if res.status_code == 200:
                # Lê o CSV retornado usando ponto e vírgula como separador
                df = pd.read_csv(StringIO(res.text), sep=";")
                df_valid = df.dropna().tail(1)
                if not df_valid.empty:
                    date_val = str(df_valid.iloc[0, 0])
                    # Converte a vírgula do decimal brasileiro para ponto
                    rate_val = float(str(df_valid.iloc[0, 1]).replace(",", "."))
                    return rate_val, date_val
                
        elif config["type"] == "fred_csv":
            df = pd.read_csv(config["url"])
            df_valid = df.dropna().tail(1)
            if not df_valid.empty:
                date_val = str(df_valid.iloc[0, 0])
                rate_val = float(df_valid.iloc[0, 1])
                return rate_val, date_val

        elif config["type"] == "direct_override":
            # Para países cujas séries no FRED foram descontinuadas (ex: BOJ / PBOC)
            res = requests.get(config["url"], timeout=10)
            if res.status_code == 200:
                data = res.json()
                return data["rate"], data["date"]

        elif config["type"] == "bis_csv":
            url = (f"https://stats.bis.org/api/v1/data/WS_CBPOL/D.{config['area']}"
            "?format=csv&lastNObservations=1")
            res = requests.get(url, timeout=15)
            if res.status_code == 200:
                df = pd.read_csv(StringIO(res.text))
                return float(df["OBS_VALUE"].iloc[-1]), str(df["TIME_PERIOD"].iloc[-1])

    except Exception as e:
        print(f"Erro ao buscar dados de {bank_code}: {e}")
        
        # Fallback de resiliência: carrega o último registro válido de um arquivo anterior
        existing_files = sorted(glob.glob("./cb_rates_*.csv"))
        if existing_files:
            try:
                last_df = pd.read_csv(existing_files[-1])
                match = last_df[last_df["central_bank"] == bank_code]
                if not match.empty:
                    last_row = match.iloc[-1]
                    print(f"-> Usando valor armazenado anterior para {bank_code}: {last_row['rate_value']}% ({last_row['effective_date']})")
                    return float(last_row['rate_value']), str(last_row['effective_date'])
            except Exception:
                pass

        return None, None
    
    return None, None
# ===================================================================
# 3. FUNÇÃO PRINCIPAL DE EXECUÇÃO DO MÓDULO (run)
# ==============================================================================
def run():
    print("\n=== Atualizando Dados dos Bancos Centrais ===")
    records = []
    today_str = datetime.now().strftime("%Y-%m-%d")

    for bank_code, config in CENTRAL_BANKS_CONFIG.items():
        rate, date_val = fetch_central_bank_rate(bank_code, config)
        if rate is not None:
            print(f"[{bank_code} - {config['country']}] {config['rate_name']}: {rate}% (Data: {date_val})")
            records.append({
                "date_updated": today_str,
                "central_bank": bank_code,
                "country": config["country"],
                "rate_name": config["rate_name"],
                "rate_value": rate,
                "effective_date": date_val
            })

    if records:
        df = pd.DataFrame(records)
        
        # Gera o próximo nome de arquivo versionado (ex: cb_rates_001.csv, cb_rates_002.csv)
        existing = glob.glob("./cb_rates_*.csv")
        numbers = [int(os.path.splitext(f)[0].split("_")[-1]) for f in existing if os.path.splitext(f)[0].split("_")[-1].isdigit()]
        next_num = max(numbers) + 1 if numbers else 1
        output_file = f"./cb_rates_{next_num:03d}.csv"
        
        df.to_csv(output_file, index=False)
        print(f"-> Salvo com sucesso em {output_file}")
    else:
        print("-> Nenhum dado pôde ser coletado nesta execução.")

if __name__ == "__main__":
    run()