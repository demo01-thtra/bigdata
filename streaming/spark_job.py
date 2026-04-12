"""
Real-Time Fraud Detection Streaming Processor.
Reads from Kafka, applies feature engineering + ML model + rule-based detection,
writes results to Kafka output topics.
"""
import os
import json
import logging
import time
import joblib
import numpy as np
from kafka import KafkaConsumer, KafkaProducer

logging.basicConfig(level=logging.INFO, format='%(asctime)s [STREAMING] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
INPUT_TOPIC = os.getenv('INPUT_TOPIC', 'transactions')
OUTPUT_TOPIC = os.getenv('OUTPUT_TOPIC', 'processed_transactions')
ALERT_TOPIC = os.getenv('ALERT_TOPIC', 'fraud_alerts')
MODEL_PATH = os.getenv('MODEL_PATH', '/app/model/fraud_model.pkl')
CONFIG_PATH = os.getenv('CONFIG_PATH', '/app/model/feature_config.json')

TRANSACTION_TYPES = ['CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER']
# Trong PaySim, nhãn isFraud=1 chỉ xuất hiện ở TRANSFER và CASH_OUT.
# Chỉ áp ML + rule "đặc thù gian lận PaySim" cho hai loại này để khớp EDA và tránh FP CASH_IN/DEBIT/PAYMENT.
PAYSIM_FRAUD_TYPES = ('TRANSFER', 'CASH_OUT')
HIGH_AMOUNT_THRESHOLD = 200000
BALANCE_RATIO_THRESHOLD = 0.8

model_data = None
feature_config = None
blacklist_accounts = set()


def load_model() -> bool:
    """Load the trained ML model, config, and blacklist."""
    global model_data, feature_config, blacklist_accounts
    try:
        model_data = joblib.load(MODEL_PATH)
        with open(CONFIG_PATH, 'r') as f:
            feature_config = json.load(f)
        blacklist_accounts = set(feature_config.get('blacklist_accounts', []))
        logger.info(f"Model loaded: {model_data['model_name']}")
        logger.info(f"Model F1: {model_data['metrics']['f1']:.4f}")
        logger.info(f"Blacklist: {len(blacklist_accounts)} accounts")
        return True
    except Exception as e:
        logger.warning(f"Could not load ML model: {e}. Rule-based only.")
        return False


def build_feature_vector(txn: dict) -> list:
    """Build feature vector matching training pipeline."""
    amount = float(txn.get('amount', 0))
    old_bal_orig = float(txn.get('oldbalanceOrg', 0))
    new_bal_orig = float(txn.get('newbalanceOrig', 0))
    old_bal_dest = float(txn.get('oldbalanceDest', 0))
    new_bal_dest = float(txn.get('newbalanceDest', 0))
    txn_type = txn.get('type', '')

    balance_change_orig = new_bal_orig - old_bal_orig
    balance_change_dest = new_bal_dest - old_bal_dest
    balance_error_orig = new_bal_orig + amount - old_bal_orig
    balance_error_dest = old_bal_dest + amount - new_bal_dest
    amount_ratio = amount / (old_bal_orig + 1)
    type_features = [1.0 if txn_type == t else 0.0 for t in TRANSACTION_TYPES]

    return [
        amount, old_bal_orig, new_bal_orig, old_bal_dest, new_bal_dest,
        balance_change_orig, balance_change_dest,
        balance_error_orig, balance_error_dest, amount_ratio
    ] + type_features


def predict_fraud_ml(txn: dict) -> tuple:
    """ML prediction. Returns (is_fraud, probability).

    PaySim chỉ có gian lật đã gán nhãn ở TRANSFER/CASH_OUT; áp ngưỡng gian lật ML
    chỉ cho hai loại đó — vẫn tính prob cho mọi loại (hiển thị) nhưng không báo fraud từ ML với CASH_IN/DEBIT/PAYMENT.
    """
    if model_data is None:
        return (False, 0.0)
    try:
        features = np.array([build_feature_vector(txn)])
        scaled = model_data['scaler'].transform(features)
        prob = float(model_data['model'].predict_proba(scaled)[0][1])
        threshold = 0.5
        if feature_config:
            threshold = feature_config.get('thresholds', {}).get('fraud_probability', 0.5)
        txn_type = txn.get('type', '')
        ml_flag = prob >= threshold and txn_type in PAYSIM_FRAUD_TYPES
        return (ml_flag, prob)
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        return (False, 0.0)


def apply_rules(txn: dict) -> tuple:
    """Rule-based detection with Blacklist. Returns (is_fraud, reason)."""
    reasons = []
    amount = float(txn.get('amount', 0))
    txn_type = txn.get('type', '')
    old_bal = float(txn.get('oldbalanceOrg', 0))
    new_bal_orig = float(txn.get('newbalanceOrig', 0))
    name_dest = txn.get('nameDest', '')
    balance_error = new_bal_orig + amount - old_bal

    if name_dest in blacklist_accounts and txn_type in PAYSIM_FRAUD_TYPES:
        reasons.append(f"BLACKLIST: Destination {name_dest[:12]} is blacklisted")

    if amount > HIGH_AMOUNT_THRESHOLD and txn_type in PAYSIM_FRAUD_TYPES:
        reasons.append(f"High amount: ${amount:,.2f}")

    if txn_type in ('TRANSFER', 'CASH_OUT') and old_bal > 0:
        ratio = amount / old_bal
        if ratio > BALANCE_RATIO_THRESHOLD:
            reasons.append(f"High balance ratio: {ratio:.2f}")

    if abs(balance_error) > 1.0 and txn_type in ('TRANSFER', 'CASH_OUT'):
        reasons.append(f"Balance error: {balance_error:,.2f}")

    if txn_type in ('TRANSFER', 'CASH_OUT') and new_bal_orig == 0 and amount > 10000:
        reasons.append("Account drained completely")

    return (len(reasons) > 0, "; ".join(reasons) if reasons else "")


def create_kafka_clients() -> tuple:
    """Create Kafka consumer and producer with retry."""
    max_retries = 30
    for attempt in range(max_retries):
        try:
            consumer = KafkaConsumer(
                INPUT_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                group_id='fraud-detection-streaming',
                auto_offset_reset='latest',
                enable_auto_commit=True,
            )
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            )
            logger.info(f"Connected to Kafka at {KAFKA_BOOTSTRAP}")
            return consumer, producer
        except Exception as e:
            logger.warning(f"Kafka not ready (attempt {attempt + 1}): {e}")
            time.sleep(2)
    raise ConnectionError("Failed to connect to Kafka")


