import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", palette="husl")
plt.rcParams.update({"figure.figsize": (12, 6), "font.size": 12})


def analyze_paysim() -> None:
    """Full EDA on PaySim dataset (primary dataset for training)."""
    print("=" * 60)
    print("PAYSIM DATASET ANALYSIS")
    print("=" * 60)

    df = pd.read_csv(DATA_DIR / "paysim.csv")
    print(f"\nShape: {df.shape}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nData types:\n{df.dtypes}")
    print(f"\nMissing values:\n{df.isnull().sum()}")
    print(f"\nBasic statistics:\n{df.describe()}")

    fraud_count = df['isFraud'].value_counts()
    fraud_rate = df['isFraud'].mean() * 100
    print(f"\nFraud distribution:\n{fraud_count}")
    print(f"Fraud rate: {fraud_rate:.4f}%")

    # 1. Class imbalance
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fraud_count.plot(kind='bar', ax=axes[0], color=['#2ecc71', '#e74c3c'])
    axes[0].set_title('Transaction Count: Normal vs Fraud')
    axes[0].set_xticklabels(['Normal', 'Fraud'], rotation=0)
    axes[0].set_ylabel('Count')

    axes[1].pie(fraud_count, labels=['Normal', 'Fraud'], autopct='%1.3f%%',
                colors=['#2ecc71', '#e74c3c'], explode=(0, 0.1))
    axes[1].set_title('Fraud Rate Distribution')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "paysim_class_imbalance.png", dpi=150)
    plt.close()

    # 2. Transaction type distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    type_counts = df['type'].value_counts()
    type_counts.plot(kind='bar', ax=axes[0], color=sns.color_palette("husl", len(type_counts)))
    axes[0].set_title('Transaction Type Distribution')
    axes[0].set_ylabel('Count')
    axes[0].tick_params(axis='x', rotation=45)

    fraud_by_type = df.groupby('type')['isFraud'].mean() * 100
    fraud_by_type.plot(kind='bar', ax=axes[1], color=sns.color_palette("husl", len(fraud_by_type)))
    axes[1].set_title('Fraud Rate by Transaction Type (%)')
    axes[1].set_ylabel('Fraud Rate (%)')
    axes[1].tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "paysim_type_distribution.png", dpi=150)
    plt.close()

    # 3. Amount distribution: fraud vs normal
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    normal = df[df['isFraud'] == 0]['amount']
    fraud = df[df['isFraud'] == 1]['amount']

    axes[0].hist(normal.clip(upper=normal.quantile(0.99)), bins=50,
                 alpha=0.7, label='Normal', color='#2ecc71')
    axes[0].hist(fraud.clip(upper=fraud.quantile(0.99)), bins=50,
                 alpha=0.7, label='Fraud', color='#e74c3c')
    axes[0].set_title('Amount Distribution (clipped at 99th percentile)')
    axes[0].set_xlabel('Amount')
    axes[0].legend()

    axes[1].boxplot([normal.clip(upper=normal.quantile(0.95)),
                     fraud.clip(upper=fraud.quantile(0.95))],
                    labels=['Normal', 'Fraud'])
    axes[1].set_title('Amount Box Plot (clipped at 95th percentile)')
    axes[1].set_ylabel('Amount')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "paysim_amount_distribution.png", dpi=150)
    plt.close()

    # 4. Balance change patterns
    df['balance_change_orig'] = df['newbalanceOrig'] - df['oldbalanceOrg']
    df['balance_error_orig'] = df['newbalanceOrig'] + df['amount'] - df['oldbalanceOrg']

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for label, color, val in [('Normal', '#2ecc71', 0), ('Fraud', '#e74c3c', 1)]:
        subset = df[df['isFraud'] == val]['balance_error_orig']
        clipped = subset.clip(lower=subset.quantile(0.01), upper=subset.quantile(0.99))
        axes[0].hist(clipped, bins=50, alpha=0.6, label=label, color=color)
    axes[0].set_title('Balance Error (Orig) Distribution')
    axes[0].set_xlabel('Balance Error')
    axes[0].legend()

    fraud_types = df[df['isFraud'] == 1]['type'].value_counts()
    fraud_types.plot(kind='pie', ax=axes[1], autopct='%1.1f%%',
                     colors=sns.color_palette("husl", len(fraud_types)))
    axes[1].set_title('Fraud Cases by Transaction Type')
    axes[1].set_ylabel('')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "paysim_balance_patterns.png", dpi=150)
    plt.close()

    # 5. Correlation heatmap (numeric features)
    numeric_cols = ['amount', 'oldbalanceOrg', 'newbalanceOrig',
                    'oldbalanceDest', 'newbalanceDest', 'isFraud']
    corr = df[numeric_cols].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap='RdYlBu_r', center=0, fmt='.3f',
                square=True, linewidths=0.5)
    plt.title('Feature Correlation Heatmap (PaySim)')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "paysim_correlation.png", dpi=150)
    plt.close()

    print("\nPaySim EDA charts saved to training/output/")


