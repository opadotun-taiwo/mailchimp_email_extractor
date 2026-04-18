# Email Marketing Analytics Pipeline

## Overview
This project is an automated data pipeline that extracts subscriber data from Gmail (Mailchimp notifications), processes it using Python, stores it in Google Sheets, and delivers actionable insights through Looker Studio dashboards.

The pipeline runs monthly using GitHub Actions, ensuring that marketing and growth teams always have up-to-date data for decision-making.

---

## Goal
The primary objective of this project is to generate actionable insights from email marketing activity to evaluate and improve performance of Google Ads and Meta Ads campaigns.

By centralizing subscriber data and visualizing trends, this pipeline helps answer key business questions:
- How many new subscribers are acquired over time?
- What is the growth trend from marketing campaigns?
- Which campaigns are driving the most conversions?
- How can marketing spend be optimized based on subscriber behavior?

---

## Architecture

![Alt text](https://github.com/opadotun-taiwo/mailchimp_email_extractor/blob/main/Subscriber%20Data%20Pipeline%20Architecture.png)

## Tech Stack

- Python (Data extraction and processing)
- IMAP (Email access)
- Pandas (Data transformation)
- GitHub Actions (Scheduling and automation)
- Google Sheets API (Data storage)
- Looker Studio (Visualization and reporting)

---

## Features

- Automated email parsing from Gmail inbox
- Monthly scheduled data pipeline using GitHub Actions
- Incremental data updates with deduplication
- Centralized dataset in Google Sheets
- Ready-to-use data source for Looker Studio dashboards
- No manual intervention required after setup

---

## Repository Structure


.
├── extract_and_load.py # Main pipeline script
├── requirements.txt # Python dependencies
└── .github/
└── workflows/
└── email-extractor.yml # CI/CD automation


---

## Setup Guide

### 1. Clone the Repository

```bash
git clone https://github.com/opadotun-taiwo/mailchimp_email_extractor.git
cd mailchimp_email_extractor
2. Install Dependencies
pip install -r requirements.txt
3. Gmail Configuration
Enable IMAP in your Gmail settings
Generate an App Password (recommended instead of your main password)
4. Google Sheets Setup
Create a Google Sheet (e.g. Mailchimp Subscribers)
Create a Google Cloud Service Account
Download the JSON credentials
Share the Google Sheet with the service account email (Editor access)
5. GitHub Secrets Configuration

In your repository, go to:
Settings → Secrets → Actions

Add the following:

EMAIL_USERNAME = your_email@gmail.com
EMAIL_PASSWORD = your_app_password
GOOGLE_CREDS   = your_service_account_json
6. Run Locally (Optional)
python extract_and_load.py

This will:

Connect to Gmail
Extract subscriber data
Push results to Google Sheets
Automation

The pipeline is scheduled using GitHub Actions:

cron: '0 0 1 * *'

This means:

Runs automatically on the 1st of every month
Can also be triggered manually from the Actions tab
Output

The final dataset is stored in Google Sheets and includes:

Email
Subscription Date
First Name
Phone Number
Subscriber IP

This dataset is continuously updated and deduplicated.

Visualization (Looker Studio) - https://datastudio.google.com/reporting/d3caf121-0112-4f59-af7d-dd7162a9d330

![Alt text](https://github.com/opadotun-taiwo/mailchimp_email_extractor/blob/main/Subscriber%20Data%20Pipeline%20Architecture.png)

Connect your Google Sheet to Looker Studio to build dashboards such as:

Subscriber growth over time
Campaign performance trends
Conversion tracking
Monthly acquisition metrics
Key Design Decisions
Google Sheets used as a lightweight data warehouse for accessibility
GitHub Actions used for cost-effective scheduling
Deduplication logic ensures clean and reliable data
Modular pipeline allows easy extension (e.g., adding campaign tagging)
Challenges Solved
Automating data extraction from unstructured email content
Handling authentication securely using environment variables
Ensuring idempotent data updates (no duplicates)
Designing a low-cost, scalable pipeline without heavy infrastructure
Business Impact
Eliminates manual data collection from email marketing tools
Provides a single source of truth for subscriber analytics
Enables data-driven optimization of Google Ads and Meta Ads campaigns
Reduces reporting time and improves marketing visibility
Future Improvements
Add campaign attribution tracking
Store historical snapshots for deeper trend analysis
Integrate with a data warehouse (BigQuery)
Add alerting for abnormal drops or spikes in subscriptions
