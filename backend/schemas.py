"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class TransactionResponse(BaseModel):
    id: UUID
    transaction_type: str
    amount: float
    name_orig: Optional[str] = None
    name_dest: Optional[str] = None
    old_balance_orig: float = 0
    new_balance_orig: float = 0
    old_balance_dest: float = 0
    new_balance_dest: float = 0
    is_fraud: bool = False
    fraud_probability: float = 0.0
    detection_method: str = "none"
    created_at: datetime

    class Config:
        from_attributes = True


class FraudAlertResponse(BaseModel):
    id: int
    transaction_id: UUID
    alert_type: str
    reason: Optional[str] = None
    risk_score: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_transactions: int
    total_frauds: int
    fraud_rate: float
    total_amount: float
    total_fraud_amount: float
    avg_fraud_amount: float
    detection_breakdown: dict


class TimelinePoint(BaseModel):
    timestamp: str
    total: int
    frauds: int


class TypeBreakdown(BaseModel):
    transaction_type: str
    total: int
    frauds: int
    fraud_rate: float


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    pages: int
