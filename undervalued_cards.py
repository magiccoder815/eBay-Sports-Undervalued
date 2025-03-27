import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import threading
import os
from datetime import datetime, timedelta
from urllib.parse import quote
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Define the base URL template
base_url = "https://www.ebay.com/sch/i.html?_oaa=1&_dcat=212&_udlo=100&_fsrp=1&_from=R40&Grade=8%7C8%252E5%7C9%7C9%252E5%7C10%7C%21&_ipg=240&Sport=Baseball%7CFootball%7CBasketball&_sacat=64482&_nkw=PSA&_sop=1&Season=2020%7C2020%252D21%7C2021%7C2021%252D22%7C2022%7C2022%252D23%7C2023%7C2023%252D24%7C2024%7C2025&LH_PrefLoc=2&rt=nc&LH_Auction=1&_pgn={}"

start_time = time.time()

# Ensure the directory exists for the output
output_dir = "C:/eBay_undervalued"
os.makedirs(output_dir, exist_ok=True)

def send_email(undervalued_cards):
    sender_email = "igorkovalevych94@gmail.com"  # Replace with your email
    sender_password = "gzpp wrgf xtzw agoj"  # Replace with your email password
    receiver_email = "superphantom2035@gmail.com"
    
    # Create the email content
    subject = "Undervalued Cards Alert"
    # Load the HTML template
    with open('C:/ebay-sports-undervalued/email-template.html', 'r') as file:
        template = file.read()

    # Generate the cards HTML
    cards_html = ""
    for card in undervalued_cards:
        cards_html += f"""
        <div class="card">
            <div class="card-inner">
                <div class="card-image">
                    <img src="{card['Image URL']}" alt="{card['Title']}">
                </div>
                <div class="card-details">
                    <h3 class="card-title">
                        <a href="{card['Card Link']}">{card['Title']}</a>
                    </h3>
                    <!-- Conditionally display Ending Date if Buying Type is Auction -->
                    {"<div class='end-date'>Ends in " + card['Ending Date'] + "</div>" if card['Buying Type'] == 'Auction' else ''}
                    <div class="card-data">
                        <span class="card-label">Current Price:</span>
                        <span class="current-price">{card['Price']}</span>
                    </div>
                    <div class="card-grid">                    
                        <div class="card-data">
                            <span class="card-label">Min Price:</span>
                            <span class="card-value">{card['Min']}</span>
                        </div>
                        
                        <div class="card-data">
                            <span class="card-label">Max Price:</span>
                            <span class="card-value">{card['Max']}</span>
                        </div>
                        
                        <div class="card-data">
                            <span class="card-label">Average:</span>
                            <span class="card-value">{card['Average']}</span>
                        </div>
                        
                        <div class="card-data">
                            <span class="card-label">Median:</span>
                            <span class="card-value">{card['Median']}</span>
                        </div>
                    </div>

                    <a href="{card['Card Link']}" class="card-button">View Details</a>
                </div>
            </div>
        </div>
        """

    # Replace the placeholder in the template with the generated cards HTML
    final_html = template.replace('<!-- CARD_LIST_PLACEHOLDER -->', cards_html)

    # Now you can use final_html with your email sending library
    body = final_html
    
    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach the body with HTML format
    msg.attach(MIMEText(body, 'html'))

    # Create SMTP session
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # Enable security
        server.login(sender_email, sender_password)  # Login with your email and password
        server.send_message(msg)  # Send the email


def clean_set_name(set_name):
    return re.sub(r'^\d{4}(-\d{2})?\s*', '', set_name).strip()

def print_elapsed_time():
    while True:
        elapsed_time = time.time() - start_time
        time.sleep(1)  # Update every second

elapsed_time_thread = threading.Thread(target=print_elapsed_time, daemon=True)
elapsed_time_thread.start()


page = 1
data = []

# Get today's and yesterday's date
today = datetime.now().date()
today_date_str = today.strftime('%Y-%m-%d')
yesterday = today - timedelta(days=1)  # Define yesterday
yesterday_date_str = yesterday.strftime('%Y-%m-%d')
# Calculate the target date (7 days ago)
days_ago = today - timedelta(days=60)

