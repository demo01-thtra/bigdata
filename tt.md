# HƯỚNG DẪN TRÌNH BÀY ĐỒ ÁN

## Chủ đề: Quản trị rủi ro & Phát hiện gian lận (Real-time Fraud Detection)

---

## 1. MỞ ĐẦU (2 phút)

**Nói:**
> Nhóm em thực hiện đề tài xây dựng hệ thống phát hiện gian lận theo thời gian thực cho ví điện tử.
> Bối cảnh: Từ 2025, Ngân hàng Nhà nước yêu cầu xác thực sinh trắc học và kiểm soát giao dịch bất thường.
> Hệ thống sử dụng Machine Learning kết hợp Rule-based để tự động phát hiện giao dịch đáng ngờ trên luồng dữ liệu streaming.

**Dataset:**
- `creditcard.csv` (Kaggle Fraud Detection) — dùng để phân tích khám phá (EDA)
- `paysim.csv` (Kaggle PaySim) — dùng để huấn luyện model và mô phỏng streaming

---

## 2. KIẾN TRÚC HỆ THỐNG (3 phút)

**Vẽ/chỉ sơ đồ:**

```
paysim.csv → [Producer] → Kafka → [Streaming Processor] → Kafka → [Backend API] → [Dashboard]
                                        ↓                              ↓
                                   ML Model                       PostgreSQL
                                   + Rules
```

**Giải thích ngắn gọn:**

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| Producer | Python + kafka-python | Đọc CSV, gửi giao dịch vào Kafka topic `transactions` |
| Kafka | Apache Kafka (KRaft) | Message broker trung gian, nhận/gửi dữ liệu streaming |
| Streaming | Python + kafka-python | Nhận giao dịch → Feature Engineering → Dự đoán ML + Rules → Gửi kết quả |
| Backend | FastAPI + PostgreSQL | Lưu DB, cung cấp REST API + WebSocket |
| Frontend | Next.js + Tailwind | Dashboard giám sát real-time |
| Docker | Docker Compose | Orchestration toàn bộ 6 services |

---

## 3. PHẦN TRAINING — MỞ NOTEBOOK

**Mở file:** `training/fraud_detection_analysis.ipynb`

**Chạy:** Kernel → Restart Kernel and Run All

### 3.1 EDA — Phân tích dữ liệu

- **Biểu đồ 1 — Class Imbalance:** Cho thấy tỷ lệ gian lận chỉ ~0.13% → dữ liệu mất cân bằng nghiêm trọng
- **Biểu đồ 2 — Phân bố loại giao dịch:** CASH_OUT và TRANSFER chiếm đa số, cũng là 2 loại duy nhất có fraud
- **Biểu đồ 3 — Phân bố số tiền:** Giao dịch fraud thường có amount lớn hơn bình thường
- **Biểu đồ 4 — Balance Error:** Giao dịch fraud thường có sai lệch số dư (balance error ≠ 0)

**Nói:**
> Từ EDA, em rút ra: cần tập trung vào TRANSFER và CASH_OUT, xử lý class imbalance, và tạo feature balance_error.

### 3.2 Feature Engineering

**Chỉ code trong notebook:**

> Em tạo thêm các feature phái sinh từ dữ liệu gốc:
> - `balance_change_orig/dest`: thay đổi số dư
> - `balance_error_orig/dest`: sai lệch kế toán (giao dịch hợp lệ phải ≈ 0)
> - `amount_ratio`: tỷ lệ amount / số dư (>1 là đáng ngờ)
> - One-hot encoding loại giao dịch

### 3.3 Kết quả Training

**Chỉ bảng so sánh 3 model:**

| Model | F1-Score | Accuracy | ROC-AUC |
|---|---|---|---|
| Logistic Regression | Baseline | ~ | ~ |
| Random Forest | **0.997** | **99.99%** | **0.999** |
| Gradient Boosting | Cao | Cao | Cao |

**Nói:**
> Em chọn **Random Forest** vì F1-Score cao nhất. F1 là metric chính vì dữ liệu mất cân bằng — mà Accuracy không đủ tin cậy.

### 3.4 Blacklist

**Nói:**
> Ngoài ML, em còn trích xuất danh sách 47 tài khoản đích nhận tiền nhiều nhất từ giao dịch fraud → tạo Blacklist. Streaming processor sẽ kiểm tra tài khoản đích có trong Blacklist không.

---

## 4. DEMO HỆ THỐNG CHẠY (5 phút)

### 4.1 Khởi động

```bash
docker-compose up --build
```

**Nói:**
> Một lệnh duy nhất khởi động 6 services: Kafka, PostgreSQL, Producer, Streaming, Backend, Frontend.

### 4.2 Mở Dashboard

Truy cập: **http://localhost:3000**

