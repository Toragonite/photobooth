"""
Background Task Manager for PhotoBooth

Manages long-running background tasks on Raspberry Pi 5.
Supports parallel agent execution, task tracking, and output collection.

Features:
- Spawn background processes with proper cleanup
- Track task status and output files
- Automatic orphan detection on restart
- Integration with state coordinator
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Callable, Any
import threading

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Background task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class BackgroundTask:
    """Represents a background task."""
    task_id: str
    agent_name: str
    command: str
    status: TaskStatus = TaskStatus.PENDING
    pid: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_file: Optional[str] = None
    error_file: Optional[str] = None
    error_message: Optional[str] = None
    exit_code: Optional[int] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        return data


class BackgroundTaskManager:
    """
    Manages background task execution and tracking.

    Usage:
        manager = BackgroundTaskManager()

        # Spawn a background task
        task = await manager.spawn(
            agent_name="print-manager",
            command="python3 process_queue.py",
            metadata={"job_id": "123"}
        )

        # Check task status
        status = manager.get_task(task.task_id)

        # Get output when complete
        output = manager.get_output(task.task_id)

        # List running tasks
        running = manager.list_tasks(status=TaskStatus.RUNNING)
    """

    def __init__(
        self,
        task_dir: str = ".claude/tasks",
        max_concurrent: int = 10,
        default_timeout: int = 300,
        state_coordinator: Optional[Any] = None
    ):
        self.task_dir = Path(task_dir)
        self.task_dir.mkdir(parents=True, exist_ok=True)

        self.output_dir = self.task_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self.state_coordinator = state_coordinator

        self._tasks: Dict[str, BackgroundTask] = {}
        self._processes: Dict[str, subprocess.Popen] = {}
        self._lock = asyncio.Lock()

        # Load existing tasks from disk
        self._load_tasks()

    def _load_tasks(self):
        """Load task state from disk on startup."""
        for task_file in self.task_dir.glob("*.json"):
            if task_file.name.startswith("_"):
                continue  # Skip internal files
            try:
                data = json.loads(task_file.read_text())
                task = BackgroundTask(
                    task_id=data["task_id"],
                    agent_name=data["agent_name"],
                    command=data["command"],
                    status=TaskStatus(data["status"]),
                    pid=data.get("pid"),
                    created_at=data["created_at"],
                    started_at=data.get("started_at"),
                    completed_at=data.get("completed_at"),
                    output_file=data.get("output_file"),
                    error_file=data.get("error_file"),
                    error_message=data.get("error_message"),
                    exit_code=data.get("exit_code"),
                    metadata=data.get("metadata", {})
                )

                # Check if running task is actually still alive
                if task.status == TaskStatus.RUNNING and task.pid:
                    if not self._process_alive(task.pid):
                        task.status = TaskStatus.FAILED
                        task.error_message = "Process died unexpectedly (orphaned)"
                        task.completed_at = datetime.utcnow().isoformat()
                        self._save_task(task)

                self._tasks[task.task_id] = task

            except Exception as e:
                logger.warning(f"Failed to load task {task_file}: {e}")

    def _save_task(self, task: BackgroundTask):
        """Save task state to disk."""
        task_file = self.task_dir / f"{task.task_id}.json"
        task_file.write_text(json.dumps(task.to_dict(), indent=2))

    async def spawn(
        self,
        agent_name: str,
        command: str,
        timeout: Optional[int] = None,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict] = None,
        on_complete: Optional[Callable[[BackgroundTask], None]] = None
    ) -> BackgroundTask:
        """
        Spawn a new background task.

        Args:
            agent_name: Name of the agent spawning the task
            command: Shell command to execute
            timeout: Timeout in seconds (default: 300)
            cwd: Working directory
            env: Environment variables
            metadata: Additional metadata to store
            on_complete: Callback when task completes

        Returns:
            BackgroundTask object
        """
        async with self._lock:
            # Check concurrent limit
            running_count = sum(
                1 for t in self._tasks.values()
                if t.status == TaskStatus.RUNNING
            )
            if running_count >= self.max_concurrent:
                raise RuntimeError(
                    f"Maximum concurrent tasks ({self.max_concurrent}) reached"
                )

            # Create task
            task_id = str(uuid.uuid4())[:8]
            task = BackgroundTask(
                task_id=task_id,
                agent_name=agent_name,
                command=command,
                status=TaskStatus.PENDING,
                metadata=metadata or {}
            )

            # Set up output files
            task.output_file = str(self.output_dir / f"{task_id}.stdout")
            task.error_file = str(self.output_dir / f"{task_id}.stderr")

            # Prepare environment
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            process_env["PHOTOBOOTH_TASK_ID"] = task_id
            process_env["PHOTOBOOTH_AGENT"] = agent_name

            try:
                # Open output files
                stdout_file = open(task.output_file, 'w')
                stderr_file = open(task.error_file, 'w')

                # Start process
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    cwd=cwd,
                    env=process_env,
                    preexec_fn=os.setsid,  # Create new process group
                    start_new_session=True
                )

                task.pid = process.pid
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.utcnow().isoformat()

                self._tasks[task_id] = task
                self._processes[task_id] = process
                self._save_task(task)

                logger.info(
                    f"Spawned background task {task_id} "
                    f"(agent={agent_name}, pid={process.pid})"
                )

                # Start monitor thread
                monitor = threading.Thread(
                    target=self._monitor_task,
                    args=(task_id, timeout or self.default_timeout, on_complete),
                    daemon=True
                )
                monitor.start()

                # Sync to state coordinator
                self._sync_state()

                return task

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                task.completed_at = datetime.utcnow().isoformat()
                self._save_task(task)
                raise

    def _monitor_task(
        self,
        task_id: str,
        timeout: int,
        on_complete: Optional[Callable]
    ):
        """Monitor task in background thread."""
        task = self._tasks.get(task_id)
        process = self._processes.get(task_id)

        if not task or not process:
            return

        try:
            # Wait for process with timeout
            exit_code = process.wait(timeout=timeout)

            task.exit_code = exit_code
            task.completed_at = datetime.utcnow().isoformat()

            if exit_code == 0:
                task.status = TaskStatus.COMPLETED
                logger.info(f"Task {task_id} completed successfully")
            else:
                task.status = TaskStatus.FAILED
                task.error_message = f"Process exited with code {exit_code}"
                logger.warning(f"Task {task_id} failed with exit code {exit_code}")

        except subprocess.TimeoutExpired:
            # Kill the process
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                process.wait(timeout=5)
            except Exception:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)

            task.status = TaskStatus.TIMEOUT
            task.error_message = f"Task timed out after {timeout}s"
            task.completed_at = datetime.utcnow().isoformat()
            logger.warning(f"Task {task_id} timed out")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow().isoformat()
            logger.error(f"Task {task_id} error: {e}")

        finally:
            # Save task state
            self._save_task(task)

            # Clean up process reference
            if task_id in self._processes:
                del self._processes[task_id]

            # Sync state
            self._sync_state()

            # Call completion callback
            if on_complete:
                try:
                    on_complete(task)
                except Exception as e:
                    logger.error(f"Task completion callback error: {e}")

    def get_task(self, task_id: str) -> Optional[BackgroundTask]:
        """Get task by ID."""
        return self._tasks.get(task_id)

    def get_output(self, task_id: str) -> Optional[str]:
        """Get task stdout output."""
        task = self._tasks.get(task_id)
        if task and task.output_file and Path(task.output_file).exists():
            return Path(task.output_file).read_text()
        return None

    def get_error(self, task_id: str) -> Optional[str]:
        """Get task stderr output."""
        task = self._tasks.get(task_id)
        if task and task.error_file and Path(task.error_file).exists():
            return Path(task.error_file).read_text()
        return None

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        agent_name: Optional[str] = None,
        limit: int = 50
    ) -> List[BackgroundTask]:
        """List tasks with optional filters."""
        tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        if agent_name:
            tasks = [t for t in tasks if t.agent_name == agent_name]

        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return tasks[:limit]

    async def cancel(self, task_id: str) -> bool:
        """Cancel a running task."""
        task = self._tasks.get(task_id)
        process = self._processes.get(task_id)

        if not task or task.status != TaskStatus.RUNNING:
            return False

        try:
            if process:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                await asyncio.sleep(1)

                if process.poll() is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)

            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow().isoformat()
            self._save_task(task)

            if task_id in self._processes:
                del self._processes[task_id]

            self._sync_state()
            logger.info(f"Task {task_id} cancelled")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False

    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks."""
        cutoff = datetime.utcnow()
        cleaned = 0

        for task_id, task in list(self._tasks.items()):
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                if task.completed_at:
                    completed = datetime.fromisoformat(task.completed_at.replace('Z', ''))
                    age_hours = (cutoff - completed).total_seconds() / 3600

                    if age_hours > max_age_hours:
                        # Remove files
                        for path in [task.output_file, task.error_file]:
                            if path and Path(path).exists():
                                Path(path).unlink()

                        task_file = self.task_dir / f"{task_id}.json"
                        if task_file.exists():
                            task_file.unlink()

                        del self._tasks[task_id]
                        cleaned += 1

        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old background tasks")
            self._sync_state()

    def _process_alive(self, pid: int) -> bool:
        """Check if a process is still running."""
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def _sync_state(self):
        """Sync task state to state coordinator."""
        if not self.state_coordinator:
            return

        try:
            running = [t.to_dict() for t in self.list_tasks(status=TaskStatus.RUNNING)]
            completed = [t.to_dict() for t in self.list_tasks(status=TaskStatus.COMPLETED)][:10]

            self.state_coordinator.update_state({
                "backgroundTasks": {
                    "running": running,
                    "completed": completed
                }
            }, updated_by="background_task_manager")
        except Exception as e:
            logger.warning(f"Failed to sync background task state: {e}")

    def get_status(self) -> Dict:
        """Get manager status summary."""
        return {
            "total_tasks": len(self._tasks),
            "running": sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING),
            "completed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED),
            "max_concurrent": self.max_concurrent,
            "default_timeout": self.default_timeout
        }