def get_price(price_text):
    price_match = re.match(r'(\d+\.\d+)(?:to|–)?', price_text)
    if price_match:
        price = float(price_match.group(1))
    else:
        price = 0.99  # Set default value if no match is found
    return price

def fetch_price_data(title, buying_type, price):
    encoded_title = quote(title)
    if buying_type == "Buy It Now":
        price_url = f"https://www.ebay.com/sch/i.html?_nkw={encoded_title}&_sacat=0&_from=R40&LH_Complete=1&LH_Sold=1&LH_PrefLoc=2&rt=nc&LH_BIN=1&_sop=12&_ipg=240"
    else:  # Auction
        price_url = f"https://www.ebay.com/sch/i.html?_nkw={encoded_title}&_sacat=0&_from=R40&LH_Complete=1&LH_Sold=1&LH_PrefLoc=2&rt=nc&LH_Auction=1&_sop=12&_ipg=240"
    response = requests.get(price_url)
    if response.status_code != 200:
        print(f"Failed to retrieve price data: {response.status_code}")
        return 0.0, 0.0, 0.0, 0.0, 0

    soup = BeautifulSoup(response.text, 'html.parser')
    sold_items_container = soup.find('ul', class_='srp-results srp-list clearfix')
    if not sold_items_container:
        return 0.0, 0.0, 0.0, 0.0, 0
    sold_items = sold_items_container.find_all("li", attrs={"data-view": re.compile(r"^mi:1686\|iid:(\d+)$")})
    sold_prices = []

    for item in sold_items:
        sold_date_element = item.find('span', class_='s-item__caption--signal POSITIVE')
        sold_date_text = ""
        if sold_date_element:
            sold_date_text = sold_date_element.get_text(strip=True)

        if sold_date_text:
            sold_date_text = sold_date_text.replace("Sold ", "").strip()  # Strip whitespace
            try:
                sold_date = datetime.strptime(sold_date_text, '%b %d, %Y')
            except ValueError:
                try:
                    sold_date = datetime.strptime(sold_date_text, '%d %b %Y')
                except ValueError:
                    print(f"Date format error for sold date: {sold_date_text}")
                    continue

            if days_ago <= sold_date.date() <= today:
                sold_price_span = item.find('span', class_='s-item__price')
                sold_price_text = sold_price_span.get_text(strip=True).replace('$', '').replace(',', '').strip()
                sold_price = get_price(sold_price_text)
                if 0.5*price <= sold_price <= 1.5*price:
                    sold_prices.append(sold_price)

    if not sold_prices:
        return 0.0, 0.0, 0.0, 0.0, 0

    # # Remove min and max prices
    # sold_prices.remove(min(sold_prices))
    # sold_prices.remove(max(sold_prices))

    # Recalculate min, max, average, and median prices
    new_min_price = min(sold_prices)
    new_max_price = max(sold_prices)
    new_avg_price = sum(sold_prices) / len(sold_prices)
    new_median_price = np.median(sold_prices)

    return new_min_price, new_max_price, new_avg_price, new_median_price, len(sold_prices)

