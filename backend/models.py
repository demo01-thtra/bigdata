"""SQLAlchemy ORM models."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Float, Boolean, Integer, DateTime, Text, ForeignKey, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID
from database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_type = Column(String(20), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    name_orig = Column(String(50))
    old_balance_orig = Column(Float, default=0)
    new_balance_orig = Column(Float, default=0)
    name_dest = Column(String(50))
    old_balance_dest = Column(Float, default=0)
    new_balance_dest = Column(Float, default=0)
    is_fraud = Column(Boolean, default=False, index=True)
    fraud_probability = Column(Float, default=0.0)
    detection_method = Column(String(20), default='none')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), index=True)
    alert_type = Column(String(50), nullable=False)
    reason = Column(Text)
    risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    total_transactions = Column(BigInteger, default=0)
    total_frauds = Column(BigInteger, default=0)
    fraud_rate = Column(Float, default=0.0)
    avg_fraud_amount = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=datetime.utcnow)
