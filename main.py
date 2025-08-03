import requests, time, numpy as np
from datetime import datetime

TRADING_PAIR = "BNBUSDT"
TP_PERCENT = 0.03
SL_PERCENT = 0.02
RSI_PERIOD = 14
RSI_BUY_THRESHOLD = 30
DELAY_SECONDS = 300

def get_price_toko(pair):
    try:
        url = f"https://api.tokocrypto.com/open/v1/market/ticker/price?symbol={pair}"
        response = requests.get(url)
        return float(response.json()["data"]["price"])
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Gagal ambil harga Tokocrypto: {e}")
        return None

def get_binance_klines(symbol="BNBUSDT", interval="5m", limit=100):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        response = requests.get(url)
        return [float(k[4]) for k in response.json()]
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Gagal ambil candle Binance: {e}")
        return []

def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    deltas = np.diff(closes)
    gain = deltas[deltas > 0].sum() / period
    loss = -deltas[deltas < 0].sum() / period
    if loss == 0: return 100
    rs = gain / loss
    return round(100 - (100 / (1 + rs)), 2)

def should_buy(price, rsi):
    return rsi is not None and rsi < RSI_BUY_THRESHOLD

def place_order(price, rsi):
    tp = price * (1 + TP_PERCENT)
    sl = price * (1 - SL_PERCENT)
    log = f"[{datetime.now()}] ✅ BUY @ {price:.2f} | RSI: {rsi} → TP: {tp:.2f} | SL: {sl:.2f}"
    print(log)
    with open("log.txt", "a") as f:
        f.write(log + "\n")

def run_bot():
    print(f"\n[{datetime.now()}] 🔄 Mengecek pasar...")
    price = get_price_toko(TRADING_PAIR)
    closes = get_binance_klines(TRADING_PAIR)
    rsi = calculate_rsi(closes, RSI_PERIOD)
    if price and rsi:
        print(f"[{datetime.now()}] Harga: {price:.2f} | RSI: {rsi}")
        if should_buy(price, rsi):
            place_order(price, rsi)
        else:
            print(f"[{datetime.now()}] ⏳ Belum ada sinyal beli.")
    else:
        print(f"[{datetime.now()}] ⚠️ Data tidak lengkap.")

print(f"[{datetime.now()}] 🚀 Bot dimulai...")
while True:
    run_bot()
    time.sleep(DELAY_SECONDS)