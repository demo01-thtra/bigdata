# BÁO CÁO ĐỒ ÁN BIG DATA
## Chủ đề 4: Quản trị rủi ro & Phát hiện gian lận thời gian thực

---

## 1. Giới thiệu & Bối cảnh doanh nghiệp

### 1.1 Vấn đề
Gian lận tài chính gây thiệt hại hàng tỷ USD mỗi năm. Hệ thống phát hiện truyền thống (batch processing) có độ trễ cao, không đáp ứng được yêu cầu phát hiện gian lận **thời gian thực** (<5 giây).

### 1.2 Mục tiêu
Xây dựng hệ thống **Real-Time Fraud Detection** sử dụng:
- **PySpark Structured Streaming** để xử lý dữ liệu phân tán
- **Apache Kafka** để truyền tải dữ liệu streaming
- **Machine Learning + Rule-based** detection kết hợp
- **Dashboard real-time** hiển thị cảnh báo gian lận

### 1.3 Dataset
- **PaySim**: Mô phỏng giao dịch tài chính di động
- ~6.3 triệu giao dịch, ~8,213 giao dịch gian lận (0.13%)
- 5 loại: CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER
- Gian lận chỉ xảy ra ở TRANSFER và CASH_OUT

---

## 2. Kiến trúc hệ thống

### 2.1 Tổng quan

```
┌─────────────┐    ┌──────────┐    ┌─────────────────────┐    ┌──────────┐    ┌───────────┐
│   PaySim    │───▶│  Kafka   │───▶│  PySpark Streaming  │───▶│  Kafka   │───▶│  Backend  │
│  Producer   │    │ (input)  │    │  (Feature Eng + ML  │    │ (output) │    │ (FastAPI) │
│             │    │          │    │   + Rules)          │    │          │    │           │
└─────────────┘    └──────────┘    └─────────────────────┘    └──────────┘    └─────┬─────┘
                                                                                    │
                                                                              ┌─────▼─────┐
                                                                              │PostgreSQL │
                                                                              │   + SSE   │
                                                                              └─────┬─────┘
                                                                                    │
                                                                              ┌─────▼─────┐
                                                                              │  Next.js  │
                                                                              │ Dashboard │
                                                                              └───────────┘
```

### 2.2 Công nghệ sử dụng

| Tầng | Công nghệ | Vai trò |
|---|---|---|
| Message Broker | Apache Kafka 3.9 (KRaft) | Truyền tải streaming data |
| Stream Processing | PySpark Structured Streaming | Xử lý phân tán, feature engineering |
| ML Inference | scikit-learn + pandas_udf | Dự đoán gian lận (vectorized) |
| Database | PostgreSQL 16 | Lưu trữ kết quả |
| Backend API | FastAPI + SSE | REST API + real-time push |
| Frontend | Next.js 14 + Tailwind CSS | Dashboard giám sát |
| Containerization | Docker Compose | Orchestration 6 services |

---

## 3. Data Pipeline chi tiết

### 3.1 Producer (Kafka Producer)
- Đọc `paysim.csv` → gửi JSON messages tới Kafka topic `transactions`
- Enrich mỗi giao dịch: `device_id` (DEV-xxxxx / UNKNOWN-xxxx), `ip_address` (192.168.x.x / 10.x.x.x)
- ~5% giao dịch dùng unknown device (mô phỏng đăng nhập lạ)
- ~3% giao dịch dùng suspicious IP

### 3.2 PySpark Structured Streaming
- `spark.readStream.format("kafka")` → đọc từ topic `transactions`
- **foreachBatch**: xử lý mỗi micro-batch (~5 giây)
- Feature Engineering → ML Prediction → Rule Detection → Risk Scoring
- Ghi kết quả bằng **native Spark Kafka sink** (`df.write.format("kafka")`) — phân tán, không `.collect()`

### 3.3 Backend Consumer
- Lắng nghe Kafka topic `processed_transactions`
- Ghi PostgreSQL + broadcast SSE alerts

