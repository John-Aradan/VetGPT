CREATE TABLE IF NOT EXISTS failed_logs(
    log_message TEXT NOT NULL UNIQUE,
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    no_attempts INT DEFAULT 0,
    Stage TEXT DEFAULT 'Pending',
    CHECK (Stage IN ('Pending', 'Failed', 'Success'))
)