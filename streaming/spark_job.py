"""
Real-Time Fraud Detection — PySpark Structured Streaming.

Reads raw transactions from Kafka via spark.readStream, applies:
  1. Feature engineering (Spark DataFrame ops — no Pandas)
  2. ML prediction (UDF with broadcast model — Spark-native)
  3. Rule-based detection (Spark SQL expressions)
  4. Window-based velocity features (txn_count per user in batch)
  5. Combined risk_score = 0.4 * rule_score + 0.6 * model_probability
  6. Detect: blacklist, rapid txn, new device / suspicious IP, high amount

Writes scored transactions to Kafka 'processed_transactions' and
fraud alerts to 'fraud_alerts'.
Uses checkpointing for fault tolerance.
"""

import os
import json
import logging
import time
import glob

import joblib
import numpy as np

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, from_json, to_json, struct, lit, when, udf,
    count, sum as spark_sum, expr, coalesce
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType,
    BooleanType, TimestampType
)
from pyspark.sql.window import Window

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [STREAMING] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
INPUT_TOPIC = os.getenv("INPUT_TOPIC", "transactions")
OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC", "processed_transactions")
ALERT_TOPIC = os.getenv("ALERT_TOPIC", "fraud_alerts")
MODEL_PATH = os.getenv("MODEL_PATH", "/app/model/fraud_model.pkl")
CONFIG_PATH = os.getenv("CONFIG_PATH", "/app/model/feature_config.json")
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", "/tmp/spark-checkpoint")
TRIGGER_INTERVAL = os.getenv("TRIGGER_INTERVAL", "5 seconds")

TRANSACTION_TYPES = ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]
PAYSIM_FRAUD_TYPES = ["TRANSFER", "CASH_OUT"]
HIGH_AMOUNT_THRESHOLD = 200_000
BALANCE_RATIO_THRESHOLD = 0.8

# ── JSON schema for Kafka messages ─────────────────────────────────────
TXN_SCHEMA = StructType([
    StructField("transaction_id", StringType()),
    StructField("step", IntegerType()),
    StructField("type", StringType()),
    StructField("amount", DoubleType()),
    StructField("nameOrig", StringType()),
    StructField("oldbalanceOrg", DoubleType()),
    StructField("newbalanceOrig", DoubleType()),
    StructField("nameDest", StringType()),
    StructField("oldbalanceDest", DoubleType()),
    StructField("newbalanceDest", DoubleType()),
    StructField("isFraud", IntegerType()),
    StructField("isFlaggedFraud", IntegerType()),
    StructField("timestamp", StringType()),
    StructField("device_id", StringType()),
    StructField("ip_address", StringType()),
])

FEATURE_COLS = [
    "amount", "oldbalanceOrg", "newbalanceOrig",
    "oldbalanceDest", "newbalanceDest",
    "balance_change_orig", "balance_change_dest",
    "balance_error_orig", "balance_error_dest",
    "amount_ratio",
    "type_CASH_IN", "type_CASH_OUT", "type_DEBIT",
    "type_PAYMENT", "type_TRANSFER",
]


# ── Load ML artefacts ──────────────────────────────────────────────────
def _load_model():
    """Return (model_data_dict, feature_config_dict, blacklist_list)."""
    try:
        model_data = joblib.load(MODEL_PATH)
        with open(CONFIG_PATH, "r") as f:
            feature_config = json.load(f)
        blacklist = feature_config.get("blacklist_accounts", [])
        logger.info(
            "Model loaded: %s  F1=%.4f  blacklist=%d accounts",
            model_data["model_name"],
            model_data["metrics"]["f1"],
            len(blacklist),
        )
        return model_data, feature_config, blacklist
    except Exception as exc:
        logger.warning("Could not load ML model (%s). Rule-only mode.", exc)
        return None, None, []


# ── Spark session ──────────────────────────────────────────────────────
def _create_spark() -> SparkSession:
    """Create a local-mode SparkSession with the Kafka connector."""
    jars = ",".join(glob.glob("/opt/spark-jars/*.jar"))
    builder = (
        SparkSession.builder
        .appName("FraudDetectionStreaming")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.driver.memory", "1g")
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true")
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
    )
    if jars:
        builder = builder.config("spark.jars", jars)
    else:
        builder = builder.config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3",
        )
    return builder.getOrCreate()


