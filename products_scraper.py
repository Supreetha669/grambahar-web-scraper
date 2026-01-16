from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import csv, time, os, re

BASE_URL = "https://grambahar.com"
OUTPUT_DIR = "output"
MAX_PRODUCTS = 100

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------ DRIVER SETUP ------------------
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)
wait = WebDriverWait(driver, 20)


# ------------------ HELPERS ------------------
def parse_weight(text):
    """Extract weight in grams from text."""
    if not text: return 0
    # Improved regex to handle spaces and various units
    m = re.search(r"(\d+(\.\d+)?)\s*(kg|gm|g|kilogram|gram)", text.lower())
    if not m:
        return 0
    v = float(m.group(1))
    unit = m.group(3)
    if unit in ["kg", "kilogram"]:
        return v * 1000.0
    return v


def to_number(text):
    """Clean currency text and convert to float."""
    # Remove non-numeric except decimal point
    clean_text = re.sub(r'[^\d.]', '', text.strip())
    try:
        return float(clean_text) if clean_text else 0.0
    except ValueError:
        return 0.0


# ------------------ COLLECT PRODUCT LINKS ------------------
print(f"🔍 Accessing {BASE_URL}...")
driver.get(BASE_URL)
time.sleep(5)

product_urls = set()

# Strategy 1: Find all internal product links
anchors = driver.find_elements(By.XPATH, "//a[contains(@href, '/products/')]")
for a in anchors:
    href = a.get_attribute("href")
    if href:
        # Normalize URL (remove query params)
        clean_href = href.split('?')[0]
        product_urls.add(clean_href)

product_urls = list(product_urls)[:MAX_PRODUCTS]
print(f"✅ Found {len(product_urls)} unique product URLs")

# ------------------ SCRAPE EACH PRODUCT PAGE ------------------
rows = []

for url in product_urls:
    try:
        driver.get(url)
        time.sleep(2)  # Slight delay for dynamic pricing to load

        # Try to find the main container or body
        try:
            main = wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        except:
            main = driver.find_element(By.TAG_NAME, "body")

        # 1. Product Name
        try:
            name = main.find_element(By.XPATH, ".//h1").text.strip()
        except:
            name = driver.title.split('-')[0].strip()

        # 2. Variant / Weight
        variant_text = ""
        # Look for buttons or labels containing weight units
        weight_patterns = [
            ".//button[contains(translate(., 'KMG', 'kmg'), 'gm') or contains(translate(., 'KMG', 'kmg'), 'kg')]",
            ".//option[contains(., 'gm') or contains(., 'kg')]",
            ".//*[contains(@class, 'active') or contains(@class, 'selected')]//*[contains(text(), 'g')]"
        ]

        for xpath in weight_patterns:
            try:
                el = main.find_element(By.XPATH, xpath)
                variant_text = el.text.strip()
                if variant_text: break
            except:
                continue

        grams = parse_weight(variant_text)
        kg = round(grams / 1000.0, 3) if grams else 0.0

        # 3. Prices
        # Find elements that look like prices (usually contain currency symbol)
        price_elements = main.find_elements(By.XPATH, "//*[contains(text(), '₹')]")
        prices_found = []
        for p in price_elements:
            val = to_number(p.text)
            if val > 0: prices_found.append(val)

        # Deduplicate and sort: Highest is likely MRP, Lowest is Selling Price
        prices_found = sorted(list(set(prices_found)), reverse=True)

        mrp = prices_found[0] if len(prices_found) > 0 else 0.0
        price = prices_found[-1] if len(prices_found) > 0 else 0.0

        perkg = round(price / kg, 2) if kg > 0 else 0.0

        rows.append([name, variant_text, grams, kg, price, mrp, perkg, url])
        print(f"✅ Scraped: {name} | Price: ₹{price}")

    except Exception as e:
        print(f"❌ Error on {url}: {e}")

# ------------------ SCRAPE LOGO + CONTACT ------------------
driver.get(BASE_URL)
time.sleep(3)

logo_url = ""
try:
    # Broad search for logo images
    logo_el = driver.find_element(By.XPATH,
                                  "//img[contains(@class, 'logo') or contains(@src, 'logo') or contains(@alt, 'Logo')]")
    logo_url = logo_el.get_attribute("src")
except:
    print("⚠️ Logo not found")

body_text = driver.find_element(By.TAG_NAME, "body").text
emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", body_text))
phones = set(re.findall(r"(?:\+91|0)?\s?\d{10,12}", body_text))

driver.quit()


# ------------------ SAVE CSVs ------------------
def save_csv(filename, header, data):
    with open(f"{OUTPUT_DIR}/{filename}", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        if isinstance(data[0], list):
            w.writerows(data)
        else:
            w.writerow(data)


save_csv("product_variants.csv",
         ["Product Name", "Variant", "Weight (gm)", "Weight (kg)", "Selling Price (₹)", "Original Price (₹)",
          "Price per kg (₹)", "Product URL"],
         rows)

save_csv("contact_info.csv",
         ["Brand Name", "Emails", "Phones"],
         ["Grambahar", ", ".join(emails), ", ".join(phones)])

save_csv("sitelogo.csv",
         ["Brand Name", "Logo URL"],
         ["Grambahar", logo_url])

print(f"\n🎉 Extraction Complete. Check the '{OUTPUT_DIR}' folder.")