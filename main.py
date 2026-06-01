import random 
from typing import List
from fastapi import FastAPI, Depends
from faker import Faker
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, declarative_base, Session


# ============================================================================
# DATABASE CONNECTION SETUP
# ============================================================================
DB_URL = 'postgresql://postgres:secretpassword@localhost:5432/computer_shop_db'
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Model (How the data shapes up inside PostgreSQL)
class ProductModel(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brand = Column(String)
    item_type = Column(String)
    full_name = Column(String)
    price = Column(Float)

# Instantly draw out the empty table structures inside PostgreSQL
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =====================================================================
# FastAPI & VALIDATION SCHEMAS
# =====================================================================

# 1. Initialize our main app (The Waiter)
app = FastAPI(title="Computer Shop Rest API Lab")

# 2. Initialize Faker
faker = Faker()

# Fixed shop lists for consistent generation attributes
BRANDS = ["Lenovo", "Apple", "Dell", "HP", "Asus"]
ITEMS = ["Laptop", "Wireless Mouse", "Mechanical Keyboard", "Gaming Monitor"]

# 3. Define our Pydantic Guard Dog (Data Validator)
class ProductSchema(BaseModel):
    id:int
    brand:str
    item_type:str
    full_name:str
    price:float = Field(..., gt=0, description="Price must be greater than 0")

    class Config:
        from_attributes = True

# =====================================================================
# REST API ENDPOINTS
# =====================================================================       
@app.get("/health")
def check_health():
    return {"status":"ok"}

@app.get("/seed-inventory")
def seed_database(db: Session = Depends(get_db)):
    """Generates 5 items using Faker and saves them permanently into PostgreSQL."""
    db.query(ProductModel).delete()

    count = 0

    for item_id in range(1, 6):
        choosen_brand = random.choice(BRANDS)
        choosen_item = random.choice(ITEMS)

        record = ProductModel(
            id=item_id,
            brand=choosen_brand, 
            item_type=choosen_item,
            full_name=f"{choosen_brand}{choosen_item}",
            price=float(faker.random_int(min=45, max=1600))
        )
        db.add(record) # Put into shopping cart
    
    db.commit() # Push changes permanently into Docker!
    return {"message": f"Success! {count} unique products saved into PostgreSQL."}
            

        

@app.get("/products", response_model=List[ProductSchema])
def get_saved_products(db: Session = Depends(get_db)):
    """Reads our inventory records directly from PostgreSQL."""
    products_in_db = db.query(ProductModel).all()
    return products_in_db