# ── Feature engineering (pure Spark DataFrame — NO Pandas) ─────────────
def add_features(df: DataFrame) -> DataFrame:
    """Derive feature columns using only Spark DataFrame API."""
    return (
        df
        .withColumn("balance_change_orig",
                     col("newbalanceOrig") - col("oldbalanceOrg"))
        .withColumn("balance_change_dest",
                     col("newbalanceDest") - col("oldbalanceDest"))
        .withColumn("balance_error_orig",
                     col("newbalanceOrig") + col("amount") - col("oldbalanceOrg"))
        .withColumn("balance_error_dest",
                     col("oldbalanceDest") + col("amount") - col("newbalanceDest"))
        .withColumn("amount_ratio",
                     col("amount") / (col("oldbalanceOrg") + lit(1)))
        # one-hot encode transaction type
        .withColumn("type_CASH_IN",
                     when(col("type") == "CASH_IN", 1.0).otherwise(0.0))
        .withColumn("type_CASH_OUT",
                     when(col("type") == "CASH_OUT", 1.0).otherwise(0.0))
        .withColumn("type_DEBIT",
                     when(col("type") == "DEBIT", 1.0).otherwise(0.0))
        .withColumn("type_PAYMENT",
                     when(col("type") == "PAYMENT", 1.0).otherwise(0.0))
        .withColumn("type_TRANSFER",
                     when(col("type") == "TRANSFER", 1.0).otherwise(0.0))
    )


# ── ML prediction via UDF (broadcast model, Spark-native) ─────────────
def build_predict_udf(spark_context, model_data):
    """Return a UDF that scores rows using the broadcast model."""
    bc_model = spark_context.broadcast(model_data)

    @udf(DoubleType())
    def predict_fraud_prob(
        amount, oldbalanceOrg, newbalanceOrig,
        oldbalanceDest, newbalanceDest,
        balance_change_orig, balance_change_dest,
        balance_error_orig, balance_error_dest,
        amount_ratio,
        type_ci, type_co, type_d, type_p, type_t,
    ):
        md = bc_model.value
        features = np.array([
            float(amount or 0), float(oldbalanceOrg or 0),
            float(newbalanceOrig or 0), float(oldbalanceDest or 0),
            float(newbalanceDest or 0), float(balance_change_orig or 0),
            float(balance_change_dest or 0), float(balance_error_orig or 0),
            float(balance_error_dest or 0), float(amount_ratio or 0),
            float(type_ci or 0), float(type_co or 0),
            float(type_d or 0), float(type_p or 0), float(type_t or 0),
        ]).reshape(1, -1)
        scaled = md["scaler"].transform(features)
        prob = md["model"].predict_proba(scaled)[0][1]
        return float(prob)

    return predict_fraud_prob


# ── Process each micro-batch ───────────────────────────────────────────
_batch_stats = {"total": 0, "frauds": 0}


