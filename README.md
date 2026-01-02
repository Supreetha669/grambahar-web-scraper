# Grambahar Web Scraper

This project is a **Python Selenium-based web scraper** that extracts **product details, website logo, and contact information** from the Grambahar website:

🔗 https://grambahar.com

The website is built using **Next.js / React**, so Selenium is used to handle dynamic, JavaScript-rendered content.

---

##  Features

###  Product Details Extraction
The scraper extracts **variant-level product information**, including:

- Product Name  
- Variant (e.g. `700gm`, `1.4kg + 1.5kg`)  
- Weight (grams & kilograms)  
- Selling Price (₹)  
- Original Price (₹)  
- Price per kilogram (calculated)

Each product variant is saved as a **separate row**, and duplicates are automatically removed.

---

###  Logo Extraction
- Identifies the official website logo from the header  
- Decodes Next.js optimized image URLs  
- Downloads and saves the **actual logo image** as `logo.png`

---

### Contact Information
- Extracts **email addresses** and **phone numbers** visible on the website  
- Uses regex-based text parsing on rendered page content  

---

##  Project Structure
grambahar_web_scraper/
│
├── products_scraper.py
├── README.md
├── requirements.txt
│
└── output/
├── product_variants.csv
├── site_logo.csv
├── contact_info.csv
└── logo.png


---

## 📄 Output Files

### 1️ `product_variants.csv`
Contains product and variant-level details.

**Columns:**
- Product Name  
- Variant  
- Weight (gm)  
- Weight (kg)  
- Selling Price (₹)  
- Original Price (₹)  
- Price per kg (₹)

---

### 2️ `site_logo.csv`
Stores reference to the downloaded logo image.

### 3️ `contact_info.csv`
Stores extracted contact details (if publicly available).


---

## 🛠 Technologies Used

- Python 3  
- Selenium  
- WebDriver Manager  
- Requests  
- Regular Expressions (regex)  
- CSV handling  

---

##  How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt


---

##  Technologies Used

- Python 3  
- Selenium  
- WebDriver Manager  
- Requests  
- Regular Expressions (regex)  
- CSV handling  

---

. Run the scraper
python products_scraper.py

3. View results

All output files will be created inside the output/ directory.

