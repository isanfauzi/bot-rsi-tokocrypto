from flask import Flask
import threading
from main import start_bot

app = Flask(__name__)

@app.route('/')
def index():
    return "🤖 Bot RSI Tokocrypto sedang berjalan di Koyeb!"

# Mulai bot RSI di thread terpisah
threading.Thread(target=start_bot, daemon=True).start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)