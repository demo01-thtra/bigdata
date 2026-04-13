# %% [markdown]
# # Huấn luyện Mô hình Phát hiện Gian lận
# ## Đồ án Big Data — Chủ đề 4: Quản trị rủi ro & Phát hiện gian lận
#
# **Pipeline:**
# 1. Đọc & khám phá dữ liệu PaySim (EDA)
# 2. Feature Engineering — 15 đặc trưng (khớp với Spark streaming)
# 3. Xử lý mất cân bằng lớp (SMOTE)
# 4. Huấn luyện 3 mô hình: Logistic Regression, Random Forest, Gradient Boosting
# 5. Đánh giá: F1, Precision, Recall, ROC-AUC, Confusion Matrix
# 6. Lưu mô hình tốt nhất → `model/fraud_model.pkl`

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    roc_curve, f1_score, precision_score, recall_score,
)
from imblearn.over_sampling import SMOTE
import joblib
import json
import os
import warnings

warnings.filterwarnings("ignore")
sns.set_style("whitegrid")
print("✓ Libraries loaded")

# %% [markdown]
# ## 1. Đọc dữ liệu PaySim
# Dataset PaySim mô phỏng giao dịch tài chính di động.
# ~6.3 triệu giao dịch, ~8,213 giao dịch gian lận (0.13%).
#
# **Nguồn:** https://www.kaggle.com/datasets/ealaxi/paysim1

# %%
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "paysim.csv")
df = pd.read_csv(DATA_PATH)
print(f"Shape: {df.shape}")
print(f"\nColumns: {list(df.columns)}")
print(f"\nData types:\n{df.dtypes}")
df.head()

# %% [markdown]
# ## 2. Khám phá dữ liệu (EDA)

# %%
print("=" * 60)
print("PHÂN BỐ NHÃN")
print("=" * 60)
print(df["isFraud"].value_counts())
print(f"\nTỷ lệ gian lận: {df['isFraud'].mean()*100:.4f}%")
print(f"Số giao dịch gian lận: {df['isFraud'].sum():,}")

print("\n" + "=" * 60)
print("GIAN LẬN THEO LOẠI GIAO DỊCH")
print("=" * 60)
fraud_by_type = (
    df.groupby("type")
    .agg(total=("isFraud", "count"), frauds=("isFraud", "sum"))
    .assign(fraud_rate_pct=lambda x: x["frauds"] / x["total"] * 100)
)
print(fraud_by_type)

print("\n" + "=" * 60)
print("THỐNG KÊ SỐ TIỀN")
print("=" * 60)
for label, sub in [("Toàn bộ", df), ("Gian lận", df[df["isFraud"] == 1])]:
    print(f"\n{label}:")
    print(f"  Min:    {sub['amount'].min():>15,.2f}")
    print(f"  Median: {sub['amount'].median():>15,.2f}")
    print(f"  Mean:   {sub['amount'].mean():>15,.2f}")
    print(f"  Max:    {sub['amount'].max():>15,.2f}")

# %%
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# 1. Phân bố Fraud vs Non-Fraud
ax = axes[0]
counts = df["isFraud"].value_counts()
ax.bar(["Non-Fraud", "Fraud"], counts.values, color=["steelblue", "crimson"])
ax.set_title("Phân bố Fraud vs Non-Fraud")
ax.set_ylabel("Số lượng giao dịch")
for i, v in enumerate(counts.values):
    ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=9)

# 2. Fraud theo loại giao dịch
ax = axes[1]
fraud_by_type["frauds"].plot.bar(ax=ax, color="crimson")
ax.set_title("Số giao dịch gian lận theo loại")
ax.set_ylabel("Số lượng")
ax.set_xticklabels(ax.get_xticklabels(), rotation=45)

# 3. Phân bố amount
ax = axes[2]
ax.hist(
    df[df["isFraud"] == 1]["amount"].clip(upper=5e6),
    bins=50, color="crimson", alpha=0.7, label="Fraud",
)
ax.hist(
    df[df["isFraud"] == 0].sample(10000, random_state=42)["amount"].clip(upper=5e6),
    bins=50, color="steelblue", alpha=0.5, label="Non-Fraud (sample 10k)",
)
ax.set_title("Phân bố số tiền giao dịch")
ax.set_xlabel("Amount")
ax.legend()

plt.tight_layout()
os.makedirs(os.path.join(os.path.dirname(__file__), "..", "docs"), exist_ok=True)
plt.savefig(
    os.path.join(os.path.dirname(__file__), "..", "docs", "eda_charts.png"),
    dpi=150, bbox_inches="tight",
)
plt.show()
print("✓ Biểu đồ EDA đã lưu → docs/eda_charts.png")