def process_transaction(txn: dict) -> dict:
    """Process a single transaction through ML + Rules."""
    ml_fraud, ml_prob = predict_fraud_ml(txn)
    rule_fraud, rule_reason = apply_rules(txn)

    is_fraud = ml_fraud or rule_fraud
    if ml_fraud and rule_fraud:
        detection_method = 'both'
    elif ml_fraud:
        detection_method = 'ml'
    elif rule_fraud:
        detection_method = 'rule'
    else:
        detection_method = 'none'

    reason = rule_reason if rule_reason else ('ML model prediction' if ml_fraud else '')

    return {
        'transaction_id': txn.get('transaction_id', ''),
        'step': txn.get('step', 0),
        'type': txn.get('type', ''),
        'amount': txn.get('amount', 0),
        'nameOrig': txn.get('nameOrig', ''),
        'oldbalanceOrg': txn.get('oldbalanceOrg', 0),
        'newbalanceOrig': txn.get('newbalanceOrig', 0),
        'nameDest': txn.get('nameDest', ''),
        'oldbalanceDest': txn.get('oldbalanceDest', 0),
        'newbalanceDest': txn.get('newbalanceDest', 0),
        'is_fraud': is_fraud,
        'fraud_probability': ml_prob,
        'detection_method': detection_method,
        'reason': reason,
        'timestamp': txn.get('timestamp', ''),
    }


def main() -> None:
    """Main streaming pipeline."""
    logger.info("Starting Real-Time Fraud Detection Pipeline...")
    has_model = load_model()
    if not has_model:
        logger.info("Running in RULE-BASED ONLY mode")

    consumer, producer = create_kafka_clients()
    logger.info(f"Listening on topic: {INPUT_TOPIC}")

    total_processed = 0
    total_frauds = 0

    for message in consumer:
        txn = message.value
        result = process_transaction(txn)

        producer.send(OUTPUT_TOPIC, value=result)
        total_processed += 1

        if result['is_fraud']:
            alert = {
                'transaction_id': result['transaction_id'],
                'type': result['type'],
                'amount': result['amount'],
                'nameOrig': result['nameOrig'],
                'nameDest': result['nameDest'],
                'fraud_probability': result['fraud_probability'],
                'detection_method': result['detection_method'],
                'reason': result['reason'],
                'timestamp': result['timestamp'],
            }
            producer.send(ALERT_TOPIC, value=alert)
            total_frauds += 1
            logger.warning(
                f"FRAUD DETECTED | {result['type']} | "
                f"${result['amount']:,.2f} | {result['detection_method']} | "
                f"{result['reason']}"
            )

        if total_processed % 50 == 0:
            producer.flush()
            logger.info(
                f"Processed: {total_processed:,} | "
                f"Frauds: {total_frauds:,} | "
                f"Rate: {(total_frauds/total_processed*100) if total_processed > 0 else 0:.2f}%"
            )


if __name__ == "__main__":
    main()
