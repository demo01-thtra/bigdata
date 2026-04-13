"""Unit tests for feature engineering functions."""
import sys
import os

# Adjust path so we can import from streaming/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'streaming'))


def test_feature_columns_count():
    """Feature vector must have 15 columns matching training pipeline."""
    from spark_job import FEATURE_COLS
    assert len(FEATURE_COLS) == 15, f"Expected 15 features, got {len(FEATURE_COLS)}"


def test_feature_columns_names():
    """Feature names must match what the model was trained on."""
    from spark_job import FEATURE_COLS
    expected = [
        'amount', 'oldbalanceOrg', 'newbalanceOrig',
        'oldbalanceDest', 'newbalanceDest',
        'balance_change_orig', 'balance_change_dest',
        'balance_error_orig', 'balance_error_dest',
        'amount_ratio',
        'type_CASH_IN', 'type_CASH_OUT', 'type_DEBIT',
        'type_PAYMENT', 'type_TRANSFER',
    ]
    assert FEATURE_COLS == expected


def test_transaction_types():
    """Must handle all PaySim transaction types."""
    from spark_job import TRANSACTION_TYPES
    assert set(TRANSACTION_TYPES) == {'CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER'}


def test_fraud_types_subset():
    """Fraud-relevant types must be subset of all types."""
    from spark_job import TRANSACTION_TYPES, PAYSIM_FRAUD_TYPES
    for ft in PAYSIM_FRAUD_TYPES:
        assert ft in TRANSACTION_TYPES, f"{ft} not in TRANSACTION_TYPES"


def test_thresholds():
    """Thresholds must be sensible."""
    from spark_job import HIGH_AMOUNT_THRESHOLD, BALANCE_RATIO_THRESHOLD
    assert HIGH_AMOUNT_THRESHOLD == 200_000
    assert 0 < BALANCE_RATIO_THRESHOLD < 1
