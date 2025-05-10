"""
Usage:
python camp_mon_reserveca.py <park_id> <facility_id> <comma_separated_dates>
park_id and facility_id can be found at reservecalifornia.com URL
Example:
Website https://www.reservecalifornia.com/Web/Default.aspx#!park/690/612
python camp_mon_reserveca.py 690 611 2025-05-31,2025-06-07,2025-06-14
"""

import requests
import time
import json
from datetime import datetime, timedelta
from urllib.parse import urlencode
from dateutil.parser import isoparse
import sys
import requests

park_id = sys.argv[1]
facility_id = sys.argv[2]
dates = [isoparse(d).replace(tzinfo=None) for d in sys.argv[3].split(',')]
start_date = min(dates).strftime(r"%Y-%m-%d")
end_date = max(dates).strftime(r"%Y-%m-%d")
dates = [d.strftime(r"%Y-%m-%dT%H:%M:%S") for d in dates]

WEB_URL = f"https://www.reservecalifornia.com/Web/Default.aspx#!park/{park_id}/{facility_id}"
API_URL = f'https://calirdr.usedirect.com/RDR/rdr/search/grid'
WEBHOOKS = [
    {"url": "https://webexapis.com/v1/webhooks/incoming/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "mention": "<@personEmail:aaaaa@example.com|Alice>"},
    {"url": "https://webexapis.com/v1/webhooks/incoming/yyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", "mention": "<@personEmail:bbbbb@example.com|Bob>"},

]
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'

PAYLOAD = {
    "IsADA": False,
    "MinVehicleLength": 0,
    "UnitCategoryId": 0,
    "StartDate": start_date,
    "WebOnly": True,
    "UnitTypesGroupIds": [],
    "SleepingUnitId": 0,
    "EndDate": end_date,
    "UnitSort": "orderby",
    "InSeasonOnly": True,
    "FacilityId": f"{facility_id}",
    "RestrictADA": False
}

print("WEB_URL:", WEB_URL)
print("DATES:", dates)
print("PAYLOAD:", json.dumps(PAYLOAD, indent=2))

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
        resp = requests.post(API_URL, headers={"User-agent": USER_AGENT}, json=PAYLOAD)
        resp.raise_for_status()
        result = resp.json()
        units = result["Facility"]["Units"]
        if units is None:
            log("No Units returned")
            continue
        available_dates = [
            d for d in dates 
            if any(
                d in u["Slices"] and u["Slices"][d]["IsFree"] == True
                for u in units.values()
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
        time.sleep(60)
