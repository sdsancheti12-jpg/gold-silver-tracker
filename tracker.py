import requests
import json
import os
from datetime import datetime

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]

PRICE_FILE = "last_prices.json"
CRASH_THRESHOLD = 2.0  # percent

def fetch_prices():
    # Example using dummy values for now
    # (we can plug real API next)
    return {
        "gold": 6250.0,    # per gram
        "silver": 74500.0 # per kg
    }

def load_last_prices():
    if not os.path.exists(PRICE_FILE):
        return None
    with open(PRICE_FILE, "r") as f:
        return json.load(f)

def save_prices(prices):
    with open(PRICE_FILE, "w") as f:
        json.dump(prices, f)

def percent_change(old, new):
    return ((new - old) / old) * 100

def post_comment(message):
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    requests.post(url, headers=headers, json={"body": message})

def main():
    prices = fetch_prices()
    last = load_last_prices()

    # Daily summary (runs once daily anyway)
    summary = (
        f"📊 **Daily Metals Summary (11 AM IST)**\n\n"
        f"🥇 Gold: ₹{prices['gold']}/g\n"
        f"🥈 Silver: ₹{prices['silver']}/kg"
    )
    post_comment(summary)

    # Crash detection
    if last:
        gold_drop = percent_change(last["gold"], prices["gold"])
        silver_drop = percent_change(last["silver"], prices["silver"])

        if gold_drop <= -CRASH_THRESHOLD:
            post_comment(
                f"🚨 **GOLD PRICE CRASH**\n\n"
                f"Dropped {abs(gold_drop):.2f}%\n"
                f"Current: ₹{prices['gold']}/g"
            )

        if silver_drop <= -CRASH_THRESHOLD:
            post_comment(
                f"🚨 **SILVER PRICE CRASH**\n\n"
                f"Dropped {abs(silver_drop):.2f}%\n"
                f"Current: ₹{prices['silver']}/kg"
            )

    save_prices(prices)

if __name__ == "__main__":
    main()
