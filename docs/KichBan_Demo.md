# KỊCH BẢN DEMO CHI TIẾT
## Hệ thống phát hiện gian lận giao dịch tài chính thời gian thực

**Thời lượng demo: 5–7 phút**

---

## CHUẨN BỊ TRƯỚC KHI DEMO

### Checklist:
- [ ] Docker Desktop đang chạy
- [ ] Mở sẵn terminal (PowerShell / CMD)
- [ ] Mở sẵn browser (Chrome/Edge) — tab trống → `http://localhost:3000`
- [ ] Tắt các app chiếm port: 3000, 8000, 9092, 5432
- [ ] Mở sẵn VS Code với project `bigdata/` (để show code nếu bị hỏi)

### Khởi động hệ thống TRƯỚC buổi demo (3–5 phút để containers ổn định):
```bash
cd c:\BAITAP\bigdata
docker compose up -d --build
```

### Kiểm tra tất cả đang chạy:
```bash
docker compose ps
```
→ Phải thấy 6 containers: fraud-kafka, fraud-postgres, fraud-producer, fraud-streaming, fraud-backend, fraud-frontend — tất cả đều "Up"

### Kiểm tra Spark đang xử lý:
```bash
docker logs fraud-streaming --tail 5
```
→ Phải thấy: `Batch X: 10 txns (Y fraud)`

---

## PHẦN 1: GIỚI THIỆU HỆ THỐNG (30 giây)

### Lời nói:
> "Em xin demo hệ thống phát hiện gian lận thời gian thực. Hệ thống gồm 6 services chạy trên Docker, dữ liệu từ PaySim được gửi qua Kafka, xử lý bằng PySpark Structured Streaming, kết quả hiển thị trên dashboard Next.js."

### Thao tác:
1. Mở terminal → chạy:
```bash
docker compose ps
```
2. **Chỉ vào màn hình** và giải thích:
> "Đây là 6 containers: Kafka làm message broker, PostgreSQL lưu trữ, Producer mô phỏng giao dịch, Spark Streaming xử lý và phát hiện gian lận, Backend API bằng FastAPI, và Frontend dashboard bằng Next.js."

---

## PHẦN 2: SHOW SPARK STREAMING LOGS (1 phút)

### Thao tác:
```bash
docker logs fraud-streaming --tail 20
```

### Lời nói:
> "Đây là logs của Spark Streaming. Mỗi 5 giây, hệ thống xử lý một micro-batch.

> Ví dụ dòng này: **'Batch 15: 10 txns (2 fraud)'** — nghĩa là batch thứ 15 có 10 giao dịch, trong đó 2 giao dịch bị phát hiện gian lận.

> Dòng **'Total: 150 txns, 25 frauds (16.67%)'** là thống kê tích lũy — tổng cộng đã xử lý 150 giao dịch, phát hiện 25 gian lận.

> Toàn bộ quá trình này chạy phân tán trên Spark — không có bước nào gom dữ liệu về driver. Kết quả ghi ra Kafka bằng native Spark Kafka sink."

### Chạy thêm (optional — nếu muốn show real-time):
```bash
docker logs fraud-streaming --follow
```
*(Ctrl+C để dừng sau 10-15 giây)*

> "Có thể thấy batches liên tục được xử lý mỗi 5 giây."

---

## PHẦN 3: DASHBOARD — TRANG CHÍNH (1.5 phút)

### Thao tác:
Mở browser → `http://localhost:3000` → tự redirect sang `/dashboard`

### Lời nói khi chỉ vào từng phần:

#### 3a. Stats Cards (4 thẻ trên cùng):
> "Phía trên là 4 thẻ thống kê tổng quan:
> - **Total Transactions**: tổng số giao dịch đã xử lý
> - **Fraud Detected**: số giao dịch gian lận phát hiện được
> - **Fraud Rate**: tỷ lệ gian lận (%)
> - **Amount at Risk**: tổng số tiền bị đánh dấu gian lận
>
> Các số liệu này **tự động cập nhật mỗi 5 giây** — không cần refresh trang. *(Chỉ vào chấm xanh 'Auto-refreshing every 5s' góc phải)*"

#### 3b. Timeline Chart (biểu đồ giữa):
> "Biểu đồ này hiển thị số lượng giao dịch và gian lận theo thời gian — 24 giờ gần nhất. Đường xanh là tổng giao dịch, đường đỏ là gian lận. Có thể hover để xem chi tiết từng thời điểm."

*(Hover chuột lên biểu đồ để show tooltip)*

