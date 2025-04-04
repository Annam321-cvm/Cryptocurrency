from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import pymongo
import pytz
import os
from datetime import datetime

# Check if running in GitHub Actions (use default Chrome)
is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"

if is_github_actions:
    chrome_driver_path = "chromedriver"  # Use default ChromeDriver in GitHub
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode in GitHub
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(chrome_driver_path)
else:
    # Local execution with Brave Browser
    brave_path = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    chrome_driver_path = r"C:\Users\harsh\Downloads\chromedriver-win64\chromedriver.exe"

    options = webdriver.ChromeOptions()
    options.binary_location = brave_path
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(chrome_driver_path)

# Initialize WebDriver
driver = webdriver.Chrome(service=service, options=options)

# Open the Crypto.com price page
url = "https://crypto.com/price"
driver.get(url)

# Wait for the table to load
try:
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
    )
    print("Page loaded successfully")
except:
    print("Timeout: Page did not load properly")
    driver.quit()

# Locate table rows
rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")

data = []
for index, row in enumerate(rows):
    try:
        name = row.find_element(By.CSS_SELECTOR, "td div div p").text.strip()  # New selector
        price = row.find_element(By.CSS_SELECTOR, "td:nth-child(3)").text.strip()
        change = row.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.strip()
        volume = row.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.strip()
        market_cap = row.find_element(By.CSS_SELECTOR, "td:nth-child(6)").text.strip()

        data.append({
            "Name": name,
            "Symbol": price,
            "Price": change,
            "24H Change": volume,
            "24H Volume": market_cap,
            "Scraped_At_UTC": datetime.now(pytz.utc)
        })

        print(f" Row {index+1} extracted: {name} - {price}")

    except Exception as e:
        print(f" Skipped Row {index+1} due to error: {e}")
        continue  # Skip problematic rows

# Close the browser
driver.quit()

# Save to CSV
df = pd.DataFrame(data)
if not df.empty:
    df.to_csv("crypto_prices.csv", index=False)
    print("Data saved to 'crypto_prices.csv'")
else:
    print("No data found to save in CSV.")

# Save to MongoDB Atlas
try:
    if data:
        mongo_uri = os.getenv("MONGO_URI")  # Load from GitHub Secrets
        client = pymongo.MongoClient(mongo_uri)
        db = client["crypto_db"]
        collection = db["crypto_prices"]
        collection.insert_many(data)
        print("Data inserted into MongoDB Atlas")
    else:
        print("No data found to insert into MongoDB.")
except Exception as mongo_err:
    print(f" MongoDB error: {mongo_err}")