# %% [markdown]
# ## 3. Feature Engineering
# Tạo **15 đặc trưng** giống hệt Spark streaming pipeline (`streaming/spark_job.py`):
# - 5 raw: `amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest`
# - 5 derived: `balance_change_orig/dest, balance_error_orig/dest, amount_ratio`
# - 5 one-hot: `type_CASH_IN, type_CASH_OUT, type_DEBIT, type_PAYMENT, type_TRANSFER`

# %%
FEATURE_COLS = [
    "amount", "oldbalanceOrg", "newbalanceOrig",
    "oldbalanceDest", "newbalanceDest",
    "balance_change_orig", "balance_change_dest",
    "balance_error_orig", "balance_error_dest",
    "amount_ratio",
    "type_CASH_IN", "type_CASH_OUT", "type_DEBIT",
    "type_PAYMENT", "type_TRANSFER",
]

# Derived features — PHẢI KHỚP VỚI spark_job.py add_features()
df["balance_change_orig"] = df["newbalanceOrig"] - df["oldbalanceOrg"]
df["balance_change_dest"] = df["newbalanceDest"] - df["oldbalanceDest"]
df["balance_error_orig"] = df["newbalanceOrig"] + df["amount"] - df["oldbalanceOrg"]
df["balance_error_dest"] = df["oldbalanceDest"] + df["amount"] - df["newbalanceDest"]
df["amount_ratio"] = df["amount"] / (df["oldbalanceOrg"] + 1)

# One-hot encode transaction type
for t in ["CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER"]:
    df[f"type_{t}"] = (df["type"] == t).astype(float)

X = df[FEATURE_COLS]
y = df["isFraud"]

print(f"✓ Feature matrix: {X.shape}")
print(f"  Positive class: {y.sum():,} ({y.mean()*100:.4f}%)")
print(f"\nCorrelation với isFraud (top 5):")
corr = df[FEATURE_COLS + ["isFraud"]].corr()["isFraud"].drop("isFraud").abs().sort_values(ascending=False)
print(corr.head())

# %% [markdown]
# ## 4. Train/Test Split + SMOTE
# - Stratified split 80/20 giữ tỷ lệ fraud
# - StandardScaler chuẩn hóa features
# - **SMOTE** oversample lớp thiểu số (fraud) lên 10% để model học tốt hơn

# %%
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y,
)
print(f"Train: {X_train.shape[0]:,} samples")
print(f"Test:  {X_test.shape[0]:,} samples")
print(f"Train fraud rate: {y_train.mean()*100:.4f}%")

# Scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# SMOTE trên train set — tăng fraud lên ~10%
smote = SMOTE(random_state=42, sampling_strategy=0.1)
X_resampled, y_resampled = smote.fit_resample(X_train_scaled, y_train)
print(f"\nSau SMOTE:")
print(f"  Samples: {X_resampled.shape[0]:,}")
print(f"  Fraud ratio: {y_resampled.mean()*100:.2f}%")

# %% [markdown]
# ## 5. Huấn luyện mô hình
# | Model | Ưu điểm |
# |---|---|
# | Logistic Regression | Baseline nhanh, interpretable |
# | Random Forest | Robust với outliers, parallel training |
# | Gradient Boosting | Sequential ensemble, thường cho F1 cao nhất |

# %%
models = {
    "LogisticRegression": LogisticRegression(
        max_iter=1000, random_state=42, class_weight="balanced",
    ),
    "RandomForest": RandomForestClassifier(
        n_estimators=100, max_depth=15, random_state=42,
        class_weight="balanced", n_jobs=-1,
    ),
    "GradientBoosting": GradientBoostingClassifier(
        n_estimators=100, max_depth=5, learning_rate=0.1,
        random_state=42, subsample=0.8,
    ),
}

results = {}
for name, model in models.items():
    print(f"\n{'='*60}")
    print(f"Training {name} ...")
    model.fit(X_resampled, y_resampled)

    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    metrics = {
        "f1": f1_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred),
        "recall": recall_score(y_test, y_pred),
        "roc_auc": roc_auc_score(y_test, y_prob),
    }
    results[name] = {"model": model, "y_pred": y_pred, "y_prob": y_prob, **metrics}

    print(f"  F1:        {metrics['f1']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")

# %% [markdown]
# ## 6. Đánh giá chi tiết
# ### 6.1 Confusion Matrix

# %%
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
for idx, (name, res) in enumerate(results.items()):
    ax = axes[idx]
    cm = confusion_matrix(y_test, res["y_pred"])
    sns.heatmap(
        cm, annot=True, fmt=",d", cmap="Blues", ax=ax,
        xticklabels=["Non-Fraud", "Fraud"],
        yticklabels=["Non-Fraud", "Fraud"],
    )
    ax.set_title(f"{name}\nF1={res['f1']:.4f}")
    ax.set_ylabel("Actual")
    ax.set_xlabel("Predicted")

plt.tight_layout()
plt.savefig(
    os.path.join(os.path.dirname(__file__), "..", "docs", "confusion_matrices.png"),
    dpi=150, bbox_inches="tight",
)
plt.show()
print("✓ Confusion matrices đã lưu → docs/confusion_matrices.png")

# %%
# Classification Report chi tiết
for name, res in results.items():
    print(f"\n{'='*60}")
    print(f"CLASSIFICATION REPORT — {name}")
    print("=" * 60)
    print(classification_report(y_test, res["y_pred"], target_names=["Non-Fraud", "Fraud"]))

# %% [markdown]
# ### 6.2 ROC Curves

# %%
plt.figure(figsize=(8, 6))
for name, res in results.items():
    fpr, tpr, _ = roc_curve(y_test, res["y_prob"])
    plt.plot(fpr, tpr, linewidth=2, label=f"{name} (AUC = {res['roc_auc']:.4f})")

plt.plot([0, 1], [0, 1], "k--", linewidth=1, label="Random (AUC = 0.5)")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curves — So sánh mô hình phát hiện gian lận")
plt.legend(loc="lower right")
plt.grid(True, alpha=0.3)
plt.savefig(
    os.path.join(os.path.dirname(__file__), "..", "docs", "roc_curves.png"),
    dpi=150, bbox_inches="tight",
)
plt.show()
print("✓ ROC curves đã lưu → docs/roc_curves.png")

# %% [markdown]
# ## 7. So sánh mô hình

# %%
comparison = pd.DataFrame(
    {
        name: {"F1": r["f1"], "Precision": r["precision"],
               "Recall": r["recall"], "ROC-AUC": r["roc_auc"]}
        for name, r in results.items()
    }
).T.round(4)

print("=" * 60)
print("BẢNG SO SÁNH MÔ HÌNH")
print("=" * 60)
print(comparison.to_string())

best_name = comparison["F1"].idxmax()
print(f"\n>>> Mô hình tốt nhất (F1): {best_name}")
print(f"    F1 = {comparison.loc[best_name, 'F1']:.4f}")

# Feature importance (Random Forest)
if "RandomForest" in results:
    importances = results["RandomForest"]["model"].feature_importances_
    feat_imp = pd.Series(importances, index=FEATURE_COLS).sort_values(ascending=False)
    print(f"\n{'='*60}")
    print("FEATURE IMPORTANCE (Random Forest)")
    print("=" * 60)
    for feat, imp in feat_imp.items():
        bar = "█" * int(imp * 80)
        print(f"  {feat:<25s} {imp:.4f}  {bar}")

# %% [markdown]
# ## 8. Lưu mô hình tốt nhất
# Lưu model + scaler + config vào `model/` để Spark streaming pipeline load khi khởi động.
#
# **Output files:**
# - `model/fraud_model.pkl` — scikit-learn model + scaler (joblib)
# - `model/feature_config.json` — feature columns, thresholds, blacklist

# %%
model_dir = os.path.join(os.path.dirname(__file__), "..", "model")
os.makedirs(model_dir, exist_ok=True)

best = results[best_name]

# Model data dict — format expected by streaming/spark_job.py
model_data = {
    "model_name": best_name,
    "model": best["model"],
    "scaler": scaler,
    "metrics": {
        "f1": best["f1"],
        "precision": best["precision"],
        "recall": best["recall"],
        "roc_auc": best["roc_auc"],
    },
}
model_path = os.path.join(model_dir, "fraud_model.pkl")
joblib.dump(model_data, model_path)

# Blacklist: tài khoản đích xuất hiện ≥3 lần trong giao dịch gian lận
fraud_dests = df[df["isFraud"] == 1]["nameDest"].value_counts()
blacklist = fraud_dests[fraud_dests >= 3].index.tolist()

feature_config = {
    "feature_columns": FEATURE_COLS,
    "thresholds": {"fraud_probability": 0.5},
    "blacklist_accounts": blacklist[:100],
}
config_path = os.path.join(model_dir, "feature_config.json")
with open(config_path, "w") as f:
    json.dump(feature_config, f, indent=2)

print("=" * 60)
print("MODEL SAVED SUCCESSFULLY")
print("=" * 60)
print(f"  Model:     {model_path}")
print(f"  Config:    {config_path}")
print(f"  Blacklist: {len(blacklist[:100])} accounts")
print(f"\n  Best model: {best_name}")
for k, v in model_data["metrics"].items():
    print(f"    {k}: {v:.4f}")

# %% [markdown]
# ## Kết luận
#
# | Thành phần | Chi tiết |
# |---|---|
# | Mô hình | Lưu tại `model/fraud_model.pkl` |
# | Cấu hình | `model/feature_config.json` (features + thresholds + blacklist) |
# | Risk score | `0.4 × rule_score + 0.6 × model_probability` |
# | Streaming | `spark_job.py` tự động load model khi khởi động |
#
# **Lưu ý:** Chạy notebook này TRƯỚC khi `docker compose up` để tạo model files.
# Nếu không có model, streaming pipeline sẽ chạy ở chế độ rule-only (chỉ dùng luật).