- **Stats Cards**: Tổng giao dịch, số fraud phát hiện, tỷ lệ fraud, tổng tiền nghi ngờ
- **Biểu đồ Fraud by Type**: Cho thấy TRANSFER và CASH_OUT là loại fraud nhiều nhất
- **Timeline Chart**: Biểu đồ fraud theo thời gian
- **Real-Time Alerts**: Cảnh báo fraud tức thì qua WebSocket (đèn xanh = đang kết nối)
- **Transaction Table**: Bảng giao dịch, highlight màu đỏ cho fraud

### 4.3 API Documentation

Truy cập: **http://localhost:8000/docs**

**Chỉ cho thầy:**
- `GET /api/stats` → thống kê tổng quan
- `GET /api/transactions` → danh sách giao dịch (có phân trang, lọc)
- `GET /api/frauds` → danh sách cảnh báo fraud
- `GET /api/stats/by-type` → thống kê theo loại giao dịch
- `WS /ws/alerts` → WebSocket nhận cảnh báo real-time

---

## 5. CHIẾN LƯỢC PHÁT HIỆN (2 phút)

**Nói:**
> Hệ thống kết hợp 2 phương pháp song song:

### Phương pháp 1: ML Model
- Random Forest đã train trên PaySim
- Dự đoán probability > 0.5 → fraud

### Phương pháp 2: Rule-based
- Số tiền > 200,000 → cảnh báo
- TRANSFER/CASH_OUT chiếm > 80% số dư → cảnh báo
- Balance error ≠ 0 → giao dịch bất thường
- Tài khoản đích trong Blacklist → cảnh báo

> Kết quả cuối: fraud = ML dự đoán HOẶC Rule vi phạm → giảm false negative.

---

## 6. KẾT LUẬN (1 phút)

**Nói:**

> Hệ thống đáp ứng yêu cầu:
> - Phát hiện gian lận **real-time** qua Kafka streaming
> - **Dual strategy**: ML + Rules tăng độ chính xác
> - **Blacklist** tài khoản nghi ngờ
> - Dashboard giám sát trực quan, cảnh báo tức thời qua WebSocket
> - Toàn bộ hệ thống đóng gói Docker, chạy 1 lệnh

---

## CHUẨN BỊ TRƯỚC KHI TRÌNH BÀY

### Checklist:

- [ ] Docker Desktop đang chạy
- [ ] Chạy `docker-compose up --build` trước 5 phút
- [ ] Mở sẵn 3 tab trình duyệt:
  - Tab 1: http://localhost:3000 (Dashboard)
  - Tab 2: http://localhost:8000/docs (API Docs)
  - Tab 3: Notebook `fraud_detection_analysis.ipynb` (đã Run All)
- [ ] Đợi ~1 phút cho producer gửi đủ dữ liệu → Dashboard hiện số liệu

### Nếu thầy hỏi:

| Câu hỏi | Trả lời |
|---|---|
| Sao không dùng creditcard.csv để train? | Vì feature space khác hoàn toàn (PCA V1-V28 vs amount/balance). Train trên paysim vì streaming data là paysim. |
| Sao chọn Random Forest? | F1-Score cao nhất, quan trọng vì class imbalance (0.13% fraud). |
| Sao cần cả ML lẫn Rules? | ML bắt pattern phức tạp, Rules bắt case đơn giản nhưng quan trọng (blacklist, high amount). Kết hợp giảm sót lọt. |
| Kafka dùng để làm gì? | Message broker trung gian, decouple producer và consumer, đảm bảo streaming real-time. |
| WebSocket hoạt động sao? | Backend nhận fraud từ Kafka → push ngay lập tức tới Dashboard qua WebSocket, không cần refresh. |
| Docker Compose tác dụng gì? | Orchestration 6 services, chạy 1 lệnh thay vì setup từng cái. |
| EDA nói fraud chỉ ở TRANSFER/CASH_OUT mà dashboard lại nhiều CASH_IN? | Trước đây: ML vẫn chấm điểm mọi loại giao dịch (có thể dương tính giả với CASH_IN) và rule “số tiền lớn”/blacklist áp cho mọi loại. **Đã chỉnh** streaming chỉ coi ML + các rule đó là fraud khi `type` là TRANSFER hoặc CASH_OUT — khớp nhãn PaySim. |

---

## CẤU TRÚC THƯ MỤC

```
BigData/
├── data/                   ← 2 dataset gốc
├── model/                  ← Model đã train (fraud_model.pkl)
├── training/
│   ├── fraud_detection_analysis.ipynb  ← Notebook show thầy
│   ├── train.py            ← Script training
│   ├── eda.py              ← Script EDA
│   └── output/             ← Biểu đồ đã export
├── producer/               ← Kafka producer (mô phỏng giao dịch)
├── streaming/              ← Streaming processor (ML + Rules)
├── backend/                ← FastAPI + PostgreSQL
├── frontend/               ← Next.js Dashboard
├── docker/                 ← SQL init
├── docker-compose.yml      ← Orchestration
└── .env                    ← Config
```
