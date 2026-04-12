"""
FastAPI Backend for Fraud Detection Dashboard.
Provides REST APIs and WebSocket for real-time alerts.
"""
import os
import logging
import math
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, Integer
from database import engine, get_db, Base
from models import Transaction, FraudAlert, SystemMetric
from schemas import (
    TransactionResponse, FraudAlertResponse, DashboardStats,
    TimelinePoint, TypeBreakdown, PaginatedResponse
)
from consumer import start_consumer_threads, websocket_clients, set_ws_loop

logging.basicConfig(level=logging.INFO, format='%(asctime)s [API] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

ENABLE_KAFKA = os.getenv("ENABLE_KAFKA", "true").lower() in ("1", "true", "yes")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    import asyncio
    set_ws_loop(asyncio.get_event_loop())
    if ENABLE_KAFKA:
        logger.info("Starting Kafka consumer threads...")
        try:
            start_consumer_threads()
        except Exception as e:
            logger.warning(f"Could not start Kafka consumer: {e}")
    else:
        logger.info("Kafka consumer disabled (ENABLE_KAFKA=false) — API + DB only, suitable for Render/Vercel without broker.")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Fraud Detection API",
    description="Real-time fraud detection and risk management system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/transactions", response_model=PaginatedResponse)
def get_transactions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_fraud: bool = None,
    transaction_type: str = None,
    db: Session = Depends(get_db),
):
    """Get paginated transaction list with optional filters."""
    query = db.query(Transaction)
    if is_fraud is not None:
        query = query.filter(Transaction.is_fraud == is_fraud)
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)

    total = query.count()
    pages = math.ceil(total / per_page) if total > 0 else 1
    items = (
        query
        .order_by(desc(Transaction.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedResponse(
        items=[TransactionResponse.model_validate(t) for t in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@app.get("/api/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Get single transaction by ID."""
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Transaction not found")
    return TransactionResponse.model_validate(txn)


@app.get("/api/frauds", response_model=PaginatedResponse)
def get_fraud_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get paginated fraud alerts."""
    query = db.query(FraudAlert)
    total = query.count()
    pages = math.ceil(total / per_page) if total > 0 else 1
    items = (
        query
        .order_by(desc(FraudAlert.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedResponse(
        items=[FraudAlertResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@app.get("/api/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    total_txns = db.query(func.count(Transaction.id)).scalar() or 0
    total_frauds = db.query(func.count(Transaction.id)).filter(
        Transaction.is_fraud == True
    ).scalar() or 0
    total_amount = db.query(func.sum(Transaction.amount)).scalar() or 0
    fraud_amount = db.query(func.sum(Transaction.amount)).filter(
        Transaction.is_fraud == True
    ).scalar() or 0
    avg_fraud_amount = db.query(func.avg(Transaction.amount)).filter(
        Transaction.is_fraud == True
    ).scalar() or 0

    detection_methods = (
        db.query(Transaction.detection_method, func.count(Transaction.id))
        .filter(Transaction.is_fraud == True)
        .group_by(Transaction.detection_method)
        .all()
    )
    breakdown = {method: count for method, count in detection_methods}

    return DashboardStats(
        total_transactions=total_txns,
        total_frauds=total_frauds,
        fraud_rate=round((total_frauds / total_txns * 100) if total_txns > 0 else 0, 4),
        total_amount=round(float(total_amount), 2),
        total_fraud_amount=round(float(fraud_amount), 2),
        avg_fraud_amount=round(float(avg_fraud_amount), 2),
        detection_breakdown=breakdown,
    )


@app.get("/api/stats/timeline", response_model=list[TimelinePoint])
def get_timeline_stats(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    """Get fraud timeline data for charts."""
    since = datetime.utcnow() - timedelta(hours=hours)
    results = (
        db.query(
            func.date_trunc('hour', Transaction.created_at).label('hour'),
            func.count(Transaction.id).label('total'),
            func.sum(func.cast(Transaction.is_fraud, Integer)).label('frauds'),
        )
        .filter(Transaction.created_at >= since)
        .group_by('hour')
        .order_by('hour')
        .all()
    )

    return [
        TimelinePoint(
            timestamp=r.hour.isoformat() if r.hour else '',
            total=r.total or 0,
            frauds=int(r.frauds or 0),
        )
        for r in results
    ]


@app.get("/api/stats/by-type", response_model=list[TypeBreakdown])
def get_stats_by_type(db: Session = Depends(get_db)):
    """Get fraud breakdown by transaction type."""
    results = (
        db.query(
            Transaction.transaction_type,
            func.count(Transaction.id).label('total'),
            func.sum(func.cast(Transaction.is_fraud, Integer)).label('frauds'),
        )
        .group_by(Transaction.transaction_type)
        .all()
    )

    return [
        TypeBreakdown(
            transaction_type=r.transaction_type,
            total=r.total,
            frauds=int(r.frauds or 0),
            fraud_rate=round((int(r.frauds or 0) / r.total * 100) if r.total > 0 else 0, 2),
        )
        for r in results
    ]


@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time fraud alerts."""
    await websocket.accept()
    websocket_clients.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(websocket_clients)}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(websocket_clients)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
