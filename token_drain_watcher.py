"""
Token Drain Watcher
Инструмент для отслеживания аномального вывода токенов с кошелька или контракта.
"""

import requests
import time
import datetime

ETHERSCAN_API_KEY = "YourApiKeyToken"  # Вставь свой API-ключ от Etherscan
ADDRESS_TO_WATCH = "0x..."  # Адрес, за которым следим
CHECK_INTERVAL = 60  # В секундах

def get_token_transfers(address):
    url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&sort=desc&apikey={ETHERSCAN_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data.get("result", [])

def detect_large_outflows(transfers, threshold_usd=10000):
    alerts = []
    for tx in transfers:
        if tx["from"].lower() == ADDRESS_TO_WATCH.lower():
            token = tx["tokenSymbol"]
            value = int(tx["value"]) / (10 ** int(tx["tokenDecimal"]))
            usd_value = estimate_usd_value(token, value)
            if usd_value and usd_value > threshold_usd:
                alerts.append({
                    "time": datetime.datetime.utcfromtimestamp(int(tx["timeStamp"])),
                    "token": token,
                    "value": value,
                    "usd": usd_value,
                    "to": tx["to"]
                })
    return alerts

def estimate_usd_value(symbol, amount):
    try:
        res = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids={symbol.lower()}&vs_currencies=usd")
        price = res.json().get(symbol.lower(), {}).get("usd")
        if price:
            return price * amount
    except:
        pass
    return None

def monitor_wallet():
    print(f"Начинаем наблюдение за: {ADDRESS_TO_WATCH}")
    seen_tx = set()

    while True:
        transfers = get_token_transfers(ADDRESS_TO_WATCH)
        new_transfers = [tx for tx in transfers if tx["hash"] not in seen_tx]

        if new_transfers:
            for tx in new_transfers:
                seen_tx.add(tx["hash"])

            alerts = detect_large_outflows(new_transfers)
            for alert in alerts:
                print(f"🚨 Вывод > $10k: {alert['token']} {alert['value']} (~${int(alert['usd'])}) → {alert['to']} at {alert['time']}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_wallet()
