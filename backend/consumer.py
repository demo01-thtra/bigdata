"""
Kafka Consumer - Listens to processed transactions and fraud alerts,
writes them to PostgreSQL, broadcasts fraud alerts via SSE and WebSocket.
"""
import os
import json
import uuid
import asyncio
import logging
import threading
import time
from datetime import datetime
from collections import deque
from kafka import KafkaConsumer
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Transaction, FraudAlert

logging.basicConfig(level=logging.INFO, format='%(asctime)s [CONSUMER] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
PROCESSED_TOPIC = os.getenv('PROCESSED_TOPIC', 'processed_transactions')

websocket_clients: list = []
_ws_loop: asyncio.AbstractEventLoop = None

# SSE support: thread-safe queue of recent alerts for SSE subscribers
sse_subscribers: list[asyncio.Queue] = []
_sse_lock = threading.Lock()


def set_ws_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _ws_loop
    _ws_loop = loop


def _build_alert_payload(data: dict) -> dict:
    """Build standard alert payload for SSE / WebSocket."""
    return {
        'type': 'fraud_alert',
        'data': {
            'transaction_id': data.get('transaction_id', ''),
            'transaction_type': data.get('type', ''),
            'amount': data.get('amount', 0),
            'detection_method': data.get('detection_method', ''),
            'reason': data.get('reason', ''),
            'fraud_probability': data.get('fraud_probability', 0),
            'risk_score': data.get('risk_score', 0),
            'device_id': data.get('device_id', ''),
            'ip_address': data.get('ip_address', ''),
            'timestamp': data.get('timestamp', ''),
        }
    }


def _broadcast_alert(data: dict) -> None:
    """Send fraud alert to all connected WebSocket and SSE clients."""
    payload = _build_alert_payload(data)

    # WebSocket broadcast
    if websocket_clients and _ws_loop is not None:
        for ws in websocket_clients[:]:
            try:
                asyncio.run_coroutine_threadsafe(ws.send_json(payload), _ws_loop)
            except Exception:
                try:
                    websocket_clients.remove(ws)
                except ValueError:
                    pass

    # SSE broadcast
    with _sse_lock:
        for q in sse_subscribers[:]:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass


def create_consumer(topic: str, group_id: str) -> KafkaConsumer:
    max_retries = 30
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id=group_id,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                max_poll_interval_ms=300000,
            )
            logger.info(f"Connected to Kafka topic: {topic}")
            return consumer
        except Exception as e:
            logger.warning(f"Kafka not ready for {topic} (attempt {attempt + 1}): {e}")
            time.sleep(2)
    raise ConnectionError(f"Failed to connect to Kafka topic {topic}")


def consume_transactions() -> None:
    consumer = create_consumer(PROCESSED_TOPIC, 'transaction-consumer-group')
    logger.info("Transaction consumer started")

    for message in consumer:
        db: Session = SessionLocal()
        try:
            data = message.value
            txn_id = uuid.UUID(data['transaction_id'])
            is_fraud = bool(data.get('is_fraud', False))

            txn = Transaction(
                id=txn_id,
                transaction_type=data['type'],
                amount=data['amount'],
                name_orig=data.get('nameOrig', ''),
                old_balance_orig=data.get('oldbalanceOrg', 0),
                new_balance_orig=data.get('newbalanceOrig', 0),
                name_dest=data.get('nameDest', ''),
                old_balance_dest=data.get('oldbalanceDest', 0),
                new_balance_dest=data.get('newbalanceDest', 0),
                device_id=data.get('device_id', ''),
                ip_address=data.get('ip_address', ''),
                is_fraud=is_fraud,
                fraud_probability=data.get('fraud_probability', 0.0),
                risk_score=data.get('risk_score', 0.0),
                detection_method=data.get('detection_method', 'none'),
                created_at=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.utcnow(),
            )
            db.add(txn)
            db.flush()

            if is_fraud:
                alert = FraudAlert(
                    transaction_id=txn_id,
                    alert_type=data.get('detection_method', 'unknown'),
                    reason=data.get('reason', ''),
                    risk_score=data.get('risk_score', 0.0),
                )
                db.add(alert)
                _broadcast_alert(data)

            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing transaction: {e}")
        finally:
            db.close()


def start_consumer_threads() -> None:
    thread = threading.Thread(target=consume_transactions, daemon=True)
    thread.start()
    logger.info("Kafka consumer thread started")
