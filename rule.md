You are a senior software architect and data engineer. Build a COMPLETE, RUNNABLE, PRODUCTION-STYLE end-to-end real-time fraud detection system.

The user is a beginner. You MUST:

* Generate ALL code
* Use BEST PRACTICES
* Keep it SIMPLE but COMPLETE
* Ensure everything runs with minimal setup

---

# PROJECT GOAL

Build a real-time fraud detection & risk management system using:

* Python (ML + Backend)
* Apache Kafka (KRaft mode, no Zookeeper)
* Apache Spark Structured Streaming
* FastAPI backend + WebSocket
* PostgreSQL database
* Next.js (App Router) frontend with real-time dashboard
* Docker (full system orchestration)

---

# EXISTING DATA

* data/creditcard.csv → PCA-anonymized features (V1-V28, Amount, Class) — used for EDA & comparison
* data/paysim.csv → Real transaction features (type, amount, balances, isFraud) — used for training & streaming

CRITICAL: These two datasets have COMPLETELY DIFFERENT feature spaces.
Solution: Train on paysim.csv (since we stream paysim data). Use creditcard.csv for EDA analysis only.

---

# PHASE 1: DATA EXPLORATION (EDA)

File: training/eda.py

Requirements:

* Analyze BOTH datasets
* For paysim.csv:
  * Distribution of transaction types
  * Fraud ratio per transaction type
  * Amount distribution (fraud vs normal)
  * Balance change patterns
  * Correlation matrix
* For creditcard.csv:
  * Class imbalance visualization
  * Amount distribution
  * PCA component analysis
* Output charts to training/output/

Purpose: Understand data before building models.

---

# PHASE 2: FEATURE ENGINEERING + MODEL TRAINING

File: training/train.py

Step 2A - Feature Engineering on paysim.csv:

* Encode transaction type (one-hot)
* Compute derived features:
  * balance_change_orig = newbalanceOrig - oldbalanceOrg
  * balance_change_dest = newbalanceDest - oldbalanceDest
  * balance_error_orig = newbalanceOrig + amount - oldbalanceOrg (should be ~0 for honest txns)
  * balance_error_dest = oldbalanceDest + amount - newbalanceDest
  * amount_ratio = amount / (oldbalanceOrg + 1)
  * is_whole_amount = (amount % 1 == 0)
* Final feature set: amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest,
  balance_change_orig, balance_change_dest, balance_error_orig, balance_error_dest,
  amount_ratio, type_CASH_OUT, type_TRANSFER, type_CASH_IN, type_DEBIT, type_PAYMENT

Step 2B - Model Training:

* Handle class imbalance: SMOTE + class_weight='balanced'
* Train multiple models:
  * RandomForestClassifier
  * XGBClassifier (if xgboost available)
  * LogisticRegression (baseline)
* Evaluate with proper metrics:
  * Accuracy, Precision, Recall, F1-Score
  * ROC-AUC, PR-AUC
  * Confusion Matrix
* Pick best model based on F1-Score (because class imbalance)
* Save:
  * model/fraud_model.pkl
  * model/feature_config.json (feature names, thresholds, scaler params)

---

# PHASE 3: KAFKA PRODUCER (Simulate Real-Time Transactions)

File: producer/producer.py

Requirements:

* Read data/paysim.csv
* Stream row-by-row with configurable delay (default 0.5s)
* Send JSON to Kafka topic "transactions"
* Include all original fields + timestamp
* Add transaction_id (UUID) for tracking
* Log progress every N messages

---

# PHASE 4: SPARK STRUCTURED STREAMING

File: streaming/spark_job.py

Requirements:

* Read from Kafka topic "transactions"
* Parse JSON payload
* Apply feature engineering (same as training phase)
* Dual detection strategy:
  1. Rule-based detection:
     * amount > 200000 (high value)
     * Transaction type in [TRANSFER, CASH_OUT] with amount > 80% of sender balance
     * Balance error != 0 (accounting anomaly)
  2. ML model prediction:
     * Load model/fraud_model.pkl
     * Predict fraud probability
     * Flag if probability > 0.5
* Combine both strategies: fraud = rule_based OR ml_prediction
* Output:
  * Write flagged fraud events to Kafka topic "fraud_alerts"
  * Write ALL processed transactions to Kafka topic "processed_transactions"
  * Console output for monitoring

---

# PHASE 5: BACKEND (FastAPI + PostgreSQL)

File: backend/main.py + supporting files

Database Schema (PostgreSQL):

