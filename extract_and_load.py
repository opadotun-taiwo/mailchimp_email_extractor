import imaplib
import email
import re
import os
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import base64
import json
import requests


# LOAD CREDENTIALS
user = os.getenv("EMAIL_USERNAME")
password = os.getenv("EMAIL_PASSWORD")
google_creds_b64 = os.getenv("GOOGLE_CREDS")

if not user or not password:
    raise ValueError("EMAIL_USERNAME or EMAIL_PASSWORD not set")

if not google_creds_b64:
    raise ValueError("GOOGLE_CREDS not set")

# Decode base64 to JSON
decoded_creds = base64.b64decode(google_creds_b64).decode("utf-8")
creds_dict = json.loads(decoded_creds)


# GOOGLE SHEETS AUTH

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sheet = client.open("Mailchimp Subscribers").sheet1


# IP GEOLOCATION (WITH CACHE)
ip_cache = {}

def get_location(ip):
    try:
        if not ip or ip.startswith(("127.", "192.168")):
            return {"city": None, "state": None, "country": None}

        if ip in ip_cache:
            return ip_cache[ip]

        url = f"https://ipinfo.io/{ip}/json"
        res = requests.get(url, timeout=5).json()

        location = {
            "city": res.get("city"),
            "state": res.get("region"),
            "country": res.get("country")
        }

        ip_cache[ip] = location
        return location

    except Exception as e:
        print(f"IP lookup failed for {ip}: {e}")
        return {"city": None, "state": None, "country": None}


# GMAIL SETUP
imap_url = 'imap.gmail.com'
my_mail = imaplib.IMAP4_SSL(imap_url)
my_mail.login(user, password)
my_mail.select('Inbox')

since_date = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")

status, data = my_mail.search(
    None,
    f'(FROM "accountservices@mailchimp.com" SUBJECT "New subscriber" SINCE "{since_date}")'
)

if status != "OK":
    raise Exception("Failed to search emails")

mail_id_list = data[0].split()
print(f"Found {len(mail_id_list)} emails")


# EXTRACT FIELDS
def extract_fields(text):
    try:
        email_match = re.search(r"Here's who subscribed:\s*(\S+)", text)
        date_match = re.search(r"Subscription date:\s*(.*)", text)
        name_match = re.search(r"First Name:\s*(.*)", text)
        phone_match = re.search(r"Phone Number:\s*(.*)", text)
        ip_match = re.search(r"Subscriber IP:\s*(.*)", text)

        return {
            "email": email_match.group(1).strip() if email_match else None,
            "subscription_date": date_match.group(1).strip() if date_match else None,
            "first_name": name_match.group(1).strip() if name_match else None,
            "phone": phone_match.group(1).strip() if phone_match else None,
            "ip": ip_match.group(1).strip() if ip_match else None
        }
    except Exception as e:
        print("Error parsing:", e)
        return None

results = []


# PROCESS EMAILS and ENRICHMENT

for i, num in enumerate(mail_id_list):
    print(f"Processing email {i+1}/{len(mail_id_list)}")
    typ, data = my_mail.fetch(num, '(RFC822)')

    for response_part in data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])

            for part in msg.walk():
                if part.get_content_type() in ['text/plain', 'text/html']:
                    body = part.get_payload(decode=True).decode(errors='ignore')

                    parsed = extract_fields(body)
                    if parsed and parsed["email"]:
                        
                        # 🔥 Enrich with location
                        location = get_location(parsed.get("ip"))

                        parsed.update({
                            "city": location["city"],
                            "state": location["state"],
                            "country": location["country"]
                        })

                        results.append(parsed)


# CONVERT TO DATAFRAME

df_new = pd.DataFrame(results)


# LOAD EXISTING DATA

try:
    existing_data = sheet.get_all_records()
    df_existing = pd.DataFrame(existing_data)

    df = pd.concat([df_existing, df_new])
    df = df.drop_duplicates(subset=["email"])

    df = df.astype(object).where(pd.notnull(df), "")

except Exception as e:
    print("No existing data or error:", e)
    df = df_new


# UPDATE SHEET

sheet.clear()
sheet.update([df.columns.values.tolist()] + df.values.tolist())

print(f"Total unique subscribers in sheet: {len(df)}")


# CLOSE CONNECTION

my_mail.close()
my_mail.logout()