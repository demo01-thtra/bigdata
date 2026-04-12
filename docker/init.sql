CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY,
    transaction_type VARCHAR(20) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    name_orig VARCHAR(50),
    old_balance_orig DECIMAL(15,2) DEFAULT 0,
    new_balance_orig DECIMAL(15,2) DEFAULT 0,
    name_dest VARCHAR(50),
    old_balance_dest DECIMAL(15,2) DEFAULT 0,
    new_balance_dest DECIMAL(15,2) DEFAULT 0,
    is_fraud BOOLEAN DEFAULT FALSE,
    fraud_probability FLOAT DEFAULT 0.0,
    detection_method VARCHAR(20) DEFAULT 'none',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fraud_alerts (
    id SERIAL PRIMARY KEY,
    transaction_id UUID REFERENCES transactions(id),
    alert_type VARCHAR(50) NOT NULL,
    reason TEXT,
    risk_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_metrics (
    id SERIAL PRIMARY KEY,
    total_transactions BIGINT DEFAULT 0,
    total_frauds BIGINT DEFAULT 0,
    fraud_rate FLOAT DEFAULT 0.0,
    avg_fraud_amount DECIMAL(15,2) DEFAULT 0.0,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transactions_is_fraud ON transactions(is_fraud);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_fraud_alerts_created_at ON fraud_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_fraud_alerts_transaction_id ON fraud_alerts(transaction_id);
