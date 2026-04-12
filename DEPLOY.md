# Deploy: Vercel (frontend) + Render (API + PostgreSQL)

Kiến trúc Docker local gồm **Kafka + producer + streaming + backend + Postgres + frontend**. Trên **Vercel** và **Render** (free tier) **không chạy được Kafka cluster đầy đủ** như Docker Compose. Cách thực tế:

| Thành phần | Nền tảng | Ghi chú |
|------------|----------|---------|
| **Next.js dashboard** | **Vercel** | Build từ thư mục `frontend/` |
| **FastAPI + REST + WebSocket** | **Render** Web Service (Docker) | File `backend/Dockerfile` |
| **PostgreSQL** | **Render** PostgreSQL | Gắn `DATABASE_URL` vào backend |

Luồng **Kafka → streaming → Kafka → backend** chỉ chạy khi bạn có **broker Kafka** (tự host VPS, [Confluent Cloud](https://www.confluent.io/confluent-cloud/), Aiven, v.v.) và chỉnh biến môi trường. Trên demo cloud đơn giản, backend chạy với **`ENABLE_KAFKA=false`**: API + DB hoạt động; bảng có thể trống hoặc bạn tự seed / chạy pipeline ở chỗ khác.

---

## 1. Render — Backend + Database

### Cách A: Blueprint (file `render.yaml`)

1. Push code lên GitHub.
2. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
3. Chọn repo, Render đọc `render.yaml` → tạo **PostgreSQL** + **Web Service** `fraud-backend`.
4. Đợi deploy xong, copy **Public URL** dạng `https://fraud-backend-xxxx.onrender.com`.

### Cách B: Tạo tay

1. **New** → **PostgreSQL** → tạo DB → copy **Internal Database URL** (hoặc External nếu cần).
2. **New** → **Web Service** → kết nối repo:
   - **Root**: để root repo hoặc chỉ rõ **Dockerfile path**: `backend/Dockerfile`
   - **Docker build context**: `backend`
3. **Environment**:
   - `DATABASE_URL` = connection string Render cung cấp (thường cần thêm `?sslmode=require` nếu kết nối từ ngoài).
   - `ENABLE_KAFKA` = `false`

4. **Health check path**: `/api/health`

**Lưu ý:** Free tier Web Service **sleep sau idle** — lần đầu mở API có thể chậm vài chục giây.

---

## 2. Vercel — Frontend

1. [Vercel](https://vercel.com) → **Add New** → **Project** → Import GitHub repo.
2. **Cấu hình project:**
   - **Framework Preset:** Next.js  
   - **Root Directory:** `frontend` (quan trọng)
3. **Environment Variables:**

   | Name | Value |
   |------|--------|
   | `NEXT_PUBLIC_API_URL` | `https://<tên-service-backend>.onrender.com` (HTTPS, không có dấu `/` cuối) |
   | `NEXT_PUBLIC_WS_URL` | `wss://<tên-service-backend>.onrender.com/ws/alerts` |

4. Deploy. URL Vercel dạng `https://<project>.vercel.app`.

**CORS:** Backend đang `allow_origins=["*"]` — không cần chỉnh cho demo. Production nên thu hẹp theo domain Vercel.

**WebSocket:** Phụ thuộc Render; nếu `wss` lỗi trên free tier, phần “Real-Time Alerts” có thể không kết nối — REST vẫn dùng được.

---

## 3. Khi nào có đủ pipeline Kafka?

1. Tạo cluster Kafka managed (Confluent / Aiven / …), lấy `bootstrap.servers` (có SSL/SASL).
2. Deploy thêm **worker** chạy `producer` + `streaming` (Docker riêng hoặc máy có Docker), trỏ `KAFKA_BOOTSTRAP_SERVERS` tới cluster.
3. Trên Render backend đặt:
   - `ENABLE_KAFKA=true`
   - `KAFKA_BOOTSTRAP_SERVERS=<chuỗi broker>`
   - `DATABASE_URL` như cũ  

Cần chỉnh code Kafka client cho **SASL/SSL** nếu nhà cung cấp yêu cầu (hiện code dùng PLAINTEXT phù hợp Docker nội bộ).

---

## 4. Checklist nhanh

- [ ] Render: backend trả `GET https://.../api/health` → `{"status":"healthy",...}`
- [ ] Vercel: `NEXT_PUBLIC_*` trùng domain Render (https / wss)
- [ ] Không commit `.env`; dùng biến trên dashboard từng nền tảng
