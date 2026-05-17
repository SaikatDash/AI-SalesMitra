from datetime import datetime
from pathlib import Path
import sys
from typing import Generator, List, Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from database_model import Base, User, SalesData
from model  import UserRegister, UserLogin, UserUpdate, UserResponse, loginresponse, SalesDataResponse
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from chatbot.rag_chatbot import SalesMitraChatbot, product_location_cluster_analysis


# Ensure tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AISalesMitra:You Personal Sales Assistant API", version="1.0.0")

# Add CORS middleware to allow requests from Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    import hashlib

    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


class ChatbotQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/api/register", status_code=201)
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    db_user = User(
        email=user.email,
        full_name=user.full_name or "",
        password=hash_password(user.password),
        is_active=1,
        role="user",
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserResponse.model_validate(db_user)


@app.put("/api/user/{user_id}")
def update_user(user_id: int, user_data: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.password is not None:
        user.password = hash_password(user_data.password)
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@app.get("/api/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@app.post("/api/login")
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user.last_login = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return loginresponse.model_validate(user)


# Sales Data Endpoints
@app.get("/api/sales", response_model=List[SalesDataResponse])
def get_sales(
    zone: Optional[str] = None,
    branch: Optional[str] = None,
    brand: Optional[str] = None,
    limit: int = 1000,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    """Get sales data with optional filters"""
    query = db.query(SalesData)
    
    if zone:
        query = query.filter(SalesData.zone == zone)
    if branch:
        query = query.filter(SalesData.branch_name == branch)
    if brand:
        query = query.filter(SalesData.brand_name == brand)
    
    return query.offset(skip).limit(limit).all()


@app.get("/api/sales/zones", response_model=List[str])
def get_zones(db: Session = Depends(get_db)):
    """Get all unique zones"""
    zones = db.query(SalesData.zone).distinct().all()
    return [z[0] for z in zones if z[0]]


@app.get("/api/sales/branches", response_model=List[str])
def get_branches(zone: Optional[str] = None, db: Session = Depends(get_db)):
    """Get all unique branches, optionally filtered by zone"""
    query = db.query(SalesData.branch_name).distinct()
    if zone:
        query = query.filter(SalesData.zone == zone)
    branches = query.all()
    return [b[0] for b in branches if b[0]]


@app.get("/api/sales/brands", response_model=List[str])
def get_brands(db: Session = Depends(get_db)):
    """Get all unique brands"""
    brands = db.query(SalesData.brand_name).distinct().all()
    return [b[0] for b in brands if b[0]]


@app.get("/api/sales/summary")
def get_sales_summary(db: Session = Depends(get_db)):
    """Get sales summary statistics"""
    from sqlalchemy import func
    
    summary = db.query(
        func.count(SalesData.id).label("total_records"),
        func.sum(SalesData.sales_amt).label("total_sales"),
        func.sum(SalesData.sales_qty).label("total_qty"),
        func.avg(SalesData.sales_amt).label("avg_sales")
    ).first()
    
    return {
        "total_records": summary.total_records or 0,
        "total_sales": float(summary.total_sales or 0),
        "total_qty": float(summary.total_qty or 0),
        "avg_sales": float(summary.avg_sales or 0)
    }


@app.get("/api/analytics/product-location-clusters")
def get_product_location_clusters(
    profit_margin_pct: float = 20.0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Cluster product-location sales and project next-year profit."""
    if profit_margin_pct < 0 or profit_margin_pct > 100:
        raise HTTPException(status_code=400, detail="profit_margin_pct must be between 0 and 100")
    result = product_location_cluster_analysis(db, SalesData, profit_margin_pct=profit_margin_pct)
    result["records"] = result["records"][: max(limit, 0)]
    return result


@app.post("/api/chatbot/query")
def ask_chatbot(payload: ChatbotQuery, db: Session = Depends(get_db)):
    """Ask the local RAG chatbot for sales insights or navigation help."""
    bot = SalesMitraChatbot(db, SalesData)
    return bot.answer(payload.query)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
