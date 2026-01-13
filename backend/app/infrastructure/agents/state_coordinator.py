"""
State Coordinator for Multi-Agent PhotoBooth System

Provides thread-safe and process-safe state management for coordinating
multiple Claude agents operating on the Raspberry Pi 5.

Features:
- Atomic read/write operations with file locking
- SQLite-based persistent state
- JSON state files for quick agent access
- State versioning for conflict detection
"""

import fcntl
import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class StateCoordinator:
    """
    Coordinates agent access to shared state with locking and persistence.

    Supports two storage backends:
    - JSON files: Fast access for frequent reads
    - SQLite: Durable storage for critical state
    """

    def __init__(
        self,
        state_dir: str = ".claude/state",
        db_path: str = "data/agent_state.db"
    ):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._local_lock = threading.RLock()
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for persistent state."""
        with self._get_db_connection() as conn:
            conn.executescript("""
                -- Agent session tracking
                CREATE TABLE IF NOT EXISTS agent_sessions (
                    session_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    started_at TEXT NOT NULL,
                    last_active_at TEXT NOT NULL,
                    context_compacted INTEGER DEFAULT 0,
                    state_json TEXT DEFAULT '{}'
                );

                -- Background task tracking
                CREATE TABLE IF NOT EXISTS background_tasks (
                    task_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    command TEXT NOT NULL,
                    status TEXT DEFAULT 'running',
                    pid INTEGER,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    output_file TEXT,
                    error_message TEXT
                );

                -- State change history (for debugging)
                CREATE TABLE IF NOT EXISTS state_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state_key TEXT NOT NULL,
                    old_version INTEGER,
                    new_version INTEGER,
                    changed_by TEXT,
                    changed_at TEXT NOT NULL,
                    changes_json TEXT
                );

                -- Indexes for performance
                CREATE INDEX IF NOT EXISTS idx_agent_sessions_status
                    ON agent_sessions(status);
                CREATE INDEX IF NOT EXISTS idx_background_tasks_status
                    ON background_tasks(status);
                CREATE INDEX IF NOT EXISTS idx_state_history_key
                    ON state_history(state_key);
            """)
            conn.commit()

    @contextmanager
    def _get_db_connection(self):
        """Get SQLite connection with proper cleanup."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def _file_lock(self, lock_path: Path, exclusive: bool = True):
        """Acquire file-based lock for cross-process coordination."""
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        with open(lock_path, 'w') as lock_file:
            lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
            try:
                fcntl.flock(lock_file.fileno(), lock_type)
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    # ==================== JSON State Operations ====================

    def read_state(self, key: str = "current") -> Dict[str, Any]:
        """
        Read state from JSON file with shared lock.

        Args:
            key: State file key (e.g., "current", "print-queue")

        Returns:
            State dictionary or empty dict if not found
        """
        state_file = self.state_dir / f"{key}.json"
        lock_file = self.state_dir / f"{key}.lock"

        with self._local_lock:
            with self._file_lock(lock_file, exclusive=False):
                try:
                    if state_file.exists():
                        return json.loads(state_file.read_text())
                    return {}
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse state file {key}: {e}")
                    return {}

    def write_state(
        self,
        state: Dict[str, Any],
        key: str = "current",
        updated_by: str = "system"
    ) -> bool:
        """
        Write state to JSON file with exclusive lock.

        Args:
            state: State dictionary to write
            key: State file key
            updated_by: Agent/system that made the update

        Returns:
            True if successful
        """
        state_file = self.state_dir / f"{key}.json"
        lock_file = self.state_dir / f"{key}.lock"

        # Update metadata
        if "meta" not in state:
            state["meta"] = {}

        old_version = state["meta"].get("version", 0)
        state["meta"]["version"] = old_version + 1
        state["meta"]["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
        state["meta"]["updatedBy"] = updated_by

        with self._local_lock:
            with self._file_lock(lock_file, exclusive=True):
                try:
                    # Write to temp file first, then rename (atomic)
                    temp_file = state_file.with_suffix('.tmp')
                    temp_file.write_text(json.dumps(state, indent=2))
                    temp_file.rename(state_file)

                    logger.debug(f"State {key} updated to version {state['meta']['version']}")
                    return True

                except Exception as e:
                    logger.error(f"Failed to write state {key}: {e}")
                    return False

    def update_state(
        self,
        updates: Dict[str, Any],
        key: str = "current",
        updated_by: str = "system"
    ) -> Dict[str, Any]:
        """
        Atomic read-modify-write operation on state.

        Args:
            updates: Dictionary of updates to merge
            key: State file key
            updated_by: Agent making the update

        Returns:
            Updated state dictionary
        """
        state_file = self.state_dir / f"{key}.json"
        lock_file = self.state_dir / f"{key}.lock"

        with self._local_lock:
            with self._file_lock(lock_file, exclusive=True):
                # Read current state
                if state_file.exists():
                    state = json.loads(state_file.read_text())
                else:
                    state = {}

                # Deep merge updates
                self._deep_merge(state, updates)

                # Update metadata
                if "meta" not in state:
                    state["meta"] = {"version": 0}

                state["meta"]["version"] = state["meta"].get("version", 0) + 1
                state["meta"]["lastUpdated"] = datetime.utcnow().isoformat() + "Z"
                state["meta"]["updatedBy"] = updated_by

                # Write atomically
                temp_file = state_file.with_suffix('.tmp')
                temp_file.write_text(json.dumps(state, indent=2))
                temp_file.rename(state_file)

                return state

    def _deep_merge(self, base: Dict, updates: Dict) -> None:
        """Recursively merge updates into base dictionary."""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    # ==================== Agent Session Operations ====================

    def register_agent_session(
        self,
        session_id: str,
        agent_name: str,
        initial_state: Optional[Dict] = None
    ) -> bool:
        """Register a new agent session."""
        now = datetime.utcnow().isoformat()

        with self._get_db_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO agent_sessions
                    (session_id, agent_name, started_at, last_active_at, state_json)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session_id,
                    agent_name,
                    now,
                    now,
                    json.dumps(initial_state or {})
                ))
                conn.commit()

                logger.info(f"Registered agent session: {agent_name} ({session_id})")
                return True

            except sqlite3.IntegrityError:
                logger.warning(f"Agent session already exists: {session_id}")
                return False

    def update_agent_session(
        self,
        session_id: str,
        state: Optional[Dict] = None,
        status: Optional[str] = None
    ) -> bool:
        """Update agent session state and/or status."""
        now = datetime.utcnow().isoformat()

        with self._get_db_connection() as conn:
            updates = ["last_active_at = ?"]
            params = [now]

            if state is not None:
                updates.append("state_json = ?")
                params.append(json.dumps(state))

            if status is not None:
                updates.append("status = ?")
                params.append(status)

            params.append(session_id)

            result = conn.execute(f"""
                UPDATE agent_sessions
                SET {', '.join(updates)}
                WHERE session_id = ?
            """, params)
            conn.commit()

            return result.rowcount > 0

    def get_agent_session(self, session_id: str) -> Optional[Dict]:
        """Retrieve agent session data."""
        with self._get_db_connection() as conn:
            row = conn.execute(
                "SELECT * FROM agent_sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()

            if row:
                return {
                    "session_id": row["session_id"],
                    "agent_name": row["agent_name"],
                    "status": row["status"],
                    "started_at": row["started_at"],
                    "last_active_at": row["last_active_at"],
                    "state": json.loads(row["state_json"])
                }
            return None

    def list_active_agents(self) -> List[Dict]:
        """List all active agent sessions."""
        with self._get_db_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM agent_sessions WHERE status = 'active'"
            ).fetchall()

            return [
                {
                    "session_id": row["session_id"],
                    "agent_name": row["agent_name"],
                    "started_at": row["started_at"],
                    "last_active_at": row["last_active_at"]
                }
                for row in rows
            ]

    # ==================== Background Task Operations ====================

    def register_background_task(
        self,
        task_id: str,
        agent_name: str,
        command: str,
        pid: Optional[int] = None
    ) -> bool:
        """Register a background task."""
        now = datetime.utcnow().isoformat()

        with self._get_db_connection() as conn:
            try:
                conn.execute("""
                    INSERT INTO background_tasks
                    (task_id, agent_name, command, pid, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (task_id, agent_name, command, pid, now))
                conn.commit()

                # Also update JSON state
                self._update_background_tasks_state()

                return True
            except sqlite3.IntegrityError:
                return False

    def complete_background_task(
        self,
        task_id: str,
        status: str = "completed",
        output_file: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Mark a background task as completed."""
        now = datetime.utcnow().isoformat()

        with self._get_db_connection() as conn:
            result = conn.execute("""
                UPDATE background_tasks
                SET status = ?, completed_at = ?, output_file = ?, error_message = ?
                WHERE task_id = ?
            """, (status, now, output_file, error_message, task_id))
            conn.commit()

            # Update JSON state
            self._update_background_tasks_state()

            return result.rowcount > 0

    def list_background_tasks(self, status: Optional[str] = None) -> List[Dict]:
        """List background tasks, optionally filtered by status."""
        with self._get_db_connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM background_tasks WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM background_tasks ORDER BY created_at DESC LIMIT 50"
                ).fetchall()

            return [dict(row) for row in rows]

    def _update_background_tasks_state(self):
        """Sync background tasks to JSON state file."""
        running = self.list_background_tasks(status="running")
        completed = self.list_background_tasks(status="completed")[:10]  # Last 10

        self.update_state({
            "backgroundTasks": {
                "running": running,
                "completed": completed
            }
        }, updated_by="state_coordinator")

    # ==================== Convenience Methods ====================

    def get_orchestrator_state(self) -> Dict:
        """Get orchestrator agent state."""
        state = self.read_state()
        return state.get("orchestrator", {})

    def get_print_queue_state(self) -> Dict:
        """Get print queue state."""
        state = self.read_state()
        return state.get("printQueue", {})

    def get_system_health_state(self) -> Dict:
        """Get system health state."""
        state = self.read_state()
        return state.get("systemHealth", {})

    def update_circuit_breaker(
        self,
        state: str,
        failure_count: int = 0,
        next_retry_at: Optional[str] = None
    ):
        """Update circuit breaker state for print queue."""
        self.update_state({
            "printQueue": {
                "circuitBreaker": {
                    "state": state,
                    "failureCount": failure_count,
                    "lastFailureAt": datetime.utcnow().isoformat() + "Z" if failure_count > 0 else None,
                    "nextRetryAt": next_retry_at
                }
            }
        }, updated_by="circuit_breaker")