#### 3c. Real-Time Alerts (bên phải):
> "Đây là phần quan trọng nhất — **Real-Time Alerts**. Chấm xanh 'Connected' cho biết frontend đang kết nối tới backend qua **Server-Sent Events (SSE)**. Khi PySpark phát hiện giao dịch gian lận, cảnh báo **đẩy tự động** tới đây mà không cần refresh."

*(Chờ vài giây — nếu có alert mới xuất hiện):*
> "Đây — vừa có một alert mới. Có thể thấy:
> - **Loại giao dịch**: TRANSFER hoặc CASH_OUT
> - **Số tiền**: ví dụ $352,000
> - **Detection method**: 'rule', 'ml', hoặc 'both'
> - **Reason**: lý do phát hiện — ví dụ 'High amount; New/unknown device'
> - **Risk score**: 40% — tính theo công thức 0.4×rule_score + 0.6×ml_probability"

#### 3d. Fraud by Type (biểu đồ dưới):
> "2 biểu đồ này cho thấy phân bổ gian lận theo loại giao dịch. Bar chart bên trái so sánh tổng vs gian lận, Pie chart bên phải cho thấy tỷ lệ phần trăm. Đúng như dataset PaySim — gian lận chỉ xảy ra ở **TRANSFER và CASH_OUT**."

#### 3e. Transaction Table (bảng dưới cùng):
> "Cuối cùng là bảng 10 giao dịch gần nhất — hiển thị ID, loại, số tiền, trạng thái fraud, risk score."

---

## PHẦN 4: TRANG TRANSACTIONS (1 phút)

### Thao tác:
Click **"Transactions"** trên navbar

### Lời nói:
> "Trang Transactions hiển thị toàn bộ giao dịch đã xử lý với phân trang."

#### 4a. Filter buttons:
> "Có 3 bộ lọc: **All** — tất cả, **Fraud** — chỉ gian lận, **Safe** — chỉ an toàn."

*(Click nút **Fraud**)*

> "Khi chọn **Fraud**, chỉ hiển thị giao dịch bị phát hiện gian lận. Mỗi dòng có:
> - **Transaction ID**
> - **Type**: TRANSFER hoặc CASH_OUT
> - **Amount**: số tiền giao dịch
> - **Status**: badge đỏ 'Fraud'
> - **Risk Score**: điểm rủi ro
> - **Detection**: phương thức phát hiện (rule / ml / both)"

#### 4b. Pagination:
*(Nếu có nhiều trang, click Next)*
> "Hệ thống phân trang — mỗi trang 20 giao dịch. Khi dữ liệu tăng lên, có thể duyệt qua các trang."

#### 4c. So sánh Fraud vs Safe:
*(Click nút **Safe**)*
> "Khi chọn Safe — giao dịch an toàn có risk_score = 0, detection_method = none. Hệ thống phân biệt rõ ràng."

*(Click lại **All** để reset)*

---

## PHẦN 5: TRANG ALERTS (1 phút)

### Thao tác:
Click **"Alerts"** trên navbar

### Lời nói:
> "Trang Alerts chia làm 2 phần:

> **Bên trái — Real-Time Alerts**: giống như ở Dashboard, nhận cảnh báo trực tiếp qua SSE. Chấm xanh 'Connected' = đang kết nối.

> **Bên phải — Alert History**: lịch sử tất cả giao dịch gian lận đã phát hiện, lấy từ PostgreSQL qua REST API. Mỗi alert hiển thị:
> - **Alert type**: 'rule' hoặc 'ml' hoặc 'both'
> - **Risk score**: ví dụ Risk: 40%
> - **Transaction ID**: mã giao dịch (cắt ngắn)
> - **Timestamp**: thời gian phát hiện"

*(Chỉ vào một alert cụ thể)*
> "Ví dụ alert này — Risk: 40%, detection method: rule — có nghĩa giao dịch bị phát hiện bởi business rules với risk_score = 0.4. Có thể là High Amount hoặc New Device."

---

## PHẦN 6: SHOW API BACKEND (45 giây)

### Thao tác:
Mở tab mới trong browser → `http://localhost:8000/api/health`

### Lời nói:
> "Backend chạy trên FastAPI. Đây là health check — hệ thống đang hoạt động bình thường."

*(Sửa URL thành `http://localhost:8000/api/stats`)*

> "API endpoint `/api/stats` trả về JSON — tổng giao dịch, tổng gian lận, tỷ lệ, tổng tiền. Dashboard gọi API này mỗi 5 giây."

