"""
Model Training Pipeline for Fraud Detection.
Trains on PaySim dataset with proper feature engineering.
Saves best model and feature configuration.
"""
import os
import json
import warnings
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    classification_report
)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')

DATA_DIR = Path(__file__).parent.parent / "data"
MODEL_DIR = Path(__file__).parent.parent / "model"
OUTPUT_DIR = Path(__file__).parent / "output"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FEATURE_COLUMNS = [
    'amount', 'oldbalanceOrg', 'newbalanceOrig',
    'oldbalanceDest', 'newbalanceDest',
    'balance_change_orig', 'balance_change_dest',
    'balance_error_orig', 'balance_error_dest',
    'amount_ratio',
    'type_CASH_IN', 'type_CASH_OUT', 'type_DEBIT',
    'type_PAYMENT', 'type_TRANSFER'
]

TRANSACTION_TYPES = ['CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER']


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply feature engineering to PaySim data."""
    result = df.copy()
    result['balance_change_orig'] = result['newbalanceOrig'] - result['oldbalanceOrg']
    result['balance_change_dest'] = result['newbalanceDest'] - result['oldbalanceDest']
    result['balance_error_orig'] = (
        result['newbalanceOrig'] + result['amount'] - result['oldbalanceOrg']
    )
    result['balance_error_dest'] = (
        result['oldbalanceDest'] + result['amount'] - result['newbalanceDest']
    )
    result['amount_ratio'] = result['amount'] / (result['oldbalanceOrg'] + 1)

    for t in TRANSACTION_TYPES:
        result[f'type_{t}'] = (result['type'] == t).astype(int)

    return result


SAMPLE_SIZE = int(os.environ.get('TRAIN_SAMPLE_SIZE', '500000'))


def load_and_prepare_data() -> tuple:
    """Load PaySim data, sample if too large, and prepare features/labels."""
    print("Loading PaySim dataset...")
    df = pd.read_csv(DATA_DIR / "paysim.csv")
    print(f"  Total records: {len(df):,}")
    print(f"  Fraud records: {df['isFraud'].sum():,}")
    print(f"  Fraud rate: {df['isFraud'].mean() * 100:.4f}%")

    if len(df) > SAMPLE_SIZE:
        fraud_df = df[df['isFraud'] == 1]
        normal_df = df[df['isFraud'] == 0].sample(
            n=min(SAMPLE_SIZE, len(df[df['isFraud'] == 0])),
            random_state=42
        )
        df = pd.concat([fraud_df, normal_df], ignore_index=True)
        print(f"  Sampled to: {len(df):,} (all {len(fraud_df):,} frauds + {len(normal_df):,} normal)")

    df = engineer_features(df)
    X = df[FEATURE_COLUMNS].values
    y = df['isFraud'].values

    return X, y


def train_and_evaluate_models(X_train, X_test, y_train, y_test, scaler) -> dict:
    """Train multiple models and return evaluation results."""
    models = {
        'LogisticRegression': LogisticRegression(
            class_weight='balanced', max_iter=1000, random_state=42
        ),
        'RandomForest': RandomForestClassifier(
            n_estimators=100, class_weight='balanced',
            max_depth=15, min_samples_split=10,
            random_state=42, n_jobs=-1
        ),
        'GradientBoosting': GradientBoostingClassifier(
            n_estimators=100, max_depth=8,
            learning_rate=0.1, random_state=42
        ),
    }

    results = {}
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1': f1_score(y_test, y_pred, zero_division=0),
            'roc_auc': roc_auc_score(y_test, y_prob),
            'pr_auc': average_precision_score(y_test, y_prob),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
        }
        results[name] = {'model': model, 'metrics': metrics}

        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1-Score:  {metrics['f1']:.4f}")
        print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
        print(f"  PR-AUC:    {metrics['pr_auc']:.4f}")

    return results


def plot_model_comparison(results: dict) -> None:
    """Plot comparison chart of all models."""
    metric_names = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'pr_auc']
    model_names = list(results.keys())

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    data = []
    for model_name in model_names:
        for metric in metric_names:
            data.append({
                'Model': model_name,
                'Metric': metric.upper(),
                'Value': results[model_name]['metrics'][metric]
            })
    comparison_df = pd.DataFrame(data)

    pivot = comparison_df.pivot(index='Metric', columns='Model', values='Value')
    pivot.plot(kind='bar', ax=axes[0], rot=45)
    axes[0].set_title('Model Comparison')
    axes[0].set_ylabel('Score')
    axes[0].set_ylim(0, 1.05)
    axes[0].legend(loc='lower right')

    best_model_name = max(results, key=lambda k: results[k]['metrics']['f1'])
    cm = np.array(results[best_model_name]['metrics']['confusion_matrix'])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[1],
                xticklabels=['Normal', 'Fraud'], yticklabels=['Normal', 'Fraud'])
    axes[1].set_title(f'Confusion Matrix ({best_model_name})')
    axes[1].set_xlabel('Predicted')
    axes[1].set_ylabel('Actual')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "model_comparison.png", dpi=150)
    plt.close()


def _build_blacklist() -> list:
    """Build blacklist from fraud destination accounts in full dataset."""
    print("Building blacklist from fraud transactions...")
    chunks = pd.read_csv(DATA_DIR / "paysim.csv", usecols=['nameDest', 'isFraud'], chunksize=500000)
    fraud_dest_counts: dict = {}
    for chunk in chunks:
        fraud_chunk = chunk[chunk['isFraud'] == 1]
        for dest in fraud_chunk['nameDest']:
            fraud_dest_counts[dest] = fraud_dest_counts.get(dest, 0) + 1
    top = sorted(fraud_dest_counts.items(), key=lambda x: x[1], reverse=True)[:50]
    blacklist = [acc for acc, _ in top]
    print(f"  Blacklist: {len(blacklist)} accounts (top fraud destinations)")
    return blacklist


def save_best_model(results: dict, scaler: StandardScaler) -> str:
    """Save the best model based on F1-Score."""
    best_name = max(results, key=lambda k: results[k]['metrics']['f1'])
    best_model = results[best_name]['model']
    best_metrics = results[best_name]['metrics']

    print(f"\n{'=' * 60}")
    print(f"BEST MODEL: {best_name} (F1={best_metrics['f1']:.4f})")
    print(f"{'=' * 60}")

    model_path = MODEL_DIR / "fraud_model.pkl"
    joblib.dump({
        'model': best_model,
        'scaler': scaler,
        'model_name': best_name,
        'metrics': best_metrics,
    }, model_path)
    print(f"Model saved to {model_path}")

    blacklist = _build_blacklist()
    config = {
        'feature_columns': FEATURE_COLUMNS,
        'transaction_types': TRANSACTION_TYPES,
        'model_name': best_name,
        'metrics': {k: v for k, v in best_metrics.items() if k != 'confusion_matrix'},
        'blacklist_accounts': blacklist,
        'thresholds': {
            'fraud_probability': 0.5,
            'high_amount': 200000,
            'balance_ratio_alert': 0.8,
        }
    }
    config_path = MODEL_DIR / "feature_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"Config saved to {config_path}")

    return best_name


def main() -> None:
    """Main training pipeline."""
    print("=" * 60)
    print("FRAUD DETECTION MODEL TRAINING PIPELINE")
    print("=" * 60)

    X, y = load_and_prepare_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"\nTrain set: {len(X_train):,} (Fraud: {y_train.sum():,})")
    print(f"Test set:  {len(X_test):,} (Fraud: {y_test.sum():,})")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    results = train_and_evaluate_models(
        X_train_scaled, X_test_scaled, y_train, y_test, scaler
    )
    plot_model_comparison(results)
    save_best_model(results, scaler)

    print("\n[OK] Training complete!")


if __name__ == "__main__":
    main()
