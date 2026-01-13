# Database Schema

> SQLite database schema for PhotoBooth application

---

## Overview

- **Database Engine:** SQLite 3
- **File Location:** `/data/photobooth.db`
- **Character Set:** UTF-8
- **Journal Mode:** WAL (Write-Ahead Logging)

---

## Schema Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    sessions     │       │     photos      │       │   print_jobs    │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │       │ id (PK)         │
│ language        │  │    │ session_id (FK) │───────│ session_id (FK) │
│ status          │  └───>│ index           │       │ status          │
│ created_at      │       │ file_path       │       │ copies          │
│ completed_at    │       │ thumbnail_path  │       │ cups_job_id     │
│ composite_path  │       │ captured_at     │       │ created_at      │
└─────────────────┘       │ file_size       │       │ started_at      │
                          └─────────────────┘       │ completed_at    │
                                                    │ error_code      │
┌─────────────────┐       ┌─────────────────┐       │ error_message   │
│    settings     │       │   job_events    │       │ retry_count     │
├─────────────────┤       ├─────────────────┤       └─────────────────┘
│ key (PK)        │       │ id (PK)         │              │
│ value           │       │ job_id (FK)     │──────────────┘
│ updated_at      │       │ event_type      │
└─────────────────┘       │ message         │
                          │ created_at      │
                          └─────────────────┘
```

---

## Tables

### sessions

Stores photo session information.

```sql
CREATE TABLE sessions (
    id              TEXT PRIMARY KEY,
    language        TEXT NOT NULL DEFAULT 'ko',
    status          TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at    TEXT,
    abandoned_at    TEXT,
    composite_path  TEXT,

    -- Constraints
    CHECK (language IN ('ko', 'en')),
    CHECK (status IN ('ACTIVE', 'COMPLETE', 'PRINTED', 'ABANDONED'))
);

-- Indexes
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | TEXT | NO | UUID primary key |
| language | TEXT | NO | Session language: 'ko' or 'en' |
| status | TEXT | NO | Session state |
| created_at | TEXT | NO | ISO 8601 timestamp |
| completed_at | TEXT | YES | When all 4 photos captured |
| abandoned_at | TEXT | YES | When session abandoned |
| composite_path | TEXT | YES | Path to composite image |

**Status Values:**
- `ACTIVE` - Session in progress
- `COMPLETE` - 4 photos captured, ready for print
- `PRINTED` - Successfully printed
- `ABANDONED` - User abandoned session

---

### photos

Stores individual photo information.

