from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


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
