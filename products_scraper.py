from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import csv, time, os, re, requests
from urllib.parse import urljoin

BASE_URL = "https://grambahar.com"
PRODUCTS_PAGE = "https://grambahar.com/products"
OUTPUT_DIR = "output"
MAX_PRODUCTS = 8

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
    m = re.search(r"(\d+)\s*(kg|gm)", text.lower())
    if not m:
        return 0
    v, u = m.groups()
    return int(v) * 1000 if u == "kg" else int(v)

# ------------------ STEP 1: OPEN PRODUCTS PAGE ------------------
print("🔍 Collecting product URLs...")
driver.get(PRODUCTS_PAGE)
time.sleep(4)

links = driver.find_elements(By.XPATH, "//a[contains(@href,'/products/')]")
product_urls = []

for a in links:
    href = a.get_attribute("href")
    if href and "/products/" in href:
        if href not in product_urls:
            product_urls.append(href)
    if len(product_urls) == MAX_PRODUCTS:
        break

print(f"✅ Collected {len(product_urls)} product URLs")

# ------------------ LOGO + CONTACT ------------------
driver.get(BASE_URL)
time.sleep(3)

# Logo
try:
    logo = driver.find_element(By.XPATH, "//img[contains(@alt,'Logo')]")
    logo_url = logo.get_attribute("src")
    logo_data = requests.get(logo_url).content
    with open(f"{OUTPUT_DIR}/logo.png", "wb") as f:
        f.write(logo_data)
except:
    print("⚠️ Logo not found")

# Contact info
body_text = driver.find_element(By.TAG_NAME, "body").text
emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", body_text))
phones = set(re.findall(r"\+91[-\s]?\d{10}|\b\d{10}\b", body_text))

# ------------------ STEP 2: SCRAPE PRODUCTS ------------------
rows = []

for url in product_urls:
    driver.get(url)
    time.sleep(3)

    try:
        main = wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
        name = main.find_element(By.TAG_NAME, "h1").text.strip()

        btns = main.find_elements(By.XPATH, ".//button[.//span[contains(text(),'gm')]]")
        spans = btns[0].find_elements(By.TAG_NAME, "span")

        variant = spans[0].text.strip()
        mrp = float(spans[1].text.replace("₹","").replace(",",""))
        price = float(spans[2].text.replace("₹","").replace(",",""))

        gm = parse_weight(variant)
        kg = round(gm / 1000, 2)
        perkg = round(price / kg, 2) if kg else 0

        rows.append([
            name, variant, gm, kg, price, mrp, perkg, url
        ])

        print("✅ Scraped:", name)

    except Exception as e:
        print("❌ Failed:", url, e)

driver.quit()

# ------------------ SAVE CSVs ------------------
with open(f"{OUTPUT_DIR}/product_variants.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow([
        "Product Name","Variant","Weight (gm)","Weight (kg)",
        "Selling Price (₹)","Original Price (₹)",
        "Price per kg (₹)","Product URL"
    ])
    w.writerows(rows)

with open(f"{OUTPUT_DIR}/contact_info.csv","w",newline="",encoding="utf-8") as f:
    csv.writer(f).writerow(["Grambahar", ", ".join(emails), ", ".join(phones)])

print("\n🎉 DONE: Website → Products → CSV")
