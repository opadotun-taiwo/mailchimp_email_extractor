import imaplib
import email
import re
import os
import pandas as pd
from datetime import datetime, timedelta

# NEW: Google Sheets imports
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load credentials
user = os.getenv("EMAIL_USERNAME")
password = os.getenv("EMAIL_PASSWORD")
google_creds = os.getenv("GOOGLE_CREDS")  # NEW

if not user or not password:
    raise ValueError("EMAIL_USERNAME or EMAIL_PASSWORD not set")

if not google_creds:
    raise ValueError("GOOGLE_CREDS not set")

imap_url = 'imap.gmail.com'

# Connect to Gmail
my_mail = imaplib.IMAP4_SSL(imap_url)
my_mail.login(user, password)
my_mail.select('Inbox')

# Search Mailchimp emails
since_date = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")

status, data = my_mail.search(
    None,
    f'(FROM "accountservices@mailchimp.com" SUBJECT "New subscriber" SINCE "{since_date}")'
)

if status != "OK":
    raise Exception("Failed to search emails")

mail_id_list = data[0].split()

print(f"Found {len(mail_id_list)} emails")

# Extract fields
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

# Loop through emails
for i, num in enumerate(mail_id_list):
    print(f"Processing email {i+1}/{len(mail_id_list)}")
    typ, data = my_mail.fetch(num, '(RFC822)')

    for response_part in data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])

            for part in msg.walk():
                if part.get_content_type() in ['text/plain', 'text/html']:  # UPDATED
                    body = part.get_payload(decode=True).decode(errors='ignore')

                    parsed = extract_fields(body)
                    if parsed and parsed["email"]:
                        results.append(parsed)

# Convert to DataFrame
df_new = pd.DataFrame(results)


# GOOGLE SHEETS INTEGRATION

# Save credentials to file (for gspread)
with open("access.json", "w") as f:
    f.write(google_creds)

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name("access.json", scope)
client = gspread.authorize(creds)

# Open your sheet (make sure name matches exactly)
sheet = client.open("Mailchimp Subscribers").sheet1

# Load existing data from sheet
try:
    existing_data = sheet.get_all_records()
    df_existing = pd.DataFrame(existing_data)
    df = pd.concat([df_existing, df_new])
    df = df.drop_duplicates(subset=["email"])
except:
    df = df_new

# Clear and update sheet
sheet.clear()
sheet.update([df.columns.values.tolist()] + df.values.tolist())

print(f"Total unique subscribers in sheet: {len(df)}")

# Close connection
my_mail.close()
my_mail.logout()