import requests
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode
from dateutil.parser import isoparse
import sys
import requests

camp_site = sys.argv[1]
dates = [isoparse(d).replace(tzinfo=None).isoformat(timespec='seconds') + "Z" for d in sys.argv[2].split(',')]
month_begin = isoparse(dates[0]).replace(day=1, tzinfo=None).isoformat(timespec='milliseconds') + "Z"

WEB_URL = f"https://www.recreation.gov/camping/campgrounds/{camp_site}"
API_URL = f'https://www.recreation.gov/api/camps/availability/campground/{camp_site}/month?{urlencode({"start_date": month_begin})}'
WEBHOOKS = [
    {"url": "https://webexapis.com/v1/webhooks/incoming/xxxxxxxxxxxxxxxxxxxxx", "mention": "<@personEmail:aaaa@example.com|Alice>"},
    {"url": "https://webexapis.com/v1/webhooks/incoming/yyyyyyyyyyyyyyyyyyyyy", "mention": "<@personEmail:bbbb@gmail.com|Bob>"},

]
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'

print("WEB_URL:", WEB_URL)
print("API_URL:", API_URL)
print("DATES:", dates)

last_msg_date_found = last_msg_date_exception = None
exc_count = 0

def send_messages(message):
    for webhook in WEBHOOKS:
        requests.post(webhook["url"], json={"markdown": message.format(mention=webhook["mention"])})

def log(msg):
    print(f"[{datetime.utcnow().isoformat(timespec='seconds')}] {msg}")


send_messages(f"{{mention}}, Start to monitor camp sites for {WEB_URL}")

while True:
    try:
        resp = requests.get(API_URL, headers={"User-agent": USER_AGENT})
        resp.raise_for_status()
        result = resp.json()
        available_dates = [
            d for d in dates 
            if any(
                d in c["availabilities"] and c["availabilities"][d] == "Available"
                for c in result["campsites"].values()
            )
        ]
        if available_dates:
            log("Found!")
            if last_msg_date_found is None or last_msg_date_found < datetime.utcnow() - timedelta(minutes=5):
                send_messages(f"{{mention}}, Found campsite on {available_dates}! Go to {WEB_URL}")
                last_msg_date_found = datetime.utcnow()
        else:
            log("Not found")
        exc_count = 0
    except Exception as e:
        log(f"Exception: {str(e)}")
        exc_count += 1
        if exc_count >= 3:
            if last_msg_date_exception is None or last_msg_date_exception < datetime.utcnow() - timedelta(minutes=5):
                send_messages(f"{{mention}}, Exception happend on finding campsite: {str(e)}")
                last_msg_date_exception = datetime.utcnow()
    finally:
        sys.stdout.flush()
        time.sleep(120)