```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY,
    transaction_type VARCHAR(20),
    amount DECIMAL(15,2),
    name_orig VARCHAR(50),
    old_balance_orig DECIMAL(15,2),
    new_balance_orig DECIMAL(15,2),
    name_dest VARCHAR(50),
    old_balance_dest DECIMAL(15,2),
    new_balance_dest DECIMAL(15,2),
    is_fraud BOOLEAN DEFAULT FALSE,
    fraud_probability FLOAT DEFAULT 0.0,
    detection_method VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fraud_alerts (
    id SERIAL PRIMARY KEY,
    transaction_id UUID REFERENCES transactions(id),
    alert_type VARCHAR(50),
    reason TEXT,
    risk_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE system_metrics (
    id SERIAL PRIMARY KEY,
    total_transactions BIGINT,
    total_frauds BIGINT,
    fraud_rate FLOAT,
    avg_fraud_amount DECIMAL(15,2),
    recorded_at TIMESTAMP DEFAULT NOW()
);
```

Backend Components:

* Kafka Consumer: Listen to "processed_transactions" and "fraud_alerts" topics, write to PostgreSQL
* REST APIs:
  * GET /api/transactions — paginated list with filters
  * GET /api/transactions/{id} — single transaction detail
  * GET /api/frauds — fraud alerts with pagination
  * GET /api/stats — dashboard statistics (total txns, fraud count, fraud rate, amount stats)
  * GET /api/stats/timeline — fraud over time (for charts)
  * GET /api/stats/by-type — fraud breakdown by transaction type
* WebSocket:
  * WS /ws/alerts — real-time fraud alert stream to frontend

---

# PHASE 6: FRONTEND (Next.js Dashboard)

Requirements:

* Next.js with App Router + Tailwind CSS
* Pages:
  * / (redirect to /dashboard)
  * /dashboard — main analytics dashboard
  * /transactions — transaction list with search/filter
  * /alerts — real-time fraud alerts

Dashboard Components:
  * Stats Cards: Total transactions, Fraud count, Fraud rate %, Total amount at risk
  * Fraud by Type: Bar/Pie chart showing fraud distribution by transaction type
  * Timeline Chart: Line chart showing fraud over time
  * Recent Alerts: Live-updating list of latest fraud alerts (WebSocket)
  * Transaction Table: Paginated table with fraud highlighting

UI:
  * Modern, dark theme
  * Responsive layout
  * Real-time updates via WebSocket
  * Loading states and error handling

---

# PHASE 7: DOCKER ORCHESTRATION

docker-compose.yml services:

* kafka (KRaft mode, single node)
* postgres (with init SQL)
* spark-master + spark-worker
* producer (Python)
* streaming (Spark job)
* backend (FastAPI)
* frontend (Next.js)

Requirements:
* Health checks for all services
* Proper dependency ordering (depends_on with condition)
* Named volumes for data persistence
* Single network for all services
* Environment variables via .env file
* Run with: docker-compose up --build

---

# PHASE 8: PROJECT STRUCTURE

```
fraud-detection/
├── data/
│   ├── creditcard.csv
│   └── paysim.csv
├── model/
│   ├── fraud_model.pkl          (generated)
│   └── feature_config.json      (generated)
├── training/
│   ├── eda.py
│   ├── train.py
│   ├── requirements.txt
│   └── output/                  (generated charts)
├── producer/
│   ├── producer.py
│   ├── requirements.txt
│   └── Dockerfile
├── streaming/
│   ├── spark_job.py
│   ├── requirements.txt
│   └── Dockerfile
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── consumer.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   ├── components/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── next.config.js
│   └── Dockerfile
├── docker/
│   └── init.sql
├── docker-compose.yml
├── .env
├── requirements.txt
└── README.md
```

---

# PHASE 9: README

Include:
* Project overview and architecture diagram (ASCII)
* Tech stack explanation
* Prerequisites
* Quick start guide (docker-compose up)
* Manual setup instructions
* API documentation
* Screenshots description
* Team information

---

# EXECUTION ORDER

1. training/eda.py → understand data
2. training/train.py → train and save model
3. docker-compose up → start infrastructure
4. producer starts → sends transactions to Kafka
5. spark streaming starts → processes and detects fraud
6. backend starts → consumes results, serves API + WebSocket
7. frontend starts → displays real-time dashboard

---

# IMPORTANT RULES

* DO NOT train on creditcard.csv and predict on paysim.csv (feature mismatch)
* Train on paysim.csv since streaming data comes from paysim
* Use creditcard.csv for EDA comparison only
* Handle class imbalance properly (paysim fraud rate is ~0.13%)
* All components must communicate through Kafka (decoupled architecture)
* WebSocket for real-time updates to frontend
* Generate FULL, RUNNABLE code for every file
* Add proper error handling and logging
* Ensure beginner-friendly with clear comments
