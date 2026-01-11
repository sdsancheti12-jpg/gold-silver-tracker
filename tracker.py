import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]

PRICE_FILE = "last_prices.json"
CRASH_THRESHOLD = 10.0  # percent

def fetch_silver_1kg_price():
    url = "https://www.goodreturns.in/silver-rates/"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    section = soup.find(
        "section",
        {"data-gr-title": "Today Silver Price Per Gram/Kg in India (INR)"}
    )

    if not section:
        raise Exception("Silver rate section not found")

    rows = section.select("tbody tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        gram = cols[0].text.strip()

        if gram == "1000":
            price_text = cols[1].text.strip()
            price = float(
                price_text.replace("₹", "").replace(",", "")
            )
            return price  # ₹ per 1kg

    raise Exception("1kg silver price not found")
    
def fetch_gold_10g_price():
    url = "https://www.goodreturns.in/gold-rates/"  # example page
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Find the specific section (optional but safer)
    section = soup.find(
        "section",
        {"data-gr-title": "Today 24 Carat Gold Rate Per Gram in India (INR)"}
    )

    if not section:
        raise Exception("Gold rate section not found")

    rows = section.select("tbody tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 2:
            continue

        gram = cols[0].text.strip()

        if gram == "10":
            price_text = cols[1].text.strip()
            price = float(
                price_text.replace("₹", "").replace(",", "")
            )
            return price  # ₹ per 10g

    raise Exception("10g gold price not found")
    
def fetch_prices():
    
    return {
        "gold": fetch_gold_10g_price() ,    # per 10 gram
        "silver": fetch_silver_1kg_price()  # per kg
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
    if old == 0:
        return 0
    return ((new - old) / old) * 100


def post_comment(message):
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE_NUMBER}/comments"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    resp= requests.post(url, headers=headers, json={"body": message})
    resp.raise_for_status()

def main():
    prices = fetch_prices()
    last = load_last_prices()

    # Daily summary (runs once daily anyway)
    summary = (
        f"📊 **Daily Metals Summary (11 AM IST)**\n\n"
        f"🥇 Gold: ₹{prices['gold']}/10g\n"
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
                f"Current: ₹{prices['gold']}/10g"
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
