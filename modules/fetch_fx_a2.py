from datetime import datetime
import os
import requests
import pandas as pd

def run():
    print("=== Atualizando Dados de Câmbio (FX) ===")
    
    url = "https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL,GBP-BRL,CNY-BRL,JPY-BRL"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"Erro na API de Câmbio: Status {response.status_code}")
            return

        data = response.json()
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Estruturando a nova linha usando 'data' como chave de data
        new_row = {"data": today}

        # Extrair e exibir cada par
        for pair, details in data.items():
            symbol = details['code']        # ex: USD
            bid_val = float(details['bid']) # ex: 5.1272
            new_row[pair] = bid_val
            print(f"  └─ {symbol}/BRL: R$ {bid_val:.4f}")

        csv_file = "fx_dashboard.csv"
        
        if os.path.exists(csv_file):
            df = pd.read_csv(csv_file)
            
            # Identificar se a coluna de data é 'data' ou 'date' no CSV existente
            date_col = 'data' if 'data' in df.columns else ('date' if 'date' in df.columns else None)
            
            if date_col:
                # Remover registros do mesmo dia para evitar duplicatas
                df = df[df[date_col].astype(str) != today]
            
            # Adicionar a nova linha usando DataFrame
            df_new = pd.DataFrame([new_row])
            df = pd.concat([df, df_new], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

        df.to_csv(csv_file, index=False)
        print(f"-> Atualizado com sucesso em {csv_file} para {today}!\n")

    except Exception as e:
        print(f"Erro no módulo de Câmbio: {e}\n")

if __name__ == "__main__":
    run()