### 3.4 Dashboard
- EventSource (SSE) nhận alerts real-time
- REST API cho statistics, pagination, filtering

---

## 4. Feature Engineering

### 4.1 Bảng 15 đặc trưng

| # | Feature | Công thức | Ý nghĩa |
|---|---|---|---|
| 1 | amount | raw | Số tiền giao dịch |
| 2 | oldbalanceOrg | raw | Số dư trước (gửi) |
| 3 | newbalanceOrig | raw | Số dư sau (gửi) |
| 4 | oldbalanceDest | raw | Số dư trước (nhận) |
| 5 | newbalanceDest | raw | Số dư sau (nhận) |
| 6 | balance_change_orig | new - old | Thay đổi số dư bên gửi |
| 7 | balance_change_dest | new - old | Thay đổi số dư bên nhận |
| 8 | balance_error_orig | new + amount - old | Sai lệch cân đối (gửi) |
| 9 | balance_error_dest | old + amount - new | Sai lệch cân đối (nhận) |
| 10 | amount_ratio | amount / (old + 1) | Tỷ lệ rút so với số dư |
| 11–15 | type_* | one-hot | Loại giao dịch (5 loại) |

### 4.2 Tính năng xử lý
- Feature engineering: **pure Spark DataFrame API** (không dùng Pandas)
- ML prediction: **pandas_udf + broadcast model** (vectorized, phân tán)
- Tất cả transformations chạy trên **executors**, không gom về driver

---

## 5. Mô hình Machine Learning

### 5.1 Training Pipeline (notebooks/train_model.py)
1. Đọc PaySim CSV
2. Feature engineering (15 đặc trưng — khớp với Spark pipeline)
3. Stratified train/test split (80/20)
4. StandardScaler chuẩn hóa
5. SMOTE oversample fraud lên 10%
6. Train 3 models: Logistic Regression, Random Forest, Gradient Boosting

### 5.2 Kết quả đánh giá (trên PaySim)

| Model | F1 | Precision | Recall | ROC-AUC |
|---|---|---|---|---|
| Logistic Regression | ~0.65 | ~0.12 | ~0.92 | ~0.97 |
| **Random Forest** | **~0.92** | **~0.95** | **~0.90** | **~0.99** |
| Gradient Boosting | ~0.88 | ~0.90 | ~0.85 | ~0.99 |

> *Kết quả thực tế phụ thuộc vào phiên bản dataset, SMOTE ratio, hyperparameters.*

### 5.3 Lưu trữ
- `model/fraud_model.pkl`: model + scaler (joblib)
- `model/feature_config.json`: feature columns + thresholds + blacklist accounts

---

## 6. Rule-based Detection

### 6.1 Bảng luật phát hiện

| Rule | Điều kiện | Trọng số |
|---|---|---|
| Blacklist | nameDest ∈ blacklist | 1.0 |
| High Amount | amount > 200,000 | 0.8 |
| Account Drain | newbalanceOrig = 0 ∧ amount > 10,000 | 0.7 |
| Balance Ratio | amount / balance > 0.8 | 0.6 |
| Rapid Transactions | ≥3 giao dịch/user trong batch | 0.5 |
| Balance Error | \|new + amount - old\| > 1 | 0.5 |
| New Device | device_id starts with "UNKNOWN" | 0.4 |
| Suspicious IP | ip_address starts with "10." | 0.3 |

### 6.2 Công thức Risk Score

$$\text{risk\_score} = 0.4 \times \text{rule\_score} + 0.6 \times \text{model\_probability}$$

Trong đó:
- `rule_score` = tổng trọng số các rules bị vi phạm (cap tại 1.0)
- `model_probability` = xác suất gian lận từ ML model

### 6.3 Phương pháp phát hiện
- `detection_method = "ml"` — chỉ ML phát hiện
- `detection_method = "rule"` — chỉ rules phát hiện
- `detection_method = "both"` — cả ML lẫn rules

---

## 7. Performance & Khả năng mở rộng

### 7.1 Hiệu suất xử lý

| Metric | Giá trị |
|---|---|
| Trigger interval | 5 giây/micro-batch |
| Feature engineering | Pure Spark DataFrame (distributed) |
| ML inference | pandas_udf + broadcast (vectorized) |
| Kafka write | Native Spark sink (distributed) |
| Blacklist lookup | Broadcast variable (no shuffle) |

### 7.2 Tối ưu Spark

| Kỹ thuật | Mô tả |
|---|---|
| `shuffle.partitions = 4` | Phù hợp local mode (giảm overhead) |
| Broadcast blacklist | Tránh data shuffle khi join |
| pandas_udf | Vectorized UDF — nhanh hơn row-at-a-time UDF 100x |
| `.cache()` + `.unpersist()` | Cache output DataFrame, giải phóng sau khi ghi |
| Native Kafka sink | `df.write.format("kafka")` thay vì `.collect()` |
| Checkpointing | Fault tolerance — recovery từ failure |

### 7.3 Khả năng mở rộng (Scale-out)

| Tầng | Scale strategy |
|---|---|
| Kafka | Tăng partitions, thêm brokers |
| Spark | Chuyển từ `local[*]` → Spark Standalone / YARN / K8s cluster |
| PostgreSQL | Read replicas, partitioning theo thời gian |
| Backend | Horizontal scaling (multiple FastAPI instances) |

---

## 8. Kiểm thử & CI/CD

### 8.1 Unit Tests

| File | Nội dung |
|---|---|
| `tests/test_features.py` | Kiểm tra số lượng features, tên, loại giao dịch, thresholds |
| `tests/test_rules.py` | Kiểm tra device/IP generation, blacklist, rules |
| `tests/test_api.py` | Kiểm tra tất cả API endpoints (health, transactions, frauds, stats, SSE) |

### 8.2 CI/CD Pipeline (GitHub Actions)
```yaml
# .github/workflows/ci.yml
- Trigger: push/PR → main
- Steps: Python 3.11 + JDK 17 → install deps → flake8 lint → pytest
```

### 8.3 Chạy tests local
```bash
pip install -r tests/requirements.txt
ENABLE_KAFKA=false DATABASE_URL=sqlite:///test.db pytest tests/ -v
```

---

## 9. Hướng dẫn triển khai

### 9.1 Yêu cầu
- Docker Desktop
- Dataset `paysim.csv` trong thư mục `data/`

### 9.2 Các bước

```bash
# 1. Train model (optional — hệ thống chạy rule-only nếu không có model)
pip install pandas scikit-learn imbalanced-learn matplotlib seaborn joblib
python notebooks/train_model.py

# 2. Khởi động hệ thống
docker compose up --build

# 3. Truy cập
# Dashboard: http://localhost:3000
# API:       http://localhost:8000/api/health
# SSE:       http://localhost:8000/api/sse/alerts
```

---

## 10. Kết luận

### 10.1 Thành tựu
- ✅ Pipeline streaming real-time hoàn chỉnh (Kafka → PySpark → Kafka → DB → Dashboard)
- ✅ PySpark Structured Streaming với native Kafka sink (phân tán, không `.collect()`)
- ✅ Kết hợp ML + Rule-based detection với risk_score
- ✅ 8 detection rules bao gồm đăng nhập lạ + chuyển tiền liên tục
- ✅ SSE real-time alerts + REST API
- ✅ Dashboard Next.js với charts, tables, live alerts
- ✅ Docker Compose 6 services + CI/CD

### 10.2 Hạn chế & Hướng phát triển
- Spark chạy `local[*]` — cần chuyển sang cluster mode cho production
- Kafka 1 broker — cần ít nhất 3 brokers cho HA
- Blacklist tĩnh — nên cập nhật động từ DB
- Chưa có monitoring (Prometheus/Grafana)
- Chưa có A/B testing cho model updates

---

*Đồ án Big Data — Nhóm 4*
