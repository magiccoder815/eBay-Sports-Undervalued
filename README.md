# Overview

The Undervalued Cards Scraper is a Python script that scrapes eBay for undervalued sports cards. It collects data on newly listed cards, evaluates their prices, and identifies those that are undervalued based on their historical prices. The script can also send an email alert with the details of undervalued cards.

# Features

-   Scrapes eBay listings for sports cards.
-   Analyzes prices to determine undervalued cards.
-   Sends email alerts with card details.
-   Saves the collected data as an Excel file date by date.(C:/eBay_undervalued/)

# Auto Daily Update Implementation

-   Extract ebay-sports-undervalued.zip file.
-   Press Win + R, type taskschd.msc, and press Enter.
-   In the Task Scheduler, click "Create Basic Task" (on the right panel).
-   Name the Task: Enter a name like "eBay Undervalued Cards" and click Next.
-   Trigger (When to Run): Select Daily and click Next.
-   Start Date & Time: Choose a start date and time (e.g., every day at 00:05 AM) and click Next.
-   Action (What to Run): Select "Start a Program" and click Next.
-   Click Browse and select undervalued_cards.exe. (e.g. C:\ebay-sports-undervalued\undervalued_cards.exe)
-   Click Next, then Finish.

# Source Code Reference

## Python Installation

-   Download the Python installer from the official Python website. (v3.11.2 or greater)
-   Run the installer and ensure to check the box that says "Add Python to PATH".
-   Follow the prompts to complete the installation.

## Install Required Libraries

```bash
pip install requests beautifulsoup4 pandas numpy openpyxl secure-smtplib yagmail
```

# Run Script

```bash
cd undervalued_cards
python undervalued_cards.py
```
