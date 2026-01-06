from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import csv
import re
import time
import os
import requests
from urllib.parse import urlparse, parse_qs, unquote

PRODUCT_URLS = [
    "https://grambahar.com/products/jaggery-combo-pack-of-4-2900-gm",
    "https://grambahar.com/products/jaggery-combo-pack-of-2-1450-gm",
    "https://grambahar.com/products/nolen-gur-pack-of-4-3000g",
    "https://grambahar.com/products/nolen-gur-pack-of-2-1500g",
    "https://grambahar.com/products/nolen-gur",
    "https://grambahar.com/products/patali-gur-pack-of-2-1400g",
    "https://grambahar.com/products/patali-gur-pack-of-4-2800g",
    "https://grambahar.com/products/patali-gur-pack-of-1-700-g"
]

os.makedirs("output", exist_ok=True)

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")


driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 20)

product_rows = []
emails = []
phones = []

def parse_weight_to_grams(text):
    matches = re.findall(r"(\d+(\.\d+)?)\s*(kg|gm)", text.lower())
    total = 0
    for value, _, unit in matches:
        value = float(value)
        total += value * 1000 if unit == "kg" else value
    return int(total)

# --------------------------------------------------
# LOAD FIRST PAGE (FOR LOGO + CONTACT)
# --------------------------------------------------
driver.get(PRODUCT_URLS[0])
time.sleep(3)

# -------- LOGO IMAGE DOWNLOAD --------
# Absolute output directory (define once at top of file)
BASE_OUTPUT_DIR = os.path.join(os.getcwd(), "output")
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)


logo_file_name = "logo.png"
logo_path = os.path.join(BASE_OUTPUT_DIR, logo_file_name)

try:
    logo_img = driver.find_element(
        By.XPATH, "//img[contains(@alt,'Logo') or contains(@title,'Logo')]"
    )

    src = logo_img.get_attribute("src")

    # Handle Next.js optimized image URL
    if "_next/image" in src:
        parsed = urlparse(src)
        real_path = unquote(parse_qs(parsed.query)["url"][0])
        logo_url = "https://grambahar.com" + real_path
    else:
        logo_url = src if src.startswith("http") else "https://grambahar.com" + src

    response = requests.get(logo_url, timeout=20)
    response.raise_for_status()

    with open(logo_path, "wb") as f:
        f.write(response.content)

    print("Logo image saved:", logo_path)

except Exception as e:
    print("Logo extraction failed:", e)


# -------- CONTACT INFO --------
page_text = driver.find_element(By.TAG_NAME, "body").text

emails = list(set(re.findall(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", page_text
)))

phones = list(set(re.findall(
    r"(\+91[-\s]?\d{10}|\b\d{10}\b)", page_text
)))

# --------------------------------------------------
# PRODUCT SCRAPING
# --------------------------------------------------
# --------------------------------------------------
# PRODUCT SCRAPING (EXACTLY 8 PRODUCTS)
# --------------------------------------------------
for url in PRODUCT_URLS:
    driver.get(url)
    time.sleep(4)

    try:
        main = wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/main'))
        )

        # Product name
        product_name = main.find_element(By.TAG_NAME, "h1").text.strip()

        # Variant buttons
        variant_buttons = main.find_elements(
            By.XPATH, ".//button[.//span[contains(text(),'gm') or contains(text(),'kg')]]"
        )

        if not variant_buttons:
            print("❌ No variants found:", url)
            continue

        # ✅ TAKE ONLY FIRST VARIANT
        spans = variant_buttons[0].find_elements(By.TAG_NAME, "span")

        if len(spans) < 3:
            print("❌ Invalid variant data:", url)
            continue

        variant = spans[0].text.strip()
        original_price = float(
            spans[1].text.replace("₹", "").replace(",", "").strip()
        )
        selling_price = float(
            spans[2].text.replace("₹", "").replace(",", "").strip()
        )

        weight_gm = parse_weight_to_grams(variant)
        weight_kg = round(weight_gm / 1000, 3)

        price_per_kg = round(
            selling_price / weight_kg, 2
        ) if weight_kg > 0 else 0

        product_rows.append([
            product_name,
            variant,
            weight_gm,
            weight_kg,
            selling_price,
            original_price,
            price_per_kg,
            url
        ])

        print("✅ Added product:", product_name)

    except Exception as e:
        print("❌ Failed:", url, e)

# --------------------------------------------------
# SAVE CSV FILES
# --------------------------------------------------

with open("output/product_variants.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Product Name",
        "Variant",
        "Weight (gm)",
        "Weight (kg)",
        "Selling Price (₹)",
        "Original Price (₹)",
        "Price per kg (₹)",
        "Product URL"
    ])

    writer.writerows(product_rows)

site_logo_path = os.path.join("output", "site_logo.csv")

with open(site_logo_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Website", "Logo File"])
    writer.writerow(["Grambahar", logo_file_name])



with open("output/contact_info.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Website", "Emails", "Phone Numbers"])
    writer.writerow([
        "Grambahar",
        ", ".join(emails),
        ", ".join(phones)
    ])

print("\nSUCCESS: All CSV files and logo image created")
