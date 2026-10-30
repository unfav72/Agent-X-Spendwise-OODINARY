-- Spendwise AI Database Schema (SQLite)

CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    account_type TEXT NOT NULL DEFAULT 'bank_account',
    institution TEXT,
    currency TEXT NOT NULL DEFAULT 'INR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    description TEXT NOT NULL,
    merchant TEXT NOT NULL,
    debit REAL NOT NULL DEFAULT 0.0,
    credit REAL NOT NULL DEFAULT 0.0,
    currency TEXT NOT NULL DEFAULT 'INR',
    category TEXT NOT NULL DEFAULT 'Other',
    reference_id TEXT,
    source_file TEXT,
    source_row INTEGER,
    extraction_confidence REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(account_id) REFERENCES accounts(id)
);

CREATE INDEX IF NOT EXISTS idx_trans_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_trans_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_trans_merchant ON transactions(merchant);
CREATE INDEX IF NOT EXISTS idx_trans_debit ON transactions(debit);
CREATE INDEX IF NOT EXISTS idx_trans_credit ON transactions(credit);

CREATE TABLE IF NOT EXISTS user_category_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_or_merchant TEXT UNIQUE NOT NULL,
    corrected_category TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS anomalies (
    id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    anomaly_type TEXT NOT NULL, -- 'spike', 'duplicate_candidate', 'velocity', 'unusual_recurring'
    severity TEXT NOT NULL DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    reason TEXT NOT NULL,
    historical_baseline REAL DEFAULT 0.0,
    delta_amount REAL DEFAULT 0.0,
    confidence REAL DEFAULT 1.0,
    status TEXT NOT NULL DEFAULT 'flagged', -- 'flagged', 'reviewed', 'dismissed', 'confirmed'
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(transaction_id) REFERENCES transactions(id)
);

CREATE TABLE IF NOT EXISTS recovery_records (
    id TEXT PRIMARY KEY,
    original_transaction_id TEXT NOT NULL,
    potential_amount REAL NOT NULL,
    confirmed_amount REAL NOT NULL DEFAULT 0.0,
    unresolved_amount REAL NOT NULL,
    status TEXT NOT NULL, -- 'potential_recovery', 'under_investigation', 'refund_requested', 'partially_confirmed', 'confirmed_recovery', 'rejected_unresolved'
    merchant TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(original_transaction_id) REFERENCES transactions(id)
);

CREATE TABLE IF NOT EXISTS recovery_links (
    id TEXT PRIMARY KEY,
    recovery_id TEXT NOT NULL,
    credit_transaction_id TEXT NOT NULL,
    linked_amount REAL NOT NULL,
    confidence_score REAL DEFAULT 1.0,
    notes TEXT,
    linked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(recovery_id) REFERENCES recovery_records(id),
    FOREIGN KEY(credit_transaction_id) REFERENCES transactions(id)
);

CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    user_query TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    final_answer TEXT,
    language TEXT DEFAULT 'English',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trace_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    thought TEXT,
    tool TEXT,
    tool_args TEXT,
    observation TEXT,
    decision TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(investigation_id) REFERENCES investigations(id)
);

