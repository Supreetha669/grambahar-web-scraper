from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import csv
import sys   # 👈 added

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "API is running"}

@app.get("/products")
def get_products():
    products = []
    with open("output/product_variants.csv", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row)
    return {"products": products}

# ✅ FIXED ENDPOINT
@app.post("/scrape")
def scrape_products():
    result = subprocess.run(
        [sys.executable, "products_scraper.py"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {
            "status": "failed",
            "stdout": result.stdout,
            "stderr": result.stderr
        }

    return {
        "status": "success",
        "stdout": result.stdout
    }
