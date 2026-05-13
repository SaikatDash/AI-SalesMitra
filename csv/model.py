from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SalesDataBase(BaseModel):
    """Base sales data schema"""
    ac_yr: str
    mmyyyy: str
    zone: str
    branch_name: str
    mkt_type: str
    brand_name: str
    sales_qty: float
    sales_amt: float
    cn_qty: Optional[float] = None
    cn_amt: Optional[float] = None
    act_qty: Optional[float] = None
    act_amt: Optional[float] = None


class SalesDataCreate(SalesDataBase):
    """Schema for creating sales data"""
    pass


class SalesDataResponse(SalesDataBase):
    """Response schema for sales data"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
