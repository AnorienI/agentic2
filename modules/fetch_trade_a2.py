import pandas as pd
import requests
from datetime import datetime
from modules.versioning import get_next_versioned_path


def get_trade_balance():
    """
    Busca os dados consolidados da Balança Comercial do Brasil (BCB/SGS)
    - Série 22707: Exportações (FOB) - US$ milhões
    - Série 22708: Importações (FOB) - US$ milhões
    - Série 22709: Saldo da Balança Comercial - US$ milhões
    """
    url_exp = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.22708/dados/ultimos/1?formato=json"
    url_imp = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.22709/dados/ultimos/1?formato=json"
    url_bal = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.22707/dados/ultimos/1?formato=json"

    res_exp = requests.get(url_exp, timeout=10).json()[0]
    res_imp = requests.get(url_imp, timeout=10).json()[0]
    res_bal = requests.get(url_bal, timeout=10).json()[0]

    date_ref = res_exp['data']
    exports_usd_m = float(res_exp['valor'])
    imports_usd_m = float(res_imp['valor'])
    balance_usd_m = float(res_bal['valor'])

    return {
        "reference_period": date_ref,
        "exports_usd_m": exports_usd_m,
        "imports_usd_m": imports_usd_m,
        "balance_usd_m": balance_usd_m
    }


def run():
    print("=== Atualizando Dados de Comércio Exterior ===")
    today = datetime.now().strftime("%Y-%m-%d")

    try:
        trade_data = get_trade_balance()
        ref_date = trade_data["reference_period"]
        exp = trade_data["exports_usd_m"]
        imp = trade_data["imports_usd_m"]
        bal = trade_data["balance_usd_m"]

        calculated_balance = round(exp - imp, 1)

        if abs(calculated_balance - bal) > 0.2:
            raise ValueError(
                f"Inconsistent trade data: "
                f"Exports ({exp}) - Imports ({imp}) = {calculated_balance}, "
                f"but API balance is {bal}."
            )

        print(f"[Brasil - Comex] Mês de Referência: {ref_date}")
        print(f"  └─ Exportações: US$ {exp:,.2f} Mi")
        print(f"  └─ Importações: US$ {imp:,.2f} Mi")
        print(f"  └─ Saldo Comercial: US$ {bal:,.2f} Mi")

        df = pd.DataFrame([{
            "date_updated": today,
            "reference_period": ref_date,
            "country": "BRA",
            "exports_usd_millions": exp,
            "imports_usd_millions": imp,
            "trade_balance_usd_millions": bal
        }])

        out_path = get_next_versioned_path("trade_data")
        df.to_csv(out_path, index=False)
        print(f"-> Salvo com sucesso em {out_path}\n")

    except Exception as e:
        print(f"Erro no módulo de Comércio Exterior: {e}\n")


if __name__ == "__main__":
    run()