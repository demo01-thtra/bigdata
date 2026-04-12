# Dữ liệu

Đặt hai file CSV sau vào thư mục này (không commit lên Git vì dung lượng lớn):

| File | Nguồn gợi ý |
|------|----------------|
| `paysim.csv` | Kaggle — *PaySim* (mô phỏng giao dịch ví) |
| `creditcard.csv` | Kaggle — *Credit Card Fraud Detection* (chỉ dùng EDA) |

Sau khi có file, chạy `python training/train.py` để tạo `model/` (nếu chưa có), rồi `docker-compose up --build`.
