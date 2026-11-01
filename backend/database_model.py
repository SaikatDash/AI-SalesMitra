from sqlalchemy import Column, Integer, String, DateTime, Float, Date, ForeignKey, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

Base = declarative_base()

class User(Base):
    """User registration and authentication model"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    password = Column(String)
    is_active = Column(Integer, default=1)  # 1 for active, 0 for inactive
    role = Column(String, default='user')  # 'user', 'admin', etc.
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SalesData(Base):
    """Sales data model from CSV"""
    __tablename__ = 'sales_data'
    
    id = Column(Integer, primary_key=True, index=True)
    ac_yr = Column(String, index=True)  # Accounting Year
    mmyyyy = Column(String, index=True)  # Month-Year
    zone = Column(String, index=True)
    branch_name = Column(String, index=True)
    mkt_type = Column(String)
    brand_name = Column(String, index=True)
    sales_qty = Column(Float)
    sales_amt = Column(Float)
    cn_qty = Column(Float, nullable=True)
    cn_amt = Column(Float, nullable=True)
    act_qty = Column(Float, nullable=True)
    act_amt = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UploadedDataset(Base):
    """Registry entry for a user's uploaded, dynamically shaped dataset."""
    __tablename__ = "uploaded_datasets"
    __table_args__ = (UniqueConstraint("user_id", "content_hash", name="uq_user_dataset_hash"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = Column(String(255), nullable=False)
    table_name = Column(String(63), nullable=False, unique=True)
    content_hash = Column(String(64), nullable=False)
    columns_json = Column(Text, nullable=False)
    row_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)





