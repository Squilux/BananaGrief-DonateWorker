import os
import time
import requests
from mcrcon import MCRcon

# =========================
# ENV VARIABLES
# =========================
DA_TOKEN = os.getenv("DA_TOKEN")

RCON_HOST = os.getenv("RCON_HOST")
RCON_PORT = int(os.getenv("RCON_PORT"))
RCON_PASS = os.getenv("RCON_PASS")

# =========================
# КУРС (АВТО)
# =========================
EUR_RATE = 100  # fallback если API не работает
last_rate_update = 0

def get_eur_rate():
    global EUR_RATE, last_rate_update

    # обновляем раз в 10 минут
    if time.time() - last_rate_update < 600:
        return EUR_RATE

    try:
        r = requests.get("https://api.exchangerate.host/latest?base=EUR&symbols=RUB")
        data = r.json()

        if "rates" in data and "RUB" in data["rates"]:
            EUR_RATE = float(data["rates"]["RUB"])
            last_rate_update = time.time()
            print("UPDATED EUR RATE:", EUR_RATE)

    except Exception as e:
        print("RATE ERROR:", e)

    return EUR_RATE

# =========================
# PRICES (НЕ ТРОГАЕМ)
# =========================
PRICES = {
    "fly": 99,

    "points_100": 65,
    "points_300": 130,
    "points_500": 260,
    "points_1000": 520,

    "acb_100": 50,
    "acb_500": 130,
    "acb_1000": 195,
    "acb_1500": 255,

    "vip": 130,
    "vipplus": 275,
    "premium": 440,
    "helper": 800,
}

# =========================
# ЦЕНЫ КЕЙСОВ (КАК В ТГ)
# =========================
CASE_PRICES = {
    "Divine": {"1": 85, "5": 320, "10": 560, "20": 830},
    "Inferno": {"1": 72, "5": 240, "10": 430, "20": 670},
    "Supreme": {"1": 65, "5": 195, "10": 385, "20": 590},
    "Titan": {"1": 58, "5": 175, "10": 265, "20": 490},
    "Galaxy": {"1": 44, "5": 145, "10": 220, "20": 365},
    "Royal": {"1": 35, "5": 115, "10": 155, "20": 285},
    "Legend": {"1": 20, "5": 85, "10": 110, "20": 195},
}

last_id = None

# =========================
# RCON
# =========================
def run(cmd):
    try:
        with MCRcon(RCON_HOST, RCON_PASS, port=RCON_PORT) as mcr:
            print("RUN:", cmd)
            print(mcr.command(cmd))
    except Exception as e:
        print("RCON ERROR:", e)

# =========================
# PROCESS
# =========================
def process(comment, amount):
    args = comment.split()

    if len(args) < 2:
        print("BAD COMMENT:", comment)
        return

    nick = args[0]
    product = args[1]

    # ===== FLY =====
    if product.lower() == "fly":
        if amount >= PRICES["fly"]:
            run(f"lp user {nick} permission set flyingallowe.command.fly true")
            run(f"lp user {nick} permission set flyingallowed.in.regions true")
        return

    # ===== РАНГИ =====
    if product.lower() in ["vip", "vipplus", "premium", "helper"]:
        if amount >= PRICES[product.lower()]:
            run(f"lp user {nick} parent set {product.lower()}")
        return

    # ===== POINTS =====
    if product.lower() == "points" and len(args) >= 3:
        value = args[2]
        key = f"points_{value}"

        if key in PRICES and amount >= PRICES[key]:
            run(f"points give {nick} {value}")
        return

    # ===== ACB =====
    if product.lower() == "acb" and len(args) >= 3:
        value = args[2]
        key = f"acb_{value}"

        if key in PRICES and amount >= PRICES[key]:
            run(f"acb {nick} {value}")
        return

    # ===== КЕЙСЫ =====
    if product in CASE_PRICES and len(args) >= 3:
        amount_keys = args[2]

        if amount_keys in CASE_PRICES[product]:
            price = CASE_PRICES[product][amount_keys]

            if amount >= price:
                run(f"cc give virtual {product} {amount_keys} {nick}")
            else:
                print("NOT ENOUGH MONEY FOR CASE")
        return

# =========================
# CHECK DONATES
# =========================
def check_donates():
    global last_id

    headers = {
        "Authorization": f"Bearer {DA_TOKEN}"
    }

    while True:
        try:
            r = requests.get(
                "https://www.donationalerts.com/api/v1/alerts/donations",
                headers=headers
            )

            data = r.json()

            if "data" in data:
                donations = data["data"]

                for d in reversed(donations):
                    donate_id = d["id"]

                    if donate_id == last_id:
                        continue

                    last_id = donate_id

                    amount = float(d["amount"])
                    currency = d.get("currency", "RUB")

                    # 💶 КОНВЕРТАЦИЯ
                    if currency == "EUR":
                        rate = get_eur_rate()
                        amount = amount * rate

                    amount = int(amount)
                    comment = d["message"]

                    print("NEW DONATE:", amount, currency, comment)

                    process(comment, amount)

        except Exception as e:
            print("API ERROR:", e)

        time.sleep(10)

print("Donate Worker Started...")
check_donates()
