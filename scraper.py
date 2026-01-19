import os
import sys
import datetime
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_TARGET_ID = os.getenv("LINE_TARGET_ID")  # User ID or Group ID
TARGET_URL = "https://cloud.coolpc.com.tw:168/"
TARGET_NAMES = ["王韋勝", "戴克羽", "廖桂彬", "白森中", "廖克豪", "謝伯承", "劉翔曜"]


def send_line_message(message):
    """Sends a push message using LINE Messaging API."""
    if not LINE_CHANNEL_ACCESS_TOKEN:
        print("Error: LINE_CHANNEL_ACCESS_TOKEN is not set.")
        return
    if not LINE_TARGET_ID:
        print("Error: LINE_TARGET_ID is not set.")
        return

    headers = {
        "Authorization": "Bearer " + LINE_CHANNEL_ACCESS_TOKEN,
        "Content-Type": "application/json",
    }

    payload = {"to": LINE_TARGET_ID, "messages": [{"type": "text", "text": message}]}

    try:
        response = requests.post(
            "https://api.line.me/v2/bot/message/push", headers=headers, json=payload
        )
        response.raise_for_status()
        print("Notification sent successfully.")
    except Exception as e:
        print(f"Failed to send notification: {e}")
        if "response" in locals() and hasattr(response, "text"):
            print(f"Server response: {response.text}")


def get_today_leave_status():
    """Scrapes the website and checks for target employees on leave today."""

    # 1. Get Today's Date in MM/DD format (e.g., "01/17")
    # GitHub Actions runners are in UTC, so we must add 8 hours for Taiwan Time
    tz = datetime.timezone(datetime.timedelta(hours=8))
    today = datetime.datetime.now(tz)
    date_str = today.strftime("%m/%d")
    print(f"Checking leave status for: {date_str}")

    # 2. Fetch the website
    try:
        response = requests.get(TARGET_URL, timeout=10)
        response.raise_for_status()
        response.encoding = "utf-8"  # Ensure correct encoding
    except Exception as e:
        return f"Error fetching website: {e}"

    soup = BeautifulSoup(response.text, "html.parser")

    # 3. Find the column index for today
    table = soup.find("table", class_="table-fixed")
    if not table:
        return "Error: Could not find the main table."

    headers = table.find("thead").find_all("th")
    target_col_index = -1

    for i, th in enumerate(headers):
        if date_str in th.get_text():
            target_col_index = i
            break

    if target_col_index == -1:
        return f"Error: Could not find column for date {date_str}."

    # 4. Get the content for that column
    tbody = table.find("tbody")
    rows = tbody.find_all("tr")

    if not rows:
        return "Error: No data rows found."

    target_td = None
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > target_col_index:
            target_td = cells[target_col_index]
            break

    if not target_td:
        return "Error: Could not find data cell for today."

    # 5. Check for names in the cell content
    cell_text = target_td.get_text()

    leavers = []

    for name in TARGET_NAMES:
        if name in cell_text:
            status = "休假"
            try:
                idx = cell_text.find(name)
                rest = cell_text[idx + len(name) :]
                if rest.startswith("【"):
                    end = rest.find("】")
                    if end != -1:
                        status = rest[1:end]
            except:
                pass

            leavers.append(f"{name} ({status})")

    # 6. Formulate Message
    if leavers:
        msg = f"[{date_str} 休假通報]\n今日請假人員：\n" + "\n".join(leavers)
    else:
        msg = f"[{date_str} 休假通報]\n今日監控名單無人請假。"

    return msg


if __name__ == "__main__":
    print("Starting scraper (Messaging API)...")
    result_msg = get_today_leave_status()
    print("Result:")
    print(result_msg)

    if LINE_CHANNEL_ACCESS_TOKEN and LINE_TARGET_ID:
        send_line_message(result_msg)
    else:
        print("\nWARNING: Token or Target ID missing. Message not sent.")
