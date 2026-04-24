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
# PRICES (RUB)
# МЕНЯЙ ТУТ ЦЕНЫ
# =========================
PRICES = {
    "fly": 99,

    "points_100": 29,
    "points_300": 59,
    "points_500": 89,
    "points_1000": 149,
    "points_1500": 199,
    "points_2000": 249,

    "acb_300": 49,
    "acb_500": 79,
    "acb_1000": 129,
    "acb_1500": 179,

    "case_1": 39,
    "case_5": 149,
    "case_10": 249,
    "case_20": 449
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
# Формат комментария:
# Nick fly
# Nick points 500
# Nick acb 1000
# Nick Divine 5
# =========================
def process(comment, amount):
    args = comment.split()

    if len(args) < 2:
        print("BAD COMMENT")
        return

    nick = args[0]
    product = args[1]

    # =========================
    # FLY
    # =========================
    if product.lower() == "fly":
        if amount >= PRICES["fly"]:
            run(f"lp user {nick} permission set flyingallowe.command.fly true")
            run(f"lp user {nick} permission set flyingallowed.in.regions true")
        return

    # =========================
    # POINTS
    # =========================
    if product.lower() == "points" and len(args) >= 3:
        value = args[2]

        key = f"points_{value}"

        if key in PRICES and amount >= PRICES[key]:
            run(f"points give {nick} {value}")
        return

    # =========================
    # ACB
    # =========================
    if product.lower() == "acb" and len(args) >= 3:
        value = args[2]

        key = f"acb_{value}"

        if key in PRICES and amount >= PRICES[key]:
            run(f"acb {nick} {value}")
        return

    # =========================
    # CASES
    # =========================
    if product in CASES and len(args) >= 3:
        keys = args[2]

        key = f"case_{keys}"

        if key in PRICES and amount >= PRICES[key]:
            run(f"cc give virtual {product} {keys} {nick}")
        return

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

                    amount = int(float(d["amount"]))
                    comment = d["message"]

                    print("NEW DONATE:", amount, comment)

                    process(comment, amount)

        except Exception as e:
            print("API ERROR:", e)

        time.sleep(10)

print("Donate Worker Started...")
check_donates()
