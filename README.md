# Real-Time Fraud Detection & Risk Management System

## Overview

Hệ thống phát hiện gian lận thời gian thực (Real-Time Fraud Detection) sử dụng các công nghệ Big Data.
Hệ thống kết hợp **Machine Learning** và **Rule-based Detection** để phát hiện giao dịch gian lận
trong luồng dữ liệu streaming.

## Architecture

```
┌─────────────┐    ┌───────────┐    ┌──────────────┐    ┌──────────┐    ┌──────────┐
│  PaySim CSV │───>│   Kafka   │───>│  Streaming   │───>│  Kafka   │───>│ FastAPI  │
│  (Producer) │    │ (topic:   │    │  (Python:     │    │ (output  │    │ Backend  │
│             │    │  txns)    │    │   ML+Rules)   │    │  topics) │    │          │
└─────────────┘    └───────────┘    └──────────────┘    └──────────┘    └────┬─────┘
                                                                           │
                                                                      ┌────▼─────┐
                                                                      │PostgreSQL│
                                                                      └────┬─────┘
                                                                           │
                                                                      ┌────▼─────┐
                                                                      │ Next.js  │
                                                                      │ Dashboard│
                                                                      └──────────┘
```

## Tech Stack

| Component        | Technology                          |
|-----------------|-------------------------------------|
| Data Streaming  | Apache Kafka (KRaft mode)           |
| Stream Processing| Python (Kafka consumer) + ML + rules |
| ML Training     | scikit-learn, pandas, numpy         |
| Backend API     | FastAPI + SQLAlchemy                |
| Database        | PostgreSQL 16                       |
| Frontend        | Next.js 14 (App Router) + Tailwind  |
| Real-time UI    | WebSocket                           |
| Containerization| Docker + Docker Compose             |

## Dataset

| Dataset          | Records    | Features           | Used For              |
|-----------------|------------|--------------------|-----------------------|
| creditcard.csv  | 284,807    | V1-V28 (PCA), Amount | EDA analysis only     |
| paysim.csv      | 6,362,620  | type, amount, balances | Training + Streaming  |

> **Lưu ý:** Hai dataset có feature space khác nhau hoàn toàn. Train trên paysim.csv vì
> dữ liệu streaming đến từ paysim.

> **Repo Git:** File CSV không được commit (quá lớn). Xem `data/README.md` để tải dữ liệu và copy `.env.example` → `.env`.

## Deploy (Vercel + Render)

Xem **[DEPLOY.md](./DEPLOY.md)** — frontend lên **Vercel** (`frontend/`), API + Postgres lên **Render** (`render.yaml` + `backend/Dockerfile`). Pipeline Kafka đầy đủ thường chỉ chạy local/Docker; trên cloud cần broker riêng (xem DEPLOY.md).

## Prerequisites

- Docker Desktop (>= 4.0)
- Docker Compose (>= 2.0)
- Python 3.11+ (cho training local)
- 8GB RAM minimum (recommended 16GB)

## Quick Start

### 0. Chuẩn bị

```bash
cp .env.example .env
# Đặt paysim.csv và creditcard.csv vào thư mục data/ (xem data/README.md)
```

### 1. Training Model (chạy local trước)

```bash
# Cài dependencies
pip install -r training/requirements.txt

# Chạy EDA (optional - tạo biểu đồ phân tích)
python training/eda.py

# Train model
python training/train.py
```

Sau khi train xong, thư mục `model/` sẽ có:
- `fraud_model.pkl` — trained model
- `feature_config.json` — feature configuration

### 2. Chạy toàn bộ hệ thống

```bash
# Build và start tất cả services
docker-compose up --build

# Hoặc chạy ở background
docker-compose up --build -d
```

### 3. Truy cập

| Service    | URL                         |
|-----------|----------------------------|
| Frontend  | http://localhost:3000       |
| Backend API| http://localhost:8000      |
| API Docs  | http://localhost:8000/docs  |

## Project Structure

```
fraud-detection/
├── data/
│   ├── creditcard.csv          # Credit card dataset (EDA only)
│   └── paysim.csv              # PaySim dataset (training + streaming)
├── model/
│   ├── fraud_model.pkl          # Trained ML model (generated)
│   └── feature_config.json      # Feature config (generated)
├── training/
│   ├── eda.py                   # Exploratory Data Analysis
│   ├── train.py                 # Model training pipeline
│   ├── requirements.txt
│   └── output/                  # EDA charts (generated)
├── producer/
│   ├── producer.py              # Kafka producer (simulates transactions)
│   ├── requirements.txt
│   └── Dockerfile
├── streaming/
│   ├── spark_job.py             # Kafka consumer: ML + rule-based (Python)
│   ├── requirements.txt
│   └── Dockerfile
├── backend/
│   ├── main.py                  # FastAPI application
│   ├── database.py              # Database connection
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic schemas
│   ├── consumer.py              # Kafka consumer (writes to DB)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                     # Next.js App Router pages
│   ├── components/              # React components
│   ├── lib/                     # API utilities
│   ├── package.json
│   └── Dockerfile
├── docker/
│   └── init.sql                 # Database initialization
├── docker-compose.yml           # Docker orchestration
├── .env.example                 # Mẫu biến môi trường (copy thành .env)
├── rule.md                      # Project specification
└── README.md
```

## API Endpoints

| Method | Endpoint                | Description                    |
|--------|------------------------|--------------------------------|
| GET    | /api/health            | Health check                   |
| GET    | /api/transactions      | Paginated transaction list     |
| GET    | /api/transactions/{id} | Single transaction detail      |
| GET    | /api/frauds            | Paginated fraud alerts         |
| GET    | /api/stats             | Dashboard statistics           |
| GET    | /api/stats/timeline    | Fraud over time (for charts)   |
| GET    | /api/stats/by-type     | Fraud breakdown by type        |
| WS     | /ws/alerts             | Real-time fraud alert stream   |

## Detection Strategy

### 1. Machine Learning (Primary)
- **Model:** Best of RandomForest / GradientBoosting / LogisticRegression
- **Features:** amount, balances, balance_change, balance_error, amount_ratio, transaction_type
- **Handling Imbalance:** class_weight='balanced'
- **Threshold:** fraud_probability >= 0.5

### 2. Rule-Based (Secondary)
- Blacklist destination accounts (từ phân tích fraud trên PaySim)
- Amount > $200,000 (chỉ TRANSFER/CASH_OUT — khớp nhãn PaySim)
- Amount > 80% of sender's balance (TRANSFER/CASH_OUT)
- Balance error != 0 (TRANSFER/CASH_OUT)
- Account completely drained with amount > $10,000 (TRANSFER/CASH_OUT)

### 3. Combined
- Final decision: `fraud = ML_prediction OR rule_based_flag`
- Detection method tracked: 'ml', 'rule', 'both', 'none'

## Monitoring

- Frontend dashboard auto-refreshes every 5 seconds
- WebSocket provides instant fraud alerts
- Streaming service logs detected frauds (`docker-compose logs -f streaming`)
- Producer logs streaming progress

## Troubleshooting

```bash
# Xem logs của từng service
docker-compose logs -f producer
docker-compose logs -f streaming
docker-compose logs -f backend

# Restart service cụ thể
docker-compose restart backend

# Xoá data và rebuild
docker-compose down -v
docker-compose up --build
```
