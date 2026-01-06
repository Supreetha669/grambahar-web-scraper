from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import csv, time, os, re

BASE_URL = "https://grambahar.com"
HOME_URL = BASE_URL              # start from home
OUTPUT_DIR = "output"
MAX_PRODUCTS = 100               # change as needed

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
    """
    Extract weight in grams from text like '700gm', '1kg', '1.4kg', '700 g'.
    """
    m = re.search(r"(\d+(\.\d+)?)\s*(kg|gm|g)", text.lower())
    if not m:
        return 0
    v = float(m.group(1))
    unit = m.group(3)
    if unit == "kg":
        return v * 1000.0
    return v  # gm or g

def to_number(text):
    text = text.replace("₹", "").replace(",", "").strip()
    return float(text) if text else 0.0

# ------------------ COLLECT PRODUCT LINKS ------------------
print("🔍 Collecting product links from site...")
driver.get(HOME_URL)
time.sleep(4)

product_urls = set()

# 1) anchors that look like product links (contain '/products/')
anchors = driver.find_elements(By.XPATH, "//a[contains(@href, '/products/')]")
for a in anchors:
    href = a.get_attribute("href")
    if href and "/products/" in href:
        product_urls.add(href)

# 2) optionally, follow a generic 'Shop/Products/Collections' link if present
try:
    collections_link = driver.find_element(
        By.XPATH,
        "//a[contains(@href, '/collections') or " +
        "contains(translate(., 'SHOP', 'shop'), 'shop') or " +
        "contains(translate(., 'PRODUCT', 'product'), 'product')]"
    )
    collections_url = collections_link.get_attribute("href")
    if collections_url:
        driver.get(collections_url)
        time.sleep(4)
        more_anchors = driver.find_elements(By.XPATH, "//a[contains(@href, '/products/')]")
        for a in more_anchors:
            href = a.get_attribute("href")
            if href and "/products/" in href:
                product_urls.add(href)
except:
    pass

product_urls = list(product_urls)[:MAX_PRODUCTS]
print(f"✅ Found {len(product_urls)} product URLs automatically")

# ------------------ SCRAPE EACH PRODUCT PAGE ------------------
rows = []

for url in product_urls:
    try:
        driver.get(url)
        time.sleep(3)

        main = wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))

        # product name (h1 or h2 inside main)
        name_el = main.find_element(By.XPATH, ".//h1 | .//h2")
        name = name_el.text.strip()

        # variant / weight text
        variant_text = ""
        try:
            # common pattern: variant button with gm/kg
            variant_btn = main.find_element(
                By.XPATH,
                ".//button[contains(., 'gm') or contains(., 'kg') or contains(., 'g')]"
            )
            variant_text = variant_btn.text.strip()
        except:
            try:
                # fallback: any element containing gm/kg text
                size_el = main.find_element(
                    By.XPATH,
                    ".//*[contains(text(),'gm') or contains(text(),'kg') or contains(text(),'g')]"
                )
                variant_text = size_el.text.strip()
            except:
                variant_text = ""

        grams = parse_weight(variant_text)
        kg = round(grams / 1000.0, 3) if grams else 0.0

        # prices
        mrp, price = 0.0, 0.0
        price_elements = main.find_elements(By.XPATH, ".//*[contains(text(),'₹')]")

        if price_elements:
            # assume first is MRP, last is selling price
            mrp = to_number(price_elements[0].text)
            price = to_number(price_elements[-1].text)
        else:
            mrp = price = 0.0

        if not price and mrp:
            price = mrp

        perkg = round(price / kg, 2) if kg else 0.0

        rows.append([
            name,
            variant_text,
            grams,
            kg,
            price,
            mrp,
            perkg,
            url
        ])
        print("✅ Scraped:", name)
    except Exception as e:
        print("❌ Failed:", url, e)

# ------------------ SCRAPE LOGO + CONTACT FROM HOME ------------------
driver.get(BASE_URL)
time.sleep(3)

# Logo URL only (for sitelogo.csv)
logo_url = ""
try:
    logo = driver.find_element(
        By.XPATH,
        "//img[contains(@alt,'Logo') or contains(@src, 'logo')]"
    )
    logo_url = logo.get_attribute("src") or ""
except:
    print("⚠️ Logo not found")

# Contact info from full body text
body_text = driver.find_element(By.TAG_NAME, "body").text
emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", body_text))
phones = set(re.findall(r"\+91[-\s]?\d{10}|\b\d{10}\b", body_text))

driver.quit()

# ------------------ SAVE CSVs ------------------
# Products
with open(f"{OUTPUT_DIR}/product_variants.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow([
        "Product Name",
        "Variant",
        "Weight (gm)",
        "Weight (kg)",
        "Selling Price (₹)",
        "Original Price (₹)",
        "Price per kg (₹)",
        "Product URL"
    ])
    w.writerows(rows)

# Contact info (if you still want it)
with open(f"{OUTPUT_DIR}/contact_info.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Brand Name", "Emails", "Phones"])
    w.writerow(["Grambahar", ", ".join(emails), ", ".join(phones)])

# Site logo CSV with only logo URL
with open(f"{OUTPUT_DIR}/sitelogo.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Brand Name", "Logo URL"])
    w.writerow(["Grambahar", logo_url])

print("\n🎉 DONE: Products + contact_info.csv + sitelogo.csv (logo URL only)")
