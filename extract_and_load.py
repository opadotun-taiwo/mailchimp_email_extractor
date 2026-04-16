import imaplib
import email
import yaml
import re
import csv
import os
from datetime import datetime, timedelta

# Load credentials
user = os.getenv("EMAIL_USERNAME")
password = os.getenv("EMAIL_PASSWORD")

imap_url = 'imap.gmail.com'

# Connect to Gmail
my_mail = imaplib.IMAP4_SSL(imap_url)
my_mail.login(user, password)
my_mail.select('Inbox')

# Search Mailchimp emails



since_date = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")

_, data = my_mail.search(None,
    f'(FROM "accountservices@mailchimp.com" SUBJECT "New subscriber" SINCE "{since_date}")'
)

mail_id_list = data[0].split()

print(f"Found {len(mail_id_list)} emails")

# Function to extract fields
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

            # Walk through email parts
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode(errors='ignore')

                    parsed = extract_fields(body)
                    if parsed and parsed["email"]:
                        results.append(parsed)

# Save to CSV
keys = ["email", "subscription_date", "first_name", "phone", "ip"]

with open("subscribers.csv", "w", newline='', encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=keys)
    writer.writeheader()
    writer.writerows(results)

print(f"✅ Extracted {len(results)} subscribers to subscribers.csv")

# Close connection
my_mail.close()
my_mail.logout()