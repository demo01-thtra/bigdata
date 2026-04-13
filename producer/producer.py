"""
Kafka Producer - Simulates real-time transaction streaming from PaySim dataset.
Reads paysim.csv and sends each row as JSON to Kafka topic 'transactions'.
Enriches each transaction with simulated device_id and ip_address to support
detection of unusual login / device anomaly rules.
"""
import os
import csv
import json
import time
import uuid
import random
import hashlib
import logging
from datetime import datetime, timedelta
from kafka import KafkaProducer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [PRODUCER] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'transactions')
DATA_PATH = os.getenv('DATA_PATH', '/app/data/paysim.csv')
SEND_INTERVAL = float(os.getenv('SEND_INTERVAL', '0.5'))
BATCH_LOG_SIZE = int(os.getenv('BATCH_LOG_SIZE', '100'))
MAX_ROWS = int(os.getenv('MAX_ROWS', '0'))

# ── Device & IP simulation ─────────────────────────────────────────────
# Each user gets 1–3 usual devices and 1–2 usual IPs.
# ~5% of transactions use an UNKNOWN device (= new/suspicious login).
# ~3% of transactions use a suspicious IP (10.x.x.x range).
_user_devices: dict[str, list[str]] = {}
_user_ips: dict[str, list[str]] = {}
NEW_DEVICE_RATE = 0.05
SUSPICIOUS_IP_RATE = 0.03


def _stable_hash(val: str, n: int) -> int:
    """Deterministic hash → integer 0..n-1."""
    return int(hashlib.md5(val.encode()).hexdigest(), 16) % n


def _get_device(user_id: str) -> str:
    """Return a device_id for user_id. Occasionally returns UNKNOWN-*."""
    if random.random() < NEW_DEVICE_RATE:
        return f"UNKNOWN-{uuid.uuid4().hex[:8]}"
    if user_id not in _user_devices:
        count = random.randint(1, 3)
        _user_devices[user_id] = [
            f"DEV-{_stable_hash(user_id + str(i), 99999):05d}" for i in range(count)
        ]
    return random.choice(_user_devices[user_id])


def _get_ip(user_id: str) -> str:
    """Return an IP for user_id. Occasionally returns suspicious 10.x.x.x."""
    if random.random() < SUSPICIOUS_IP_RATE:
        return f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    if user_id not in _user_ips:
        count = random.randint(1, 2)
        _user_ips[user_id] = [
            f"192.168.{_stable_hash(user_id + str(i), 255)}.{_stable_hash(user_id + str(i) + 'x', 254) + 1}"
            for i in range(count)
        ]
    return random.choice(_user_ips[user_id])


def create_producer() -> KafkaProducer:
    """Create Kafka producer with retry logic."""
    max_retries = 30
    for attempt in range(max_retries):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                max_block_ms=10000,
            )
            logger.info(f"Connected to Kafka at {KAFKA_BOOTSTRAP}")
            return producer
        except Exception as e:
            logger.warning(f"Kafka not ready (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(2)
    raise ConnectionError(f"Failed to connect to Kafka after {max_retries} attempts")


def stream_transactions() -> None:
    """Read CSV and stream transactions to Kafka."""
    producer = create_producer()
    base_time = datetime.now()
    sent_count = 0
    fraud_count = 0

    logger.info(f"Reading data from {DATA_PATH}")
    logger.info(f"Streaming to topic '{KAFKA_TOPIC}' with {SEND_INTERVAL}s interval")

    with open(DATA_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 0 < MAX_ROWS <= sent_count:
                logger.info(f"Reached MAX_ROWS limit ({MAX_ROWS})")
                break

            transaction = {
                'transaction_id': str(uuid.uuid4()),
                'step': int(row['step']),
                'type': row['type'],
                'amount': float(row['amount']),
                'nameOrig': row['nameOrig'],
                'oldbalanceOrg': float(row['oldbalanceOrg']),
                'newbalanceOrig': float(row['newbalanceOrig']),
                'nameDest': row['nameDest'],
                'oldbalanceDest': float(row['oldbalanceDest']),
                'newbalanceDest': float(row['newbalanceDest']),
                'isFraud': int(row['isFraud']),
                'isFlaggedFraud': int(row['isFlaggedFraud']),
                'timestamp': (base_time + timedelta(seconds=sent_count)).isoformat(),
                'device_id': _get_device(row['nameOrig']),
                'ip_address': _get_ip(row['nameOrig']),
            }

            producer.send(
                KAFKA_TOPIC,
                key=transaction['transaction_id'],
                value=transaction
            )
            sent_count += 1
            if transaction['isFraud'] == 1:
                fraud_count += 1

            if sent_count % BATCH_LOG_SIZE == 0:
                logger.info(
                    f"Sent {sent_count:,} transactions "
                    f"(Frauds: {fraud_count:,}) | "
                    f"Last: {transaction['type']} ${transaction['amount']:,.2f}"
                )

            time.sleep(SEND_INTERVAL)

    producer.flush()
    producer.close()
    logger.info(f"Streaming complete. Total sent: {sent_count:,}, Frauds: {fraud_count:,}")


if __name__ == "__main__":
    logger.info("Starting Kafka Transaction Producer...")
    stream_transactions()
