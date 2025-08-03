import requests
import numpy as np
import time
import hmac
import hashlib
import os
import threading
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask

# === Load API Key dari .env ===
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# === Konfigurasi Bot ===
TRADING_PAIR = "BNBUSDT"
RSI_PERIOD = 14
RSI_BUY_THRESHOLD = 30
TP_PERCENT = 0.03
SL_PERCENT = 0.02
DELAY_SECONDS = 1800  # setiap 30 menit

# === Flask dummy agar Koyeb Web Service tetap hidup ===
app = Flask(__name__)
@app.route("/")
def index():
    return "Bot RSI Tokocrypto aktif!", 200

# === Ambil harga real-time dari Binance ===
def get_price_binance(pair):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
        response = requests.get(url, timeout=10)
        data = response.json()
        return float(data["price"])
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Gagal ambil harga Binance: {e}")
        return None

# === Ambil data candle dari Binance (untuk RSI) ===
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

# === Hitung RSI ===
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

# === Kirim order real ke Tokocrypto ===
def order_real(price):
    print(f"[{datetime.now()}] 📤 Mengirim order beli nyata...")

    try:
        base_url = "https://api.tokocrypto.com"
        endpoint = "/open/v1/orders"
        timestamp = str(int(time.time() * 1000))

        body = {
            "symbol": TRADING_PAIR,
            "side": "BUY",
            "type": "LIMIT",
            "timeInForce": "GTC",
            "price": f"{price:.2f}",
            "origQty": "0.1",  # Sesuaikan jumlah
            "timestamp": timestamp
        }

        query_string = '&'.join([f"{key}={body[key]}" for key in body])
        signature = hmac.new(API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

        headers = {
            "X-MBX-APIKEY": API_KEY
        }

        body["signature"] = signature
        response = requests.post(f"{base_url}{endpoint}", headers=headers, params=body)

        if response.status_code == 200:
            print(f"[{datetime.now()}] ✅ Order berhasil: {response.json()}")
        else:
            print(f"[{datetime.now()}] ❌ Order gagal: {response.text}")

    except Exception as e:
        print(f"[{datetime.now()}] ❌ Exception saat kirim order: {e}")

# === Simulasi atau Real Order ===
def place_order(price, rsi):
    tp = price * (1 + TP_PERCENT)
    sl = price * (1 - SL_PERCENT)
    log = f"[{datetime.now()}] ✅ BUY @ {price:.2f} | RSI: {rsi} → TP: {tp:.2f} | SL: {sl:.2f}"
    print(log)
    with open("log.txt", "a") as f:
        f.write(log + "\n")
    order_real(price)

# === Bot utama ===
def run_bot():
    while True:
        print(f"\n[{datetime.now()}] 🔄 Mengecek kondisi pasar...")
        price = get_price_binance(TRADING_PAIR)
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

        time.sleep(DELAY_SECONDS)

# === Mulai bot di thread terpisah agar Flask tetap hidup ===
if __name__ == "__main__":
    print(f"[{datetime.now()}] 🚀 Bot RSI dimulai di background...")
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Menjaga Koyeb instance tetap hidup
    app.run(host="0.0.0.0", port=8080)