try:
    while True:
        page_start_time = time.time()
        response = requests.get(base_url.format(page))

        if response.status_code != 200:
            print(f"Failed to retrieve page {page}: {response.status_code}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        items_container = soup.find('ul', class_='srp-results srp-list clearfix')
        items = items_container.find_all("li", attrs={"data-view": re.compile(r"^mi:1686\|iid:(\d+)$")})
        items_count = 0

        for item in items:
            # Extract Listing Date
            # listing_date_element = item.find('span', class_='s-item__dynamic s-item__listingDate')
            # listing_date = ""
            # if listing_date_element:
            #     listing_date_text = listing_date_element.find('span', class_='BOLD').get_text(strip=True)
            #     current_year = datetime.now().year
            #     if len(listing_date_text.split('-')) == 2:  # Format is likely "Mar-14"
            #         listing_date_text = f"{current_year}-{listing_date_text}"  # Append current year
            #         listing_date_text = listing_date_text.replace('-', ' ')  # Change to "2025 Mar 14"
            #     listing_date = datetime.strptime(listing_date_text, '%Y %b %d %H:%M')
            # print(listing_date)
            # Check if the listing date is today or yesterday

            # Define the time window
            now = datetime.now()
            today_8pm = now.replace(hour=20, minute=0, second=0, microsecond=0)
            tomorrow_8pm = today_8pm + timedelta(days=1)
            # tomorrow_8pm = today_8pm + timedelta(days=1)
            # tomorrow_8pm = tomorrow_8pm.replace(hour=1, minute=0, second=0, microsecond=0)
            # Mapping for weekdays to determine the correct date
            weekday_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}

            end_date_element = item.find('span', class_='s-item__time-end')
            end_datetime = None
            if end_date_element:
                end_date_text = end_date_element.get_text(strip=True).replace("(", "").replace(")", "")
                # Case 1: "Today 01:22 PM"
                if end_date_text.startswith("Today"):
                    time_match = re.search(r'(\d{1,2}:\d{2} [APM]{2})', end_date_text)
                    if time_match:
                        time_str = time_match.group(1)
                        end_datetime = datetime.strptime(time_str, "%I:%M %p").replace(
                            year=now.year, month=now.month, day=now.day
                        )

                # Case 2: "Thu, 03:40 PM"
                else:
                    match = re.search(r'([A-Za-z]{3}), (\d{1,2}:\d{2} [APM]{2})', end_date_text)
                    if match:
                        weekday_str, time_str = match.groups()
                        today_weekday = now.weekday()
                        target_weekday = weekday_map.get(weekday_str)

                        if target_weekday is not None:
                            days_ahead = (target_weekday - today_weekday) % 7
                            target_date = now + timedelta(days=days_ahead)
                            end_datetime = datetime.strptime(time_str, "%I:%M %p").replace(
                                year=target_date.year, month=target_date.month, day=target_date.day
                            )
                # Validate time range (between today 8 PM and tomorrow 8 PM)
                if end_datetime and today_8pm <= end_datetime <= tomorrow_8pm:
                        print(f"Valid item ending at: {end_datetime}")

                        # Extract item details
                        title_element = item.find('div', class_='s-item__title')
                        title = ""
                        if title_element:
                            title_text = " ".join(span.get_text(strip=True) for span in title_element.find_all('span'))
                            title = re.sub(r'New Listing\s*', '', title_text).strip()
                        print(title)

                        price_span = item.find('span', class_='s-item__price')
                        price_text = price_span.get_text(strip=True).replace('$', '').replace(',', '').strip()
                        price = get_price(price_text)
                        link = item.find('a', class_='s-item__link')['href']

                        product_response = requests.get(link)
                        product_soup = BeautifulSoup(product_response.text, 'html.parser')


                        # Extract Image URL
                        image_container = product_soup.find('div', {'data-testid': 'ux-image-carousel-container'})
                        image_url = ""
                        if image_container:
                            image_element = image_container.find('div', {'data-idx': '0'})
                            if image_element:
                                img_tag = image_element.find('img')
                                if img_tag:
                                    image_url = img_tag['src']
                        else:
                            print("Image container not found.")
                        print(image_url)

                        # Initialize Buying Type
                        buying_type = "Buy It Now"  # Default to "Buy It Now"

                        # Check for Auction
                        if product_soup.find('div', {'data-testid': 'x-bid-action'}):
                            buying_type = "Auction"

                        # Fetch card details
                        sport_val = season_year = set_name = variation = player_name = card_number = grade = ""

                        # Extract specifications
                        specifications_section = product_soup.find('section', class_='product-spectification')
                        if specifications_section:
                            details = specifications_section.find_all('li')
                            for detail in details:
                                name = detail.find('div', class_='s-name')
                                value = detail.find('div', class_='s-value')
                                if name and value:
                                    name_text = name.get_text(strip=True)
                                    value_text = value.get_text(strip=True)
                                    if name_text == "Sport":
                                        sport_val = value_text
                                    elif name_text in ["Season", "Year"]:
                                        season_year = value_text
                                    elif name_text == "Set":
                                        set_name = clean_set_name(value_text)
                                    elif name_text == "Parallel/Variety":
                                        variation = value_text
                                    elif name_text in ["Player/Athlete", "Player"]:
                                        player_name = value_text
                                    elif name_text == "Card Number":
                                        card_number = value_text 
                                    elif name_text == "Grade":
                                        grade = value_text

                        # Alternatively, check another section for specifications
                        specifications_section_new = product_soup.find('div', {'data-testid': 'ux-layout-section-evo'})
                        if specifications_section_new:
                            details = specifications_section_new.find_all('dl')
                            for detail in details:
                                label = detail.find('dt').get_text(strip=True) if detail.find('dt') else ""
                                value = detail.find('dd').get_text(strip=True) if detail.find('dd') else ""

                                if label == "Sport":
                                    sport_val = value
                                elif label in ["Season", "Year"]:
                                    season_year = value
                                elif label == "Set":
                                    set_name = clean_set_name(value)
                                elif label == "Parallel/Variety":
                                    variation = value
                                elif label in ["Player/Athlete", "Player"]:
                                    player_name = value
                                elif label == "Card Number":
                                    card_number = value
                                elif label == "Grade":
                                    grade = value

                        # Fetch price data
                        print(price)
                        min_price, max_price, avg_price, median_price, compared_items = fetch_price_data(title, buying_type, price)

                        undervalued_status = ""
                        if min_price > 0 and avg_price > 0 and median_price > 0:
                            if price < 0.8 * median_price:
                                undervalued_status = "Undervalued"
                        print(price, min_price, max_price, avg_price, median_price, compared_items, undervalued_status)
                        print("-------------------------------------------------------------")

                        data.append({
                            "Title": title,
                            "Buying Type": buying_type,
                            "Sport": sport_val,
                            "Season Year": season_year,
                            "Set": set_name,
                            "Variation": variation,
                            "Player Name": player_name,
                            "Price": f"${price}",
                            "Card Number": card_number,
                            "Grade": grade,
                            "Card Link": link,
                            "Listing Date": today_date_str,  # Format as needed
                            "Ending Date": end_date_text,
                            "Image URL": image_url,
                            "Min": f"${min_price}",
                            "Max": f"${max_price}",
                            "Average": f"${avg_price:.2f}",
                            "Median": f"${median_price}",
                            "Compared Items": compared_items,
                            "Undervalued Status": undervalued_status
                        })
                elif end_datetime > tomorrow_8pm:
                    print('limit date')
                    break
                else:
                    print("Not match")
        # # Save the collected data for the current page
        # df = pd.DataFrame(data)
        # page_filename = os.path.join(output_dir, f"New_Data_Page_{page}.xlsx")
        # df.to_excel(page_filename, index=False)
        # print(f"New Data - Page {page} saved to '{page_filename}'.")
        if end_datetime > tomorrow_8pm:
            print('limit date')
            break
        page_end_time = time.time()
        page_duration = page_end_time - page_start_time
        print(f"Time taken for page {page}: {page_duration:.2f} seconds")

        # If items_count is less than 240, exit the loop after this page
        # if items_count < 240:
        #     print(f"Less than 240 items found on page {page}. Ending data collection.")
        #     break

        page += 1

except KeyboardInterrupt:
    print(f"\nData collection interrupted. Saving collected data...")

undervalued_cards = [card for card in data if card.get('Undervalued Status') == 'Undervalued']

if undervalued_cards:
    send_email(undervalued_cards)
    print(f"Email sent with {len(undervalued_cards)} undervalued cards.")
else:
    print("No undervalued cards found.")


# Save final collected data for the sport
df_final = pd.DataFrame(data)
final_filename = os.path.join(output_dir, f"{today_date_str}.xlsx")
df_final.to_excel(final_filename, index=False)
print(f"New Data saved to '{final_filename}'.")

# End timer
end_time = time.time()
execution_time = end_time - start_time
print(f"Total Execution Time: {execution_time:.2f} seconds")