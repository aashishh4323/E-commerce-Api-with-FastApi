import json
import uuid
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi import FastAPI, HTTPException, Query, Path ,Depends , Request
from app.service.product import get_all_products,load_products , change_product , add_product , delete_product
from app.schema.product import Product , ProductUpdate
from uuid import uuid4 , UUID
from datetime import datetime
from typing import List, Dict
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=env_path)

print("ENV PATH:", env_path)
print("BASE_URL:", os.getenv("BASE_URL"))  


app= FastAPI()




@app.middleware("http")
async def lifecycle(request, call_next):
    print("Before request")
    response = await call_next(request)
    print("After request")
    return response

def common_logic():
    print("Executing common logic for multiple endpoints...")
    return {"message": "This is a common logic function that can be reused across multiple endpoints."}


@app.get("/")
def root(dep: Dict = Depends(common_logic)):
    DB_PATH = os.getenv("BASE_URL")
    print("DB_PATH:", DB_PATH)  # DEBUG
    return JSONResponse(content={"message": "Welcome to the FastAPI E-commerce API!", "db_path": DB_PATH, **dep}, status_code=200)

@app.get("/products",response_model=Dict)

def list_products(
    dep=Depends(load_products),
    name: str = Query(
        default=None,
        min_length=3,
        max_length=50,
        description="Search product by name"
    ),
    sort_by_price: bool = Query(False),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):

    products =dep

    # filtering
    if name:
        needle = name.strip().lower()
        products = [
            p for p in products if needle in p.get("name", "").lower()
        ]

    if not products:
        raise HTTPException(status_code=404, detail="No products found")

    # sorting
    if sort_by_price:
        reverse = order == "desc"
        products.sort(key=lambda p: p.get("price", 0), reverse=reverse)

    total = len(products)

    # pagination
    products = products[offset:offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "products": products
    }


@app.get("/products/{product_id}",response_model = Dict)
def get_product_by_id(

    product_id: str = Path(..., min_length=36, max_length=36)
):
    products = get_all_products()

    for product in products:
        if product.get("id") == product_id:
            return product

    raise HTTPException(status_code=404, detail="Product not found")


@app.post("/products", status_code=201)
def create_product(product: Product):
    product_dict = product.model_dump(mode="json")
    product_dict["id"] = str(uuid.uuid4())
    product_dict["created_at"] = datetime.utcnow().isoformat() + "Z"
    try:
        added_product = add_product(product_dict)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return product.model_dump(mode="json")


@app.delete("/products/{product_id}")
def delete_product_by_id(
    product_id: str = Path(..., min_length=36, max_length=36)
):
    try:
        result = delete_product(product_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": f"Product with ID {product_id} has been deleted."}



@app.patch("/products/{product_id}")
def update_product(
    product_id: UUID = Path(..., description="Product UUID"),
    payload: ProductUpdate = ...,
):
    try:
        update_product = change_product(
            str(product_id), payload.model_dump(mode="json", exclude_unset=True)
        )
        return update_product
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