def make_process_batch(spark, model_data, feature_config, blacklist_set):
    """Return a foreachBatch callback with captured references."""

    # Broadcast blacklist for efficient distributed lookup
    bc_blacklist = spark.sparkContext.broadcast(blacklist_set)

    # Build predict UDF if model available
    predict_udf = None
    fraud_threshold = 0.5
    if model_data is not None:
        predict_udf = build_predict_udf(spark.sparkContext, model_data)
        fraud_threshold = (
            feature_config.get("thresholds", {}).get("fraud_probability", 0.5)
            if feature_config else 0.5
        )

    # UDF to check blacklist via broadcast variable
    @udf(BooleanType())
    def is_in_blacklist(name_dest):
        return name_dest in bc_blacklist.value

    # ── callback ───────────────────────────────────────────────────────
    def process_batch(batch_df: DataFrame, batch_id: int):
        if batch_df.rdd.isEmpty():
            return

        # 1. Feature engineering (Spark DataFrame, no Pandas)
        featured = add_features(batch_df)

        # 2. ML prediction (UDF + broadcast model, NOT .toPandas())
        if predict_udf is not None:
            featured = featured.withColumn(
                "fraud_probability",
                predict_udf(*[col(c) for c in FEATURE_COLS]),
            )
        else:
            featured = featured.withColumn("fraud_probability", lit(0.0))

        # 3. ML fraud flag — only TRANSFER / CASH_OUT have labelled fraud
        featured = featured.withColumn(
            "ml_fraud",
            (col("fraud_probability") >= lit(fraud_threshold))
            & col("type").isin(PAYSIM_FRAUD_TYPES),
        )

        # 4. Rule-based detection (pure Spark expressions)
        featured = (
            featured
            .withColumn("rule_blacklist",
                        is_in_blacklist(col("nameDest"))
                        & col("type").isin(PAYSIM_FRAUD_TYPES))
            .withColumn("rule_high_amount",
                        (col("amount") > HIGH_AMOUNT_THRESHOLD)
                        & col("type").isin(PAYSIM_FRAUD_TYPES))
            .withColumn("rule_balance_ratio",
                        (col("amount") / (col("oldbalanceOrg") + lit(1))
                         > BALANCE_RATIO_THRESHOLD)
                        & col("type").isin(PAYSIM_FRAUD_TYPES)
                        & (col("oldbalanceOrg") > 0))
            .withColumn("rule_balance_error",
                        (expr("abs(newbalanceOrig + amount - oldbalanceOrg)") > 1.0)
                        & col("type").isin(PAYSIM_FRAUD_TYPES))
            .withColumn("rule_account_drain",
                        (col("newbalanceOrig") == 0)
                        & (col("amount") > 10000)
                        & col("type").isin(PAYSIM_FRAUD_TYPES))
            # Detect device / IP anomaly
            .withColumn("rule_new_device",
                        col("device_id").startswith("UNKNOWN"))
            .withColumn("rule_suspicious_ip",
                        col("ip_address").startswith("10."))
        )

        # 5. Window-based velocity feature (number of txns per user in batch)
        user_win = Window.partitionBy("nameOrig")
        featured = (
            featured
            .withColumn("txn_count_batch",
                        count("*").over(user_win))
            .withColumn("sum_amount_batch",
                        spark_sum("amount").over(user_win))
            .withColumn("rule_rapid_txn",
                        col("txn_count_batch") >= 3)
        )

        # 6. Aggregate rule_score (0.0 — 1.0)
        featured = featured.withColumn(
            "rule_score",
            when(col("rule_blacklist"), 1.0).otherwise(0.0)
            + when(col("rule_high_amount"), 0.8).otherwise(0.0)
            + when(col("rule_balance_ratio"), 0.6).otherwise(0.0)
            + when(col("rule_balance_error"), 0.5).otherwise(0.0)
            + when(col("rule_account_drain"), 0.7).otherwise(0.0)
            + when(col("rule_new_device"), 0.4).otherwise(0.0)
            + when(col("rule_suspicious_ip"), 0.3).otherwise(0.0)
            + when(col("rule_rapid_txn"), 0.5).otherwise(0.0),
        )
        featured = featured.withColumn(
            "rule_score",
            when(col("rule_score") > 1.0, 1.0).otherwise(col("rule_score")),
        )

        # 7. Combined risk_score = 0.4 * rule + 0.6 * model
        featured = featured.withColumn(
            "risk_score",
            lit(0.4) * col("rule_score") + lit(0.6) * col("fraud_probability"),
        )

        # 8. Final fraud flag & detection method
        featured = featured.withColumn(
            "is_fraud",
            col("ml_fraud") | (col("rule_score") > 0),
        )
        featured = featured.withColumn(
            "detection_method",
            when(col("ml_fraud") & (col("rule_score") > 0), "both")
            .when(col("ml_fraud"), "ml")
            .when(col("rule_score") > 0, "rule")
            .otherwise("none"),
        )

        # Build human-readable reason
        featured = featured.withColumn(
            "reason",
            coalesce(
                when(col("rule_blacklist"), lit("BLACKLIST destination; ")).otherwise(lit("")),
                lit(""),
            )
            + when(col("rule_high_amount"), lit("High amount; ")).otherwise(lit(""))
            + when(col("rule_balance_ratio"), lit("High balance ratio; ")).otherwise(lit(""))
            + when(col("rule_balance_error"), lit("Balance error; ")).otherwise(lit(""))
            + when(col("rule_account_drain"), lit("Account drained; ")).otherwise(lit(""))
            + when(col("rule_new_device"), lit("New/unknown device; ")).otherwise(lit(""))
            + when(col("rule_suspicious_ip"), lit("Suspicious IP; ")).otherwise(lit(""))
            + when(col("rule_rapid_txn"), lit("Rapid transactions; ")).otherwise(lit(""))
            + when(col("ml_fraud") & ~(col("rule_score") > 0),
                   lit("ML model prediction")).otherwise(lit("")),
        )

        # 9. Write to Kafka via native Spark sink (distributed — no .collect())
        output_cols = [
            "transaction_id", "step", "type", "amount",
            "nameOrig", "oldbalanceOrg", "newbalanceOrig",
            "nameDest", "oldbalanceDest", "newbalanceDest",
            "device_id", "ip_address",
            "is_fraud", "fraud_probability", "risk_score",
            "detection_method", "reason", "timestamp",
            "txn_count_batch", "sum_amount_batch",
        ]
        output_df = (
            featured.select(output_cols)
            .withColumn("fraud_probability",
                        coalesce(col("fraud_probability"), lit(0.0)))
            .withColumn("risk_score",
                        coalesce(col("risk_score"), lit(0.0)))
            .withColumn("txn_count_batch",
                        coalesce(col("txn_count_batch"), lit(0)))
            .withColumn("sum_amount_batch",
                        coalesce(col("sum_amount_batch"), lit(0.0)))
        ).cache()

        # Kafka format: key = transaction_id, value = to_json(struct(*))
        kafka_df = output_df.select(
            col("transaction_id").cast("string").alias("key"),
            to_json(struct([col(c) for c in output_cols])).alias("value"),
        )

        # Distributed write: ALL transactions → processed_transactions
        kafka_df.write.format("kafka") \
            .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
            .option("topic", OUTPUT_TOPIC) \
            .save()

        # Distributed write: FRAUD only → fraud_alerts
        fraud_df = output_df.filter(col("is_fraud"))
        batch_frauds = fraud_df.count()
        if batch_frauds > 0:
            fraud_df.select(
                col("transaction_id").cast("string").alias("key"),
                to_json(struct([col(c) for c in output_cols])).alias("value"),
            ).write.format("kafka") \
                .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
                .option("topic", ALERT_TOPIC) \
                .save()

        batch_total = output_df.count()
        output_df.unpersist()

        _batch_stats["total"] += batch_total
        _batch_stats["frauds"] += batch_frauds
        rate = (
            _batch_stats["frauds"] / _batch_stats["total"] * 100
            if _batch_stats["total"] > 0
            else 0
        )
        logger.info(
            "Batch %d: %d txns (%d fraud) | Total: %d txns, %d frauds (%.2f%%)",
            batch_id, batch_total, batch_frauds,
            _batch_stats["total"], _batch_stats["frauds"], rate,
        )

    return process_batch


