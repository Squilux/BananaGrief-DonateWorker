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
# PRICES RUB
# =========================
PRICES = {
    "fly": 99,

    "points_100": 29,
    "points_300": 59,
    "points_500": 89,
    "points_1000": 149,

    "acb_100": 49,
    "acb_500": 79,
    "acb_1000": 129,
    "acb_1500": 129,

    "case_1": 39,
    "case_5": 149,
    "case_10": 249,
    "case_20": 449,

    "vip": 299,
    "vipplus": 499,
    "premium": 999,
    "helper": 1499,
}

# =========================
# PRICES EUR
# =========================
PRICES_EUR = {
    "fly": 2,

    "points_100": 1,
    "points_300": 2,
    "points_500": 3,
    "points_1000": 5,

    "acb_100": 1,
    "acb_500": 2,
    "acb_1000": 3,
    "acb_1500": 4,

    "case_1": 1,
    "case_5": 3,
    "case_10": 5,
    "case_20": 9,

    "vip": 4,
    "vipplus": 6,
    "premium": 12,
    "helper": 18,
}

# =========================
# CASE NAMES
# =========================
CASES = [
    "Divine",
    "Inferno",
    "Supreme",
    "Titan",
    "Galaxy",
    "Royal"
]

last_id = None

# =========================
# RCON SEND
# =========================
def run(cmd):
    try:
        with MCRcon(RCON_HOST, RCON_PASS, port=RCON_PORT) as mcr:
            print("RUN:", cmd)
            print(mcr.command(cmd))
    except Exception as e:
        print("RCON ERROR:", e)

# =========================
# PROCESS DONATE
# =========================
def process(comment, amount, currency):
    args = comment.split()

    if len(args) < 2:
        print("BAD COMMENT:", comment)
        return

    nick = args[0]
    product = args[1].lower()
    value = args[2] if len(args) >= 3 else None

    prices = PRICES if currency == "RUB" else PRICES_EUR

    print("PARSED:", nick, product, value, "|", amount, currency)

    # =========================
    # ПРИВИЛЕГИИ
    # =========================
    if product in ["vip", "vipplus", "premium", "helper"]:
        if amount >= prices[product]:
            run(f"lp user {nick} parent set {product}")
        return

    # =========================
    # FLY
    # =========================
    if product == "fly":
        if amount >= prices["fly"]:
            run(f"lp user {nick} permission set flyingallowe.command.fly true")
            run(f"lp user {nick} permission set flyingallowed.in.regions true")
        return

    # =========================
    # POINTS
    # =========================
    if product == "points" and value:
        key = f"points_{value}"
        if key in prices and amount >= prices[key]:
            run(f"points give {nick} {value}")
        return

    # =========================
    # БЛОКИ ПРИВАТА
    # =========================
    if product == "acb" and value:
        key = f"acb_{value}"
        if key in prices and amount >= prices[key]:
            run(f"acb {nick} {value}")
        return

    # =========================
    # КЕЙСЫ
    # =========================
    if value:
        case_name = product.capitalize()
        key = f"case_{value}"

        if case_name in CASES and key in prices and amount >= prices[key]:
            run(f"cc give virtual {case_name} {value} {nick}")
        return

    print("UNKNOWN:", comment)

# =========================
# CHECK DONATIONS
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
                    comment = d["message"]

                    print("NEW DONATE:", amount, currency, comment)

                    process(comment, amount, currency)

        except Exception as e:
            print("API ERROR:", e)

        time.sleep(10)

print("Donate Worker Started...")
check_donates()
