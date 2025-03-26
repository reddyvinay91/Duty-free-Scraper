#!/usr/bin/env python

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from bs4 import BeautifulSoup

def main():
    # 1. Set up Selenium options and initialize the driver
    chrome_options = Options()
    # Uncomment this line to run headless (without an open browser window)
    # chrome_options.add_argument("--headless")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 20)
    
    # 2. Open the main King Power duty-free page
    url = "https://www.kingpower.com/en/collection/duty-free"
    driver.get(url)
    time.sleep(3)  # Allow the page to load
    
    # 3. Locate the section tabs
    section_tabs = driver.find_elements(By.CSS_SELECTOR, "nav.tw-kp-container-navigation ul.tw-list-none li a")
    print("Found", len(section_tabs), "section tabs.")
    
    if len(section_tabs) == 0:
        print("No section tabs found! Please inspect the nav element and update the selector.")
    
    all_products = []  # To store scraped product data
    
    # 4. Loop through each section tab
    for i in range(len(section_tabs)):
        section_tabs = driver.find_elements(By.CSS_SELECTOR, "nav.tw-kp-container-navigation ul.tw-list-none li a")
        if i >= len(section_tabs):
            break
        
        current_tab = section_tabs[i]
        section_name = current_tab.text.strip()
        print("\nProcessing section:", section_name)
        
        try:
            current_tab.click()
        except Exception as e:
            print(f"Error clicking section '{section_name}':", e)
            continue
        
        try:
            sub_sections = driver.find_elements(By.CSS_SELECTOR, "ul.sub-section-nav li a")
            if sub_sections:
                print("Found sub-sections. Clicking the first one.")
                try:
                    sub_sections[0].click()
                    time.sleep(2)
                except Exception as sub_e:
                    print("Error clicking sub-section:", sub_e)
        except Exception as e:
            print("No sub-sections found or error:", e)
        
        # 5. Wait for products to load
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-item")))
        except Exception as e:
            print(f"Product list not loaded for section '{section_name}':", e)
            continue
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        
        # 6. Loop for pagination
        while True:
            time.sleep(2)
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            
            product_cards = soup.select("div.product-item")
            if not product_cards:
                print(f"No products found on this page in section '{section_name}'.")
                break
            
            print(f"Found {len(product_cards)} products in section '{section_name}' on this page.")
            
            for card in product_cards:
                try:
                    product_name = card.select_one("a.product-title").get_text(strip=True) if card.select_one("a.product-title") else None
                    product_url = card.select_one("a.product-title")["href"] if card.select_one("a.product-title") else None
                    product_image = card.select_one("img")["src"] if card.select_one("img") else None
                    original_price = card.select_one("span.original-price").get_text(strip=True) if card.select_one("span.original-price") else None
                    discounted_price = card.select_one("span.discounted-price").get_text(strip=True) if card.select_one("span.discounted-price") else None
                    discount_text = card.select_one("div.offer").get_text(strip=True) if card.select_one("div.offer") else None
                    brand_name = card.select_one("span.brand-name").get_text(strip=True) if card.select_one("span.brand-name") else None
                    
                    options_elements = card.select("ul.options li")
                    options = ", ".join([elem.get_text(strip=True) for elem in options_elements]) if options_elements else None
                    
                    all_products.append({
                        "Section": section_name,
                        "Product Name": product_name,
                        "Product URL": product_url,
                        "Product Image": product_image,
                        "Original Price": original_price,
                        "Discounted Price": discounted_price,
                        "Discount/Offer Text": discount_text,
                        "Brand Name": brand_name,
                        "Different Options": options
                    })
                except Exception as err:
                    print("Error processing a product card:", err)
                    continue
            
            # 7. Try to click the "Next" button
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "a.pagination-next")
                driver.execute_script("arguments[0].scrollIntoView();", next_btn)
                time.sleep(1)
                next_btn.click()
                wait.until(EC.staleness_of(next_btn))
                time.sleep(2)
            except Exception as e:
                print(f"No further pages in section '{section_name}', moving on.")
                break
    
    driver.quit()
    
    # 8. Save the collected data
    df = pd.DataFrame(all_products)
    output_path = "data/products.xlsx"
    df.to_excel(output_path, index=False)
    print("\nScraping completed. Data saved to", output_path)

if __name__ == "__main__":
    main()
