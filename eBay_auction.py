import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import threading
import os

# Define the base URL template
base_url = "https://www.ebay.com/sch/i.html?_dcat=212&_udlo=100&_fsrp=1&_from=R40&Sport={}&_nkw=PSA&_sacat=64482&Grade=8%7C8%252E5%7C9%7C9%252E5%7C10%7C%21&Season=2020%7C2020%252D21%7C2021%7C2021%252D22%7C2022%7C2022%252D23%7C2023%7C2023%252D24%7C2024%7C2025&LH_Auction=1&_sop=10&_ipg=240&_pgn={}"

sports = ["Baseball", "Basketball", "Football"]

start_time = time.time()

def clean_set_name(set_name):
    return re.sub(r'^\d{4}(-\d{2})?\s*', '', set_name).strip()

def print_elapsed_time():
    while True:
        elapsed_time = time.time() - start_time
        print(f"Total Elapsed Time: {elapsed_time:.2f} seconds", end='\r')
        time.sleep(1)  # Update every second

elapsed_time_thread = threading.Thread(target=print_elapsed_time, daemon=True)
elapsed_time_thread.start()

# Loop over the sports and scrape each one sequentially
for sport_name in sports:
    print(f"\nScraping Sport: {sport_name}")
    
    # Ensure the directory exists for the current sport
    output_dir = os.path.join("Auction", sport_name)
    os.makedirs(output_dir, exist_ok=True)

    page = 1
    data = []

    try:
        while True:
            print(f"Scraping {sport_name} - Page {page}")
            page_start_time = time.time()
            url = base_url.format(sport_name, page)
            response = requests.get(url)

            if response.status_code != 200:
                print(f"Failed to retrieve {sport_name} page {page}: {response.status_code}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            items_container = soup.find('div', id='srp-river-results')
            items = items_container.find_all("li", attrs={"data-view": re.compile(r"^mi:1686\|iid:(\d+)$")})
            items_count = len(items)

            print(f"Auction items found on page {page}: {items_count}")

            for item in items:
                title_element = item.find('div', class_='s-item__title')
                title = ""
                if title_element:
                    title_text = " ".join(span.get_text(strip=True) for span in title_element.find_all('span'))
                    title = re.sub(r'New Listing\s*', '', title_text).strip()

                price_span = item.find('span', class_='s-item__price')
                price = price_span.get_text(strip=True) if price_span else "N/A"
                
                link = item.find('a', class_='s-item__link')['href']
                product_response = requests.get(link)
                product_soup = BeautifulSoup(product_response.text, 'html.parser')

                sport_val = season_year = set_name = variation = player_name = card_number = grade = ""

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

                data.append({
                    "Title": title,
                    "Sport": sport_val,
                    "Season Year": season_year,
                    "Set": set_name,
                    "Variation": variation,
                    "Player Name": player_name,
                    "Price": price,
                    "Card Number": card_number,
                    "Grade": grade,
                    "Card Link": link
                })

            # Save the collected data for the current page
            df = pd.DataFrame(data)
            page_filename = os.path.join(output_dir, f"{sport_name}_Auction_Data_Page_{page}.xlsx")
            df.to_excel(page_filename, index=False)
            print(f"Data for {sport_name} - Page {page} saved to '{page_filename}'.")

            page_end_time = time.time()
            page_duration = page_end_time - page_start_time
            print(f"Time taken for {sport_name} page {page}: {page_duration:.2f} seconds")

            if items_count < 240:
                print(f"Less than 240 items found on page {page}. Moving to next sport.")
                break

            page += 1

    except KeyboardInterrupt:
        print(f"\nData collection for {sport_name} interrupted. Saving collected data...")

    # Save final collected data for the sport
    df_final = pd.DataFrame(data)
    final_filename = os.path.join(output_dir, f"{sport_name}_Auction_Data.xlsx")
    df_final.to_excel(final_filename, index=False)
    print(f"Auction data for {sport_name} saved to '{final_filename}'.")

# End timer
end_time = time.time()
execution_time = end_time - start_time
print(f"Total Execution Time: {execution_time:.2f} seconds")