```sql
CREATE TABLE photos (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    index           INTEGER NOT NULL,
    file_path       TEXT NOT NULL,
    thumbnail_path  TEXT NOT NULL,
    captured_at     TEXT NOT NULL DEFAULT (datetime('now')),
    file_size       INTEGER NOT NULL,
    width           INTEGER NOT NULL,
    height          INTEGER NOT NULL,

    -- Constraints
    CHECK (index >= 0 AND index <= 3),
    UNIQUE (session_id, index),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_photos_session_id ON photos(session_id);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | TEXT | NO | UUID primary key |
| session_id | TEXT | NO | FK to sessions |
| index | INTEGER | NO | Photo position (0-3) |
| file_path | TEXT | NO | Path to full image |
| thumbnail_path | TEXT | NO | Path to thumbnail |
| captured_at | TEXT | NO | ISO 8601 timestamp |
| file_size | INTEGER | NO | File size in bytes |
| width | INTEGER | NO | Image width in pixels |
| height | INTEGER | NO | Image height in pixels |

---

### print_jobs

Stores print job information.

```sql
CREATE TABLE print_jobs (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'PENDING',
    copies          INTEGER NOT NULL DEFAULT 1,
    cups_job_id     INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    started_at      TEXT,
    completed_at    TEXT,
    cancelled_at    TEXT,
    error_code      TEXT,
    error_message   TEXT,
    retry_count     INTEGER NOT NULL DEFAULT 0,
    next_retry_at   TEXT,

    -- Constraints
    CHECK (copies >= 1 AND copies <= 3),
    CHECK (status IN ('PENDING', 'PROCESSING', 'PRINTING', 'COMPLETED',
                      'FAILED', 'CANCELLED', 'RETRY_PENDING')),
    CHECK (retry_count >= 0 AND retry_count <= 3),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_print_jobs_session_id ON print_jobs(session_id);
CREATE INDEX idx_print_jobs_status ON print_jobs(status);
CREATE INDEX idx_print_jobs_created_at ON print_jobs(created_at);
CREATE INDEX idx_print_jobs_cups_job_id ON print_jobs(cups_job_id);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | TEXT | NO | UUID primary key |
| session_id | TEXT | NO | FK to sessions |
| status | TEXT | NO | Job state |
| copies | INTEGER | NO | Number of copies (1-3) |
| cups_job_id | INTEGER | YES | CUPS job ID when submitted |
| created_at | TEXT | NO | When job created |
| started_at | TEXT | YES | When printing started |
| completed_at | TEXT | YES | When printing finished |
| cancelled_at | TEXT | YES | When cancelled |
| error_code | TEXT | YES | Error code if failed |
| error_message | TEXT | YES | Error description |
| retry_count | INTEGER | NO | Number of retry attempts |
| next_retry_at | TEXT | YES | Scheduled retry time |

**Status Values:**
- `PENDING` - Waiting in queue
- `PROCESSING` - Preparing to print
- `PRINTING` - Currently printing
- `COMPLETED` - Successfully printed
- `FAILED` - Print failed
- `CANCELLED` - Cancelled by user
- `RETRY_PENDING` - Waiting for retry

---

### job_events

Stores job timeline events for debugging/history.

```sql
CREATE TABLE job_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    message     TEXT NOT NULL,
    details     TEXT,  -- JSON
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),

    FOREIGN KEY (job_id) REFERENCES print_jobs(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_job_events_job_id ON job_events(job_id);
CREATE INDEX idx_job_events_created_at ON job_events(created_at);
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | INTEGER | NO | Auto-increment PK |
| job_id | TEXT | NO | FK to print_jobs |
| event_type | TEXT | NO | Event type identifier |
| message | TEXT | NO | Human-readable message |
| details | TEXT | YES | JSON extra data |
| created_at | TEXT | NO | Event timestamp |

**Event Types:**
- `CREATED` - Job created
- `SUBMITTED` - Submitted to CUPS
- `STARTED` - Printing started
- `PROGRESS` - Progress update
- `COMPLETED` - Successfully completed
- `FAILED` - Print failed
- `RETRY_SCHEDULED` - Retry scheduled
- `RETRY_STARTED` - Retry attempt started
- `CANCELLED` - Job cancelled

---

### settings

Stores application settings as key-value pairs.

```sql
CREATE TABLE settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,  -- JSON
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Seed default settings
INSERT INTO settings (key, value) VALUES
    ('display.default_language', '"ko"'),
    ('display.countdown_options', '[3, 5, 8, 10]'),
    ('display.default_countdown', '5'),
    ('display.sound_enabled', 'true'),
    ('print.max_copies', '3'),
    ('print.paper_size', '"4x6"'),
    ('print.quality', '"high"'),
    ('print.logo_enabled', 'true'),
    ('print.date_enabled', 'true'),
    ('print.date_format', '"YYYY.MM.DD"'),
    ('system.timezone', '"Africa/Kigali"'),
    ('system.admin_pin_hash', '"$2b$12$..."'),
    ('system.auto_cleanup_days', '30'),
    ('system.log_level', '"error"'),
    ('network.ssid', '"photobooth"'),
    ('network.password_hash', '"$2b$12$..."'),
    ('network.channel', '6');
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| key | TEXT | NO | Setting key (dot notation) |
| value | TEXT | NO | JSON-encoded value |
| updated_at | TEXT | NO | Last update timestamp |

---

### admin_sessions

Stores admin authentication sessions.

```sql
CREATE TABLE admin_sessions (
    token       TEXT PRIMARY KEY,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    expires_at  TEXT NOT NULL,
    revoked     INTEGER NOT NULL DEFAULT 0
);

-- Indexes
CREATE INDEX idx_admin_sessions_expires_at ON admin_sessions(expires_at);

-- Cleanup old sessions periodically
-- DELETE FROM admin_sessions WHERE expires_at < datetime('now');
```

**Columns:**

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| token | TEXT | NO | JWT token (hashed) |
| created_at | TEXT | NO | When token issued |
| expires_at | TEXT | NO | Token expiration |
| revoked | INTEGER | NO | 1 if manually revoked |

---

### login_attempts

Stores failed login attempts for rate limiting.

```sql
CREATE TABLE login_attempts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address  TEXT NOT NULL,
    attempted_at TEXT NOT NULL DEFAULT (datetime('now')),
    success     INTEGER NOT NULL DEFAULT 0
);

-- Indexes
CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address);
CREATE INDEX idx_login_attempts_time ON login_attempts(attempted_at);

-- Cleanup old attempts periodically
-- DELETE FROM login_attempts WHERE attempted_at < datetime('now', '-1 hour');
```

---

### system_logs

Stores application logs (optional, can use file-based logging).

```sql
CREATE TABLE system_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    level       TEXT NOT NULL,
    source      TEXT NOT NULL,
    message     TEXT NOT NULL,
    details     TEXT,  -- JSON
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX idx_system_logs_level ON system_logs(level);
CREATE INDEX idx_system_logs_source ON system_logs(source);
CREATE INDEX idx_system_logs_created_at ON system_logs(created_at);

-- Keep only last 7 days
-- DELETE FROM system_logs WHERE created_at < datetime('now', '-7 days');
```

---

## Migrations

### Migration Table

```sql
CREATE TABLE schema_migrations (
    version     INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

### Migration Files

```
migrations/
├── 001_initial_schema.sql
├── 002_add_job_events.sql
├── 003_add_system_logs.sql
└── ...
```

### Example Migration

```sql
-- migrations/001_initial_schema.sql
-- Migration: Initial schema
-- Version: 1

BEGIN TRANSACTION;

CREATE TABLE sessions (...);
CREATE TABLE photos (...);
CREATE TABLE print_jobs (...);
CREATE TABLE settings (...);

INSERT INTO schema_migrations (version, name)
VALUES (1, 'initial_schema');

COMMIT;
```

---

## Common Queries

### Get Session with Photos

```sql
SELECT
    s.*,
    json_group_array(
        json_object(
            'id', p.id,
            'index', p.index,
            'thumbnail_path', p.thumbnail_path,
            'captured_at', p.captured_at
        )
    ) as photos
FROM sessions s
LEFT JOIN photos p ON s.id = p.session_id
WHERE s.id = ?
GROUP BY s.id;
```

### Get Active Print Jobs

```sql
SELECT * FROM print_jobs
WHERE status IN ('PENDING', 'PROCESSING', 'PRINTING', 'RETRY_PENDING')
ORDER BY created_at ASC;
```

### Get Today's Statistics

```sql
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
    SUM(CASE WHEN status = 'CANCELLED' THEN 1 ELSE 0 END) as cancelled
FROM print_jobs
WHERE date(created_at) = date('now');
```

### Get Storage Usage

```sql
SELECT
    COUNT(*) as session_count,
    SUM(
        (SELECT COALESCE(SUM(file_size), 0) FROM photos WHERE session_id = s.id)
    ) as total_photo_bytes
FROM sessions s;
```

### Cleanup Old Sessions

```sql
DELETE FROM sessions
WHERE status = 'ABANDONED'
AND created_at < datetime('now', '-30 days');
```

### Get Jobs for Retry

```sql
SELECT * FROM print_jobs
WHERE status = 'RETRY_PENDING'
AND next_retry_at <= datetime('now')
ORDER BY next_retry_at ASC;
```

---

## Indexes Summary

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| sessions | idx_sessions_status | status | Filter by status |
| sessions | idx_sessions_created_at | created_at | Date queries |
| photos | idx_photos_session_id | session_id | Join optimization |
| print_jobs | idx_print_jobs_session_id | session_id | Join optimization |
| print_jobs | idx_print_jobs_status | status | Filter active jobs |
| print_jobs | idx_print_jobs_created_at | created_at | Date queries |
| print_jobs | idx_print_jobs_cups_job_id | cups_job_id | CUPS lookup |
| job_events | idx_job_events_job_id | job_id | Timeline queries |
| job_events | idx_job_events_created_at | created_at | Date queries |

---

## Backup Strategy

```bash
# Daily backup
sqlite3 /data/photobooth.db ".backup /data/backups/photobooth-$(date +%Y%m%d).db"

# Keep last 7 backups
find /data/backups -name "photobooth-*.db" -mtime +7 -delete
```

---

## Performance Notes

1. **WAL Mode**: Enables concurrent reads during writes
   ```sql
   PRAGMA journal_mode = WAL;
   ```

2. **Foreign Keys**: Must be enabled per connection
   ```sql
   PRAGMA foreign_keys = ON;
   ```

3. **Connection Pool**: Use single connection or small pool (SQLite limitation)

4. **Vacuum**: Run periodically to reclaim space
   ```sql
   VACUUM;
   ```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
