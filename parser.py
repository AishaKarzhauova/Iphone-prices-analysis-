from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import re
import dateparser
from datetime import datetime


class ParserOLX:
    def __init__(self):
        self.driver = webdriver.Chrome()

    def _parse_title(self, ad):
        try:
            # Locate the <a> tag with class `css-q0o6xu` and extract its text
            title_element = ad.find("h4", class_="css-1s3qyje")
            return title_element.text.strip() if title_element else "No title found"
        except Exception as e:
            print(f"Error parsing title: {e}")
            return "Error extracting title"

    def _parse_is_bargain(self, ad):
        price_element = ad.find("p", {"data-testid": "ad-price"})
        price_text = price_element.text.strip() if price_element else ""

        if price_text:
            return "Договорная" in price_text

        return False

    def _parse_price(self, ad):
        price_element = ad.find("p", class_="css-13afqrm")
        price_text = price_element.text.strip() if price_element else ""

        digits_only = re.sub(r'\D', '', price_text)

        return float(digits_only) if digits_only else 0.0

    def _parse_location(self, ad):
        location_element = ad.find("p", {"data-testid": "location-date"})
        if location_element:
            # Split the text into location and possible date
            location_text = location_element.text.strip()
            if " - " in location_text:
                parts = location_text.split(" - ")
                city = parts[0].split(",")[0].strip()
                district = parts[0].split(",")[1].strip() if "," in parts[0] else ""
                return city, district
            else:
                city = location_text.split(",")[0].strip()
                district = location_text.split(",")[1].strip() if "," in location_text else ""
                return city, district
        return "Unknown", "Unknown"

    def _parse_date(self, ad):
        location_element = ad.find("p", {"data-testid": "location-date"})
        if location_element:
            location_text = location_element.text.strip().split("-")
            date_str = location_text[-1].strip()
            if "Сегодня" in date_str:
                return datetime.now().strftime("%Y-%m-%d")
            else:
                parsed_date = dateparser.parse(date_str)
                return parsed_date.strftime("%Y-%m-%d") if parsed_date else "Unknown"
        return "Unknown"

    def scrape_and_save_to_csv(self, URL, output_file):
        data = {
            "Title": [],
            "Price": [],
            "City": [],
            "Bargain": [],
            "Date": [],
            "District": []
        }

        while URL:
            self.driver.get(URL)
            content = self.driver.page_source
            soup = BeautifulSoup(content, 'html.parser')

            ads = soup.find_all("div", {"data-cy": "l-card"})

            for ad in ads:
                title = self._parse_title(ad)
                price = self._parse_price(ad)
                is_bargain = self._parse_is_bargain(ad)
                location = self._parse_location(ad)
                date = self._parse_date(ad)
                city = location[0]
                district = location[1]

                # Append data to the dictionary
                data["Title"].append(title)
                data["Price"].append(price)
                data["City"].append(city)
                data["Bargain"].append(is_bargain)
                data["Date"].append(date)
                data["District"].append(district)

            next_page_url = soup.find("a", {"data-testid": "pagination-forward"})

            if next_page_url:
                URL = "https://www.olx.kz" + next_page_url["href"]
            else:
                break

        self.driver.quit()

        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding="utf-8-sig")

        return df



URL = 'https://www.olx.kz/q-iphone/'
output_file = 'olx_iphone2.csv'

olx_parser = ParserOLX()
df = olx_parser.scrape_and_save_to_csv(URL, output_file)