def analyze_creditcard() -> None:
    """EDA on Credit Card dataset (secondary dataset for comparison)."""
    print("\n" + "=" * 60)
    print("CREDIT CARD DATASET ANALYSIS")
    print("=" * 60)

    df = pd.read_csv(DATA_DIR / "creditcard.csv")
    print(f"\nShape: {df.shape}")
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nMissing values: {df.isnull().sum().sum()}")

    fraud_count = df['Class'].value_counts()
    fraud_rate = df['Class'].mean() * 100
    print(f"\nFraud distribution:\n{fraud_count}")
    print(f"Fraud rate: {fraud_rate:.4f}%")

    # 1. Class imbalance
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fraud_count.plot(kind='bar', ax=axes[0], color=['#3498db', '#e74c3c'])
    axes[0].set_title('Credit Card: Normal vs Fraud')
    axes[0].set_xticklabels(['Normal', 'Fraud'], rotation=0)
    axes[0].set_ylabel('Count')

    axes[1].pie(fraud_count, labels=['Normal', 'Fraud'], autopct='%1.3f%%',
                colors=['#3498db', '#e74c3c'], explode=(0, 0.1))
    axes[1].set_title('Credit Card Fraud Rate')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "creditcard_class_imbalance.png", dpi=150)
    plt.close()

    # 2. Amount distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    normal_amt = df[df['Class'] == 0]['Amount']
    fraud_amt = df[df['Class'] == 1]['Amount']

    axes[0].hist(normal_amt.clip(upper=normal_amt.quantile(0.99)), bins=50,
                 alpha=0.7, label='Normal', color='#3498db')
    axes[0].hist(fraud_amt.clip(upper=fraud_amt.quantile(0.99)), bins=50,
                 alpha=0.7, label='Fraud', color='#e74c3c')
    axes[0].set_title('Credit Card Amount Distribution')
    axes[0].set_xlabel('Amount')
    axes[0].legend()

    axes[1].boxplot([normal_amt.clip(upper=500), fraud_amt.clip(upper=500)],
                    labels=['Normal', 'Fraud'])
    axes[1].set_title('Credit Card Amount Box Plot (clipped)')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "creditcard_amount_distribution.png", dpi=150)
    plt.close()

    # 3. Top PCA components for fraud separation
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    top_features = ['V1', 'V2', 'V3', 'V4', 'V10', 'V14']
    for idx, feat in enumerate(top_features):
        ax = axes[idx // 3][idx % 3]
        ax.hist(df[df['Class'] == 0][feat], bins=50, alpha=0.6,
                label='Normal', color='#3498db', density=True)
        ax.hist(df[df['Class'] == 1][feat], bins=50, alpha=0.6,
                label='Fraud', color='#e74c3c', density=True)
        ax.set_title(f'{feat} Distribution')
        ax.legend()
    plt.suptitle('Top PCA Components: Normal vs Fraud', fontsize=14)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "creditcard_pca_components.png", dpi=150)
    plt.close()

    print("\nCredit Card EDA charts saved to training/output/")


def generate_comparison_summary() -> None:
    """Generate a comparison summary of both datasets."""
    print("\n" + "=" * 60)
    print("DATASET COMPARISON SUMMARY")
    print("=" * 60)

    ps = pd.read_csv(DATA_DIR / "paysim.csv")
    cc = pd.read_csv(DATA_DIR / "creditcard.csv")

    summary = {
        "Dataset": ["PaySim", "Credit Card"],
        "Rows": [len(ps), len(cc)],
        "Features": [len(ps.columns), len(cc.columns)],
        "Fraud Count": [ps['isFraud'].sum(), cc['Class'].sum()],
        "Fraud Rate (%)": [
            round(ps['isFraud'].mean() * 100, 4),
            round(cc['Class'].mean() * 100, 4)
        ],
        "Feature Type": ["Real (interpretable)", "PCA (anonymized)"],
        "Used For": ["Training + Streaming", "EDA comparison only"]
    }
    summary_df = pd.DataFrame(summary)
    print(f"\n{summary_df.to_string(index=False)}")
    summary_df.to_csv(OUTPUT_DIR / "dataset_comparison.csv", index=False)

    print("\n>>> CONCLUSION: Train on PaySim (features match streaming data)")
    print(">>> Credit Card dataset used for EDA analysis only")


if __name__ == "__main__":
    analyze_paysim()
    analyze_creditcard()
    generate_comparison_summary()
    print("\n✅ EDA complete! Check training/output/ for all charts.")