# ── Main ───────────────────────────────────────────────────────────────
def main():
    logger.info("Starting PySpark Structured Streaming Fraud Detection …")

    # Wait for Kafka
    for attempt in range(30):
        try:
            from kafka import KafkaConsumer as KC
            c = KC(bootstrap_servers=KAFKA_BOOTSTRAP)
            c.close()
            logger.info("Kafka is ready at %s", KAFKA_BOOTSTRAP)
            break
        except Exception:
            logger.warning("Kafka not ready (attempt %d/30)", attempt + 1)
            time.sleep(2)

    model_data, feature_config, blacklist = _load_model()
    blacklist_set = set(blacklist)

    spark = _create_spark()
    spark.sparkContext.setLogLevel("WARN")
    logger.info("SparkSession created (master=%s)", spark.sparkContext.master)

    # ── spark.readStream from Kafka ────────────────────────────────────
    raw_stream = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", INPUT_TOPIC)
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
    )

    # Parse JSON
    parsed = (
        raw_stream
        .select(from_json(col("value").cast("string"), TXN_SCHEMA).alias("data"))
        .select("data.*")
        .withColumn("event_time", col("timestamp").cast(TimestampType()))
    )

    # ── writeStream with foreachBatch + checkpoint ─────────────────────
    process_fn = make_process_batch(spark, model_data, feature_config, blacklist_set)

    query = (
        parsed.writeStream
        .foreachBatch(process_fn)
        .option("checkpointLocation", CHECKPOINT_DIR)
        .trigger(processingTime=TRIGGER_INTERVAL)
        .start()
    )

    logger.info("Streaming query started — listening on topic '%s'", INPUT_TOPIC)
    query.awaitTermination()


if __name__ == "__main__":
    main()
