import requests
import numpy as np
import time
from datetime import datetime
from flask import Flask, jsonify

import threading

# ==== Konfigurasi ====
TRADING_PAIR = "BNBUSDT"
RSI_PERIOD = 14
RSI_BUY_THRESHOLD = 30
TP_PERCENT = 0.03
SL_PERCENT = 0.02

app = Flask(__name__)

# ==== Ambil harga dari Tokocrypto ====
def get_price_toko(pair):
    try:
        url = f"https://api.tokocrypto.com/open/v1/market/ticker/price?symbol={pair}"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data["data"]["price"])
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Gagal ambil harga Toko: {e}")
        return None

# ==== Ambil data candle dari Binance ====
def get_binance_klines(symbol="BNBUSDT", interval="5m", limit=100):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        response = requests.get(url, timeout=10)
        data = response.json()
        closes = [float(candle[4]) for candle in data]
        return closes
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Gagal ambil kline Binance: {e}")
        return []

# ==== Hitung RSI ====
def calculate_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    deltas = np.diff(closes)
    gains = deltas[deltas > 0]
    losses = -deltas[deltas < 0]
    avg_gain = np.mean(gains[-period:]) if len(gains) >= period else 0
    avg_loss = np.mean(losses[-period:]) if len(losses) >= period else 0
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

# ==== Simulasi order beli ====
def place_order(price, rsi):
    tp = price * (1 + TP_PERCENT)
    sl = price * (1 - SL_PERCENT)
    log = f"[{datetime.now()}] ✅ BUY @ {price:.2f} | RSI: {rsi} → TP: {tp:.2f} | SL: {sl:.2f}"
    print(log)
    with open("log.txt", "a") as f:
        f.write(log + "\n")

# ==== Bot Utama ====
def run_bot():
    print(f"[{datetime.now()}] 🔄 Mengecek kondisi pasar...")
    price = get_price_toko(TRADING_PAIR)
    closes = get_binance_klines(TRADING_PAIR, "5m", 100)
    rsi = calculate_rsi(closes, RSI_PERIOD)

    if price and rsi:
        print(f"[{datetime.now()}] Harga: {price:.2f} | RSI: {rsi}")
        if rsi < RSI_BUY_THRESHOLD:
            place_order(price, rsi)
        else:
            print(f"[{datetime.now()}] ⏳ Belum ada sinyal beli (RSI > {RSI_BUY_THRESHOLD})")
    else:
        print(f"[{datetime.now()}] ⚠️ Data tidak lengkap.")

# ==== Endpoint trigger bot ====
@app.route("/run")
def trigger_bot():
    threading.Thread(target=run_bot).start()
    return jsonify({"status": "Bot dijalankan", "time": str(datetime.now())})

# ==== Root: jika buka langsung di browser ====
@app.route("/")
def homepage():
    return f"""
    <h2>🚀 Bot RSI Tokocrypto</h2>
    <p>Status: Siap dijalankan</p>
    <p><a href="/run">Jalankan Bot Sekarang</a></p>
    <p><i>{datetime.now()}</i></p>
    """

# ==== Jalankan Web Service ====
if __name__ == "__main__":
    print(f"[{datetime.now()}] 🌐 Web Service aktif...")
    app.run(host="0.0.0.0", port=8080)
