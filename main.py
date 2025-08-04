import requests
import time
import hmac
import hashlib
import os
from datetime import datetime
from dotenv import load_dotenv

# === Load API Key dari .env ===
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# === Konfigurasi ===
TRADING_PAIR = "BNBUSDT"
TP_PERCENT = 0.03   # 3% Take Profit
SL_PERCENT = 0.02   # 2% Stop Loss

# === Ambil 1 candle terakhir dari Binance (interval 1 jam) ===
def get_last_candle(symbol="BNBUSDT"):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        return open_price, close_price
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Gagal ambil candle Binance: {e}")
        return None, None

# === Kirim real order ke Tokocrypto ===
def send_order(side, price):
    print(f"[{datetime.now()}] 📤 Kirim order {side} ke Tokocrypto...")

    try:
        base_url = "https://api.tokocrypto.com"
        endpoint = "/open/v1/orders"
        timestamp = str(int(time.time() * 1000))

        body = {
            "symbol": TRADING_PAIR,
            "side": side,
            "type": "LIMIT",
            "timeInForce": "GTC",
            "price": f"{price:.2f}",
            "origQty": "0.1",  # Ganti sesuai saldo
            "timestamp": timestamp
        }

        query_string = '&'.join([f"{key}={body[key]}" for key in body])
        signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()

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

# === Bot utama ===
def run_bot():
    print(f"\n[{datetime.now()}] 🔍 Mengecek candle 1 jam terakhir...")

    open_price, close_price = get_last_candle(TRADING_PAIR)

    if open_price and close_price:
        print(f"[{datetime.now()}] 🕐 Open: {open_price:.2f} | Close: {close_price:.2f}")

        if close_price > open_price:
            trend = "UP"
            side = "BUY"
            entry = close_price
            tp = entry * (1 + TP_PERCENT)
            sl = entry * (1 - SL_PERCENT)
        elif close_price < open_price:
            trend = "DOWN"
            side = "SELL"
            entry = close_price
            tp = entry * (1 - TP_PERCENT)
            sl = entry * (1 + SL_PERCENT)
        else:
            print(f"[{datetime.now()}] ⏳ Tidak ada pergerakan candle.")
            return

        print(f"[{datetime.now()}] 📈 Trend: {trend} → {side} @ {entry:.2f} | TP: {tp:.2f} | SL: {sl:.2f}")
        send_order(side, entry)

    else:
        print(f"[{datetime.now()}] ⚠️ Data candle tidak tersedia.")

# === Eksekusi Sekali Saja ===
if __name__ == "__main__":
    run_bot()
