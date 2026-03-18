from xml.parsers.expat import model

from pydantic import BaseModel, Field , AnyUrl , field_validator ,EmailStr, model_validator , computed_field 
from typing import Annotated , Literal , Optional , List
from uuid import UUID, uuid4
from datetime import datetime


class Seller(BaseModel):
    id: UUID

    name: Annotated[
        str,
        Field(
            min_length=2,
            max_length=60,
            title="Seller Name",
            description="Name of the seller (2-60 chars).",
            examples=["Mi Store", "Apple Store"],
        ),
    ]

    email: EmailStr = Field(
        ...,
        description="Seller's contact email"
    )
    website: Optional[AnyUrl]



    @field_validator("email" , mode="after")
    @classmethod
    def validate_seller_email_domain(cls , value:str):
        allowed_domains = ["example.com", "store.com"]
        domain = str(value).split("@")[-1].lower
        if domain not in allowed_domains:
            raise ValueError(f"Email domain must be one of: {', '.join(allowed_domains)}")
        
        return value

class Dimension(BaseModel):
    length: Annotated[float, Field(gt=0, description="Length in cm")]
    width: Annotated[float, Field(gt=0, description="Width in cm")]
    height: Annotated[float, Field(gt=0, description="Height in cm")]

    @field_validator("length", "width", "height", mode="after")
    @classmethod
    def validate_dimensions(cls, value: float):
        if value <= 0:
            raise ValueError("Dimensions must be greater than zero")
        return value
    



class Product(BaseModel):
    id: UUID 
    sku: Annotated[
        str,
        Field(
            min_length=6,
            max_length=30,
            title="SKU",
            description="Stock Keeping Unit",
            examples=["XIAO-359GB-001", "APPL-212GB-049"],
        ),
    ]
    name: Annotated[
        str,
        Field(
            min_length=3,
            max_length=80,
            title="Product Name",
            description="Readable product name (3-80 chars).",
            examples=["Xiaomi Model Pro", "Apple Model X"],
        ),
    ]

    description: Annotated[
        str,
        Field(max_length=200, description="Short product description"),
    ]

    category: Annotated[
        str,
        Field(
            min_length=3,
            max_length=30,
            description="Category like mobiles/laptops/electronics/accessories",
            examples=["mobiles", "laptops"],
        ),
    ]

    brand: Annotated[
        str,
        Field(min_length=2, max_length=40, examples=["Xiaomi", "Apple"]),
    ]

    price: Annotated[float, Field(gt=0, strict=True, description="Base price (INR)")]
    currency: Literal["INR"] = "INR"

    discount_percent: Annotated[
        int,
        Field(ge=0, le=90, description="Discount in percent (0-90)"),
    ] = 0

    stock: Annotated[int, Field(ge=0, description="Available stock (>=0)")]
    is_active: Annotated[bool, Field(description="Is product active?")]

    rating: Annotated[
        float,
        Field(ge=0, le=5, strict=True, description="Rating out of 5"),
    ]
    tags: Annotated[
        Optional[list[str]],
        Field(default=None,max_length=10, description="List of tags for the product"),
    ]

    image_urls: Annotated[
        Optional[List[AnyUrl]],
        Field(
            default=None,
            description="List of image URLs for the product",
        )
    ]
    dimensions: Dimension
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Product creation timestamp")
    
    seller: Seller

    @field_validator("sku" , mode="after")
    @classmethod
    def validate_sku_format(cls , value:str):
        if "-" not in value:
            raise ValueError("SKU must contain at least one underscore")

        last = value.split("-")[-1]
        if not (len(last) == 3 and last.isdigit()):
            raise ValueError("SKU must end with a 3-digit number")
        
        return value
    @model_validator(mode="after")
    @classmethod
    def validate_business_rules(cls, model: "Product"):
        if model.stock ==0 and model.is_active is True:
            raise ValueError("Product cannot be active if stock is zero")
        
        if model.discount_percent >0 and model.rating ==0 :
            raise ValueError("Product with discount cannot have zero rating")
        
        return model
    
    @computed_field
    @property
    def discounted_price(self) -> float:
        discount_amount = (self.price * self.discount_percent) / 100
        return round(self.price - discount_amount, 2)
    
    @computed_field
    @property
    def volume_cm3(self) -> float:
        return round(self.dimensions.length * self.dimensions.width * self.dimensions.height, 2)
    

#### Update Models

class DimensionsCMUpdate(BaseModel):
    length: Optional[float] = Field(gt=0)
    width: Optional[float] = Field(gt=0)
    height: Optional[float] = Field(gt=0)


class SellerUpdate(BaseModel):
    name: Optional[str] = Field(min_length=2, max_length=60)
    email: Optional[EmailStr]
    website: Optional[AnyUrl]

    @field_validator("email", mode="after")
    @classmethod
    def validate_seller_email_domain(cls, value: EmailStr):
        allowed_domains = {
            "mistore.in",
            "realmeofficial.in",
            "samsungindia.in",
            "lenovostore.in",
            "hpworld.in",
            "applestoreindia.in",
            "dellexclusive.in",
            "sonycenter.in",
            "oneplusstore.in",
            "asusexclusive.in",
        }
        domain = str(value).split("@")[-1].lower()
        if domain not in allowed_domains:
            raise ValueError(f"Seller email domain not allowed: {domain}")
        return value


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(min_length=3, max_length=80)
    description: Optional[str] = Field(max_length=200)
    category: Optional[str]
    brand: Optional[str]
    price: Optional[float] = Field(gt=0)
    currency: Optional[Literal["INR", "USD", "EUR"]]
    discount_percent: Optional[int] = Field(ge=0, le=90)
    stock: Optional[int] = Field(ge=0)
    is_active: Optional[bool]
    rating: Optional[float] = Field(ge=0, le=5)
    tags: Optional[List[str]] = Field(max_items=10)
    image_urls: Optional[List[AnyUrl]]
    dimensions_cm: Optional[DimensionsCMUpdate]
    seller: Optional[SellerUpdate]
    @model_validator(mode="after")
    @classmethod
    def validate_business_rules(cls, model: "ProductUpdate"):

        if model.stock is not None and model.is_active is not None:
            if model.stock == 0 and model.is_active:
                raise ValueError("If stock is 0, is_active must be false")

        if model.discount_percent is not None and model.rating is not None:
            if model.discount_percent > 0 and model.rating == 0:
                raise ValueError("Discounted product must have rating")

        return model
    @computed_field
    @property
    def final_price(self) -> Optional[float]:
        if self.price is None or self.discount_percent is None:
            return None
        return round(self.price * (1 - self.discount_percent / 100), 2)
    @computed_field
    @property
    def volume_cm3(self) -> Optional[float]:
        if self.dimensions_cm is None:
            return None

        d = self.dimensions_cm
        return round(d.length * d.width * d.height, 2)
