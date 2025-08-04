import requests, numpy as np, time, hmac, hashlib, os
from datetime import datetime
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

# Load API dari .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Konfigurasi trading
TRADING_PAIR = "BNBUSDT"
RSI_PERIOD = 14
RSI_BUY_THRESHOLD = 30
TP_PERCENT = 0.03
SL_PERCENT = 0.02
DELAY_SECONDS = 1800  # 30 menit

# === Binance RSI Source Only ===
def get_price_binance(pair):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
        res = requests.get(url, timeout=10)
        return float(res.json()["price"])
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Gagal ambil harga Binance: {e}")
        return None

def get_binance_klines(symbol="BNBUSDT", interval="5m", limit=100):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
        res = requests.get(url, timeout=10)
        return [float(c[4]) for c in res.json()]
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Gagal ambil candle Binance: {e}")
        return []

def calculate_rsi(closes, period=14):
    if len(closes) < period + 1: return None
    deltas = np.diff(closes)
    gains = deltas[deltas > 0]
    losses = -deltas[deltas < 0]
    avg_gain = np.mean(gains[-period:]) if len(gains) >= period else 0
    avg_loss = np.mean(losses[-period:]) if len(losses) >= period else 0
    if avg_loss == 0: return 100
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def order_real(price):
    print(f"[{datetime.now()}] 📤 Kirim order LIMIT BUY...")
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
            "origQty": "0.1",
            "timestamp": timestamp
        }
        query = '&'.join([f"{k}={body[k]}" for k in body])
        sig = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
        headers = {"X-MBX-APIKEY": API_KEY}
        body["signature"] = sig
        res = requests.post(f"{base_url}{endpoint}", headers=headers, params=body)
        if res.status_code == 200:
            print(f"[{datetime.now()}] ✅ Order sukses: {res.json()}")
        else:
            print(f"[{datetime.now()}] ❌ Order gagal: {res.text}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error order: {e}")

def place_order(price, rsi):
    tp = price * (1 + TP_PERCENT)
    sl = price * (1 - SL_PERCENT)
    log = f"[{datetime.now()}] ✅ BUY @{price:.2f} | RSI: {rsi} → TP: {tp:.2f} | SL: {sl:.2f}"
    print(log)
    with open("log.txt", "a") as f:
        f.write(log + "\n")
    order_real(price)

def run_bot_loop():
    print(f"[{datetime.now()}] 🚀 Bot RSI mulai jalan background...")
    while True:
        print(f"[{datetime.now()}] 🔄 Mengecek kondisi pasar...")
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

# === Flask web + background bot ===
app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Bot RSI Aktif dan Berjalan."

# Mulai bot di background
Thread(target=run_bot_loop).start()

# Jalankan Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

