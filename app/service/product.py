import json
from pathlib import Path
from typing import List, Dict

DATA_FILE = Path(__file__).parent.parent / "data" / "products.json"





def load_products() -> List[Dict]:
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_all_products() -> List[Dict]:
    return load_products()


def save_product(products:List[Dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(products, file, indent=4, ensure_ascii=False)


def add_product(product:Dict) -> Dict:
    products = get_all_products()
    if any(p.get("id") == product.get("id") for p in products):
        raise ValueError("Product with this ID already exists.")
    products.append(product)
    save_product(products)
    return product        



def delete_product(product_id:str) ->str:
    products = get_all_products()
    for idx, product in enumerate(products):
        if product["id"] == str(product_id):
            deleted_product = products.pop(idx) 
            save_product(products)
    return {"message": f"Product with ID {product_id} has been deleted.", "deleted_product": deleted_product}





def change_product(product_id: str, updated_data: Dict) -> Dict:
    products = get_all_products()
    for idx, product in enumerate(products):
        if product.get("id") == product_id:
            for key, value in updated_data.items():
                if (
                    isinstance(value, dict)
                    and key in product
                    and isinstance(product[key], dict)
                ):
                    product[key].update(value)
                elif value is not None and key in product:
                    product[key] = value
            products[idx] = product
            save_product(products)
            return product
    raise ValueError("Product with this ID does not exist.")

