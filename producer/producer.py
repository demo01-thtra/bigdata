"""
Kafka Producer - Simulates real-time transaction streaming from PaySim dataset.
Reads paysim.csv and sends each row as JSON to Kafka topic 'transactions'.
"""
import os
import csv
import json
import time
import uuid
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
