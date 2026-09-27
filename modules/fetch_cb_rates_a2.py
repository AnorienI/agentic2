import pandas as pd
import requests
from datetime import datetime
from modules.versioning import get_next_versioned_path

def get_selic_rate():
    """Busca a taxa Selic Meta atual (BCB - Brasil)"""
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
        data = res.json()
        return float(data[0]['valor']), data[0]['data']
    raise Exception(f"Erro BCB: {res.status_code}")

def get_fed_funds_rate():
    """Busca a taxa de juros do Federal Reserve (EUA - FED) via FRED"""
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=FEDFUNDS"
    df = pd.read_csv(url)
    df_valid = df.dropna().tail(1)
    
    date_val = str(df_valid.iloc[0, 0])   # 1ª coluna (Data)
    rate = float(df_valid.iloc[0, 1])      # 2ª coluna (Valor da Taxa)
    return rate, date_val

def get_ecb_rate():
    """Busca a taxa de juros do Banco Central Europeu (BCE) via FRED"""
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=ECBDFR"
    df = pd.read_csv(url)
    df_valid = df.dropna().tail(1)
    
    date_val = str(df_valid.iloc[0, 0])   # 1ª coluna (Data)
    rate = float(df_valid.iloc[0, 1])      # 2ª coluna (Valor da Taxa)
    return rate, date_val



def run():
    print("=== Atualizando Dados dos Bancos Centrais ===")
    records = []
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. Brasil (BCB)
    try:
        selic, date_selic = get_selic_rate()
        print(f"[BCB - Brasil] Selic Meta: {selic}% (Data: {date_selic})")
        records.append({
            "date_updated": today,
            "central_bank": "BCB",
            "country": "BRL",
            "rate_name": "Selic Target",
            "rate_value": selic,
            "effective_date": date_selic
        })
    except Exception as e:
        print(f"Erro ao buscar BCB: {e}")

    # 2. Estados Unidos (FED)
    try:
        fed_rate, date_fed = get_fed_funds_rate()
        print(f"[FED - EUA] Fed Funds Rate: {fed_rate}% (Data: {date_fed})")
        records.append({
            "date_updated": today,
            "central_bank": "FED",
            "country": "USD",
            "rate_name": "Fed Funds Rate",
            "rate_value": fed_rate,
            "effective_date": date_fed
        })
    except Exception as e:
        print(f"Erro ao buscar FED: {e}")

    # 3. Zona do Euro (BCE)
    try:
        ecb_rate, date_ecb = get_ecb_rate()
        print(f"[BCE - Eurozona] Deposit Facility Rate: {ecb_rate}% (Data: {date_ecb})")
        records.append({
            "date_updated": today,
            "central_bank": "ECB",
            "country": "EUR",
            "rate_name": "Deposit Facility Rate",
            "rate_value": ecb_rate,
            "effective_date": date_ecb
        })
    except Exception as e:
        print(f"Erro ao buscar BCE: {e}")

    # Salvar em CSV versionado  <-- only this final block changes
    if records:
        df = pd.DataFrame(records)
        out_path = get_next_versioned_path("cb_rates")
        df.to_csv(out_path, index=False)
        print(f"-> Salvo com sucesso em {out_path}\n")

if __name__ == "__main__":
    run()