CREATE TABLE IF NOT EXISTS inference_history (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    transaction_amount DOUBLE PRECISION NOT NULL CHECK (transaction_amount > 0),
    transactions_24h INTEGER NOT NULL CHECK (transactions_24h >= 0),
    new_device BOOLEAN NOT NULL,
    risk_probability DOUBLE PRECISION NOT NULL CHECK (risk_probability BETWEEN 0 AND 1),
    risk_label TEXT NOT NULL CHECK (risk_label IN ('tinggi', 'rendah')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_inference_user_created ON inference_history(username, created_at DESC);
