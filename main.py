import os
import random
import requests
import time
import threading
from bs4 import BeautifulSoup
from googlesearch import search
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask

# Web server kısmı (Railway aktif tutmak için)
app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot Aktif!'

# Telegram bot bilgileri
TG_BOT_TOKEN = 'BOT_TOKENİN'
TG_CHAT_ID = 'CHAT_IDİN'
LOG_FILE = 'checked_google.log'

def generate_user_agent():
    # Random User-Agent üret
    browsers = [...]
    return random.choice(browsers)

HEADERS = {...}
DORKS = [
    # Stripe ve Braintree dorkları (mevcut)
    '"pay with card" + "pricing"',
    '"membership" + "pay with card"',
    'inurl:/donate intext:"pay with card"',
    'inurl:/checkout intext:"stripe"',
    'intext:"stripe" intitle:"buy membership"',
    '"checkout" + "powered by stripe"',
    'intext:"stripe" intitle:"purchase"',
    'inurl:/payment intext:"powered by Stripe"',
    'intext:"credit card" intext:"Stripe Checkout"',

    # WooCommerce ve genel ödeme dorkları
    '"woocommerce" + "buy now"',
    '"donate now" + "credit card"',
    '"subscribe now" + "card"',
    '"Please provide the information as written on your credit card."',

    # Braintree (b3) dorkları
    'inurl:/checkout intext:"Braintree"',
    'inurl:/donate intext:"Braintree"',
    'intext:"Braintree" intitle:"payment"',
    'inurl:/checkout intext:"Braintree API"',
    'intext:"Braintree" intitle:"purchase"',
    'inurl:/payment intext:"powered by Braintree"',
    'intext:"hosted fields" intext:"braintree"',
    'intext:"Braintree Drop-in UI"',
    'intext:"Braintree SDK"',
    'intext:"nonce" intext:"braintree"',

    # Braintree Auth
    'inurl:/checkout intext:"Braintree Auth"',
    'intext:"Braintree Auth" intitle:"payment gateway"',
    'inurl:/payment intext:"Braintree Auth"',
    'intext:"Braintree Auth" intitle:"secure payment"',
    'inurl:/auth intext:"Braintree"',
    'intext:"Braintree authentication" intitle:"payment"',

    # Braintree 3D Secure
    'inurl:/checkout intext:"Braintree 3D Secure"',
    'intext:"Braintree 3D Secure" intitle:"payment"',
    'inurl:/checkout intext:"3D Secure Braintree"',
    'intext:"Braintree 3D Secure" intitle:"secure payment"',
    'inurl:/donate intext:"Braintree 3D Secure"',

    # Braintree Marketplace
    'inurl:/checkout intext:"Braintree Marketplace"',
    'intext:"Braintree Marketplace" intitle:"payment"',
    'inurl:/donate intext:"Braintree Marketplace"',
    'inurl:/checkout intext:"Braintree platform"',
    'intext:"Braintree platform" intitle:"payment"',

    # Diğer Braintree detayları
    'intext:"Braintree API" intitle:"payment gateway"',
    'inurl:/payment intext:"Braintree API"',
    'intext:"Braintree" intitle:"card details"',
    'intext:"Braintree" intitle:"credit card" intitle:"confirm"',
    'inurl:/checkout intext:"Braintree secure"',
    'inurl:/checkout intext:"Braintree token"',
    'intext:"client_token" intext:"braintree"',
    'intext:"payment_method_nonce" intext:"braintree"',

    # Payflow dorkları
    'intext:"Payflow" intitle:"payment"',
    'intext:"Payflow" intitle:"credit card"',
    'inurl:/checkout intext:"Payflow"',
    'intext:"powered by Payflow"',
    'inurl:/payment intext:"Payflow Pro"',
    'inurl:/checkout intext:"PayPal Payflow"',
    'intext:"Payflow Gateway" intitle:"checkout"'
]
def send_tg(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage", data={
            "chat_id": TG_CHAT_ID,
            "text": msg,
            "parse_mode": "Markdown"
        })
    except Exception as e:
        print(f"[!] Telegram gönderilemedi: {e}")

def already_checked(url):
    if not os.path.exists(LOG_FILE):
        return False
    with open(LOG_FILE, 'r') as f:
        return url in f.read()

def log_url(url):
    with open(LOG_FILE, 'a') as f:
        f.write(url + '\n')

def detect_gateway(text):
    if "stripe" in text:
        return "Stripe 💳"
    elif "braintree" in text and "3d secure" in text:
        return "Braintree 3D Secure 🔐"
    elif "braintree auth" in text:
        return "Braintree Auth ✅"
    elif "braintree" in text:
        return "Braintree 💵"
    elif "woocommerce" in text:
        return "WooCommerce 🛒"
    elif "payflow" in text:
        return "Payflow 💳"
    elif "square" in text:
        return "Square 🏦"
    elif "authorize.net" in text:
        return "Authorize.Net 💼"
    return "Unknown ❓"

def detect_captcha(text):
    return "✅ Var" if any(x in text for x in ['captcha', 'recaptcha', 'g-recaptcha', 'hcaptcha', 'cloudflare']) else "❌ Yok"

def detect_cloudflare(headers):
    return "✅ Var" if 'cloudflare' in headers.get('Server', '').lower() else "❌ Yok"

def get_platform(headers):
    return headers.get('Server', 'Unknown ❓')

def check_site(url):
    try:
        HEADERS['User-Agent'] = generate_user_agent()
        r = requests.get(url, headers=HEADERS, timeout=10)
        html = r.text.lower()
        status = r.status_code
        headers = r.headers
        gateway = detect_gateway(html)
        captcha = detect_captcha(html)
        cloudflare = detect_cloudflare(headers)
        platform = get_platform(headers)

        msg = f"""
🛑 **APİ BULUCU** 🛑
🔗 **Site:** {url}
💳 **Gateways:** {gateway}  
☁️ **Cloudflare:** {cloudflare}  
🔒 **Captcha:** {captcha}  
🌐 **Platform:** {platform}  
📄 **HTTP Status:** {status}  
📡 **Kurucu:** @xSoew
"""
        print(msg)
        send_tg(msg)
        log_url(url)
    except Exception as e:
        print(f"[!] Hata ({url}): {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! `/site` komutu ile tarama başlatabilirsiniz.")

async def site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Tarama başlatılıyor...")
    for dork in DORKS:
        try:
            results = search(dork, num_results=10, lang="en")
            for url in results:
                if "-" in url or already_checked(url):
                    continue
                check_site(url)
                time.sleep(random.uniform(2, 4))
        except Exception as e:
            await update.message.reply_text(f"[!] Google engelledi: {e}")
            time.sleep(10)

def telegram_bot():
    app = Application.builder().token(TG_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("site", site))
    app.run_polling()

# Her iki işlemi aynı anda çalıştırmak için
if __name__ == "__main__":
    threading.Thread(target=telegram_bot).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