*(Optional — nếu muốn show thêm: `http://localhost:8000/api/stats/by-type`)*

> "API `/api/stats/by-type` phân tích theo loại giao dịch — CASH_IN, CASH_OUT, TRANSFER... Dữ liệu này vẽ biểu đồ Fraud by Type trên dashboard."

---

## PHẦN 7: SHOW CODE NHANH (45 giây — optional, nếu có thời gian)

### Thao tác:
Chuyển sang VS Code → mở `streaming/spark_job.py`

### Lời nói:
> "Đây là file xử lý chính — `spark_job.py`.

*(Scroll đến hàm `add_features`)*
> "Feature engineering — 15 đặc trưng, toàn bộ bằng Spark DataFrame API, chạy trên executors."

*(Scroll đến phần `rule_score`)*
> "Rule-based detection — 8 rules với trọng số từ 0.3 đến 1.0."

*(Scroll đến `df.write.format("kafka")`)*
> "Kết quả ghi ra Kafka bằng native Spark sink — phân tán, không `.collect()`."

---

## PHẦN 8: KẾT THÚC DEMO (15 giây)

### Lời nói:
> "Như vậy hệ thống đang phát hiện gian lận real-time — từ lúc giao dịch phát sinh đến khi alert hiển thị trên dashboard trong vòng dưới 5 giây. Toàn bộ chạy trên Docker Compose với 6 services. Cảm ơn thầy/cô đã lắng nghe, em xin nhận câu hỏi."

---

## XỬ LÝ SỰ CỐ THƯỜNG GẶP

### Sự cố 1: Dashboard hiển thị "Connection Error"
```bash
# Kiểm tra backend
docker logs fraud-backend --tail 10
# Restart nếu cần
docker compose restart backend
```
**Nói:** "Backend đang khởi động lại, chờ vài giây."

### Sự cố 2: Real-Time Alerts hiển thị "Disconnected" (chấm đỏ)
```bash
docker compose restart backend
```
→ Refresh trang browser (F5)

### Sự cố 3: Không có dữ liệu (dashboard trống)
```bash
# Kiểm tra producer đang gửi data
docker logs fraud-producer --tail 5
# Kiểm tra streaming đang xử lý
docker logs fraud-streaming --tail 5
```
**Nếu producer hết data (đã gửi hết CSV):**
```bash
docker compose restart producer
```

### Sự cố 4: Streaming container restart loop
```bash
docker logs fraud-streaming --tail 20
# Rebuild nếu cần
docker compose build streaming --no-cache
docker compose up streaming -d --force-recreate
```

### Sự cố 5: Port conflict (port đã bị chiếm)
```bash
# Kiểm tra port
netstat -ano | findstr :3000
netstat -ano | findstr :8000
# Kill process theo PID
taskkill /PID <PID> /F
```

---

## TIMELINE TỔNG THỂ

| Thời gian | Phần | Nội dung |
|---|---|---|
| 0:00 – 0:30 | Phần 1 | Giới thiệu + `docker compose ps` |
| 0:30 – 1:30 | Phần 2 | Spark Streaming logs |
| 1:30 – 3:00 | Phần 3 | Dashboard (stats, charts, alerts, table) |
| 3:00 – 4:00 | Phần 4 | Transactions (filter, pagination) |
| 4:00 – 5:00 | Phần 5 | Alerts page (real-time + history) |
| 5:00 – 5:45 | Phần 6 | API Backend (health, stats) |
| 5:45 – 6:30 | Phần 7 | Code walkthrough (optional) |
| 6:30 – 6:45 | Phần 8 | Kết thúc + mời Q&A |

**Tổng: ~6–7 phút**

---

## MẸO DEMO HIỆU QUẢ

1. **Khởi động hệ thống TRƯỚC 5 phút** — để dữ liệu tích lũy, dashboard có nhiều data đẹp hơn
2. **Phóng to browser** (Ctrl + "+") — để người xem nhìn rõ số liệu và biểu đồ
3. **Dùng terminal font size lớn** — để logs đọc được từ xa
4. **Nếu hết thời gian** — bỏ Phần 6 + 7, tập trung vào Dashboard + Alerts
5. **Khi hover chart** — di chuột chậm để tooltip hiện rõ ràng
6. **Nếu có alert mới pop up** — dừng lại và chỉ: "Đây, alert vừa đẩy real-time"
7. **Luôn mở sẵn backup terminal** — phòng trường hợp cần restart service
