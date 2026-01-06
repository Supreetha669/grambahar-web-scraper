from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Product(BaseModel):
    product_name: str
    product_url: str

@app.get("/")
def root():
    return {"status": "Grambahar API running"}

@app.post("/api/products")
def receive_product(product: Product):
    return {
        "message": "Product received successfully",
        "data": product
    }
