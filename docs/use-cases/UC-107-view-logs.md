# UC-107: View Logs

## Summary

Admin views system logs from the dashboard to diagnose issues, monitor activity, and debug problems without SSH access to the Raspberry Pi.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **Admin** | Primary | Operator viewing logs |
| **System** | Secondary | Provides log data |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Admin is authenticated |
| PRE-2 | Log files are accessible |

---

## Trigger

Admin navigates to Logs section on dashboard.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Admin navigates to Logs section                               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Frontend displays log source selector:                        │
│     │ - Application logs                                            │
│     │ - Print job logs                                              │
│     │ - System logs (journalctl)                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Admin selects log source (default: Application)               │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Frontend requests: GET /api/admin/logs?source=app&lines=100   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Backend reads log file, returns last N lines                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Frontend displays logs in scrollable view:                    │
│     │ - Timestamp                                                   │
│     │ - Level (color-coded)                                         │
│     │ - Message                                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Admin scrolls through logs                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Admin uses search/filter to find specific entries             │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Filter by Log Level

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 6a  │ Admin selects level filter: Error only                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6b  │ View updates to show only ERROR level logs                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6c  │ Count badge shows filtered vs total entries                   │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Search Logs

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 8a  │ Admin enters search term: "CUPS"                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8b  │ Frontend filters logs containing "CUPS"                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8c  │ Matching text highlighted in results                          │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Real-Time Log Streaming

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 6a  │ Admin enables "Live" toggle                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6b  │ Frontend polls for new logs every 2 seconds                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6c  │ New entries appear at bottom with animation                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6d  │ Auto-scroll keeps newest entries visible                      │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-4: Download Logs

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 7a  │ Admin taps [Download] button                                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7b  │ System generates log export (last 24 hours or filtered view)  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7c  │ Download as .txt or .log file                                 │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: Log File Not Found

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Selected log source file doesn't exist                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Display message: "No logs available for this source"          │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Suggest other log sources                                     │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Large Log File

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Log file exceeds display limit                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Return only last 1000 lines                                   │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Show notice: "Showing last 1000 entries. Download for full log"│
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Admin can view system logs |
| POST-2 | Admin can filter and search logs |
| POST-3 | Admin can download logs for offline analysis |

---

## Business Rules

| ID | Rule |
|----|------|
| LOG-BR-1 | Default display: last 100 lines |
| LOG-BR-2 | Maximum display: 1000 lines |
| LOG-BR-3 | Live mode poll interval: 2 seconds |
| LOG-BR-4 | Log retention: 7 days |
| LOG-BR-5 | Sensitive data (passwords) never logged |

---

## Log Sources

| Source | Description | Path/Command |
|--------|-------------|--------------|
| Application | Backend application logs | /var/log/photobooth/app.log |
| Print | Print job specific logs | /var/log/photobooth/print.log |
| CUPS | Print service logs | journalctl -u cups |
| System | System-level logs | journalctl -u photobooth-backend |

---

## Log Levels

| Level | Color | Description |
|-------|-------|-------------|
| DEBUG | Gray | Detailed debugging info |
| INFO | Blue | General information |
| WARNING | Orange | Potential issues |
| ERROR | Red | Errors that need attention |
| CRITICAL | Red (bold) | Severe errors |

---

## UI/UX Requirements

### Log Viewer Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back                     Logs                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─── Source ───────────────────────────────────────────────┐   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ │   │
│  │  │    App    │ │   Print   │ │   CUPS    │ │  System   │ │   │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘ │   │
│  │      ↑ selected                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── Filters ──────────────────────────────────────────────┐   │
│  │  Level: [All ▼]   Search: [_______________] [🔍]         │   │
│  │                                                          │   │
│  │  □ Live updates              [⬇️ Download]               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── Log Entries (142 total) ──────────────────────────────┐   │
│  │                                                          │   │
│  │  14:32:15  INFO   Session abc-123 started                │   │
│  │  14:32:20  INFO   Photo 1/4 captured                     │   │
│  │  14:32:25  INFO   Photo 2/4 captured                     │   │
│  │  14:32:30  INFO   Photo 3/4 captured                     │   │
│  │  14:32:35  INFO   Photo 4/4 captured                     │   │
│  │  14:32:36  INFO   Generating composite                   │   │
│  │  14:32:38  INFO   Composite generated: 1.2MB             │   │
│  │  14:32:40  INFO   Print job created: job-456             │   │
│  │  14:32:41  INFO   Submitted to CUPS: cups-789            │   │
│  │  14:32:42  ERROR  CUPS rejected job: printer offline     │   │
│  │  14:32:42  WARN   Scheduling retry 1/3 in 3s             │   │
│  │  14:32:45  INFO   Retry 1: Submitting to CUPS            │   │
│  │  14:32:46  INFO   CUPS accepted job                      │   │
│  │  14:33:30  INFO   Print completed successfully           │   │
│  │                                                          │   │
│  │  (scroll for more...)                                    │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Error Highlight

```
Log Entry (Error):
┌──────────────────────────────────────────────────────────────┐
│  14:32:42  ERROR  CUPS rejected job: printer offline         │
│  ─────────────────────────────────────────────────────────── │
│  │ Red background highlight for ERROR level entries        │ │
└──────────────────────────────────────────────────────────────┘
```

### Live Mode Indicator

```
┌─────────────────────────────────────────────────────────────────┐
│  ✓ Live updates                  ● Recording...                 │
│                                    ↑ Pulsing indicator          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### API Endpoint

```typescript
// GET /api/admin/logs

interface LogsRequest {
  source: 'app' | 'print' | 'cups' | 'system';
  lines?: number;       // Default: 100, max: 1000
  level?: 'debug' | 'info' | 'warning' | 'error';
  search?: string;      // Filter by content
  since?: string;       // ISO timestamp
}

interface LogsResponse {
  entries: LogEntry[];
  total_count: number;
  truncated: boolean;
  oldest_timestamp: string;
  newest_timestamp: string;
}

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  source?: string;
  extra?: Record<string, any>;
}
```

### Backend Implementation

```python
# Log viewing service

import re
from pathlib import Path
from datetime import datetime

class LogViewerService:
    LOG_PATHS = {
        'app': Path('/var/log/photobooth/app.log'),
        'print': Path('/var/log/photobooth/print.log'),
    }

    MAX_LINES = 1000
    LOG_PATTERN = re.compile(
        r'^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) '
        r'(?P<level>\w+) '
        r'(?P<message>.*)$'
    )

    async def get_logs(
        self,
        source: str,
        lines: int = 100,
        level: str | None = None,
        search: str | None = None,
    ) -> LogsResponse:
        if source in ('cups', 'system'):
            return await self._get_journal_logs(source, lines, level, search)

        log_path = self.LOG_PATHS.get(source)
        if not log_path or not log_path.exists():
            return LogsResponse(
                entries=[],
                total_count=0,
                truncated=False,
                oldest_timestamp=None,
                newest_timestamp=None,
            )

        # Read file (tail)
        entries = []
        with open(log_path, 'r') as f:
            # Read last N lines efficiently
            all_lines = f.readlines()
            recent_lines = all_lines[-min(self.MAX_LINES, len(all_lines)):]

        for line in recent_lines:
            entry = self._parse_log_line(line.strip())
            if entry:
                # Apply filters
                if level and entry.level.lower() != level:
                    continue
                if search and search.lower() not in entry.message.lower():
                    continue
                entries.append(entry)

        # Limit output
        truncated = len(entries) > lines
        entries = entries[-lines:]

        return LogsResponse(
            entries=entries,
            total_count=len(entries),
            truncated=truncated,
            oldest_timestamp=entries[0].timestamp if entries else None,
            newest_timestamp=entries[-1].timestamp if entries else None,
        )

    async def _get_journal_logs(
        self,
        source: str,
        lines: int,
        level: str | None,
        search: str | None,
    ) -> LogsResponse:
        """Get logs from systemd journal."""
        import subprocess

        unit = 'cups' if source == 'cups' else 'photobooth-backend'

        cmd = ['journalctl', '-u', unit, '-n', str(min(lines, self.MAX_LINES)),
               '--no-pager', '-o', 'json']

        if level:
            priority_map = {
                'debug': '7',
                'info': '6',
                'warning': '4',
                'error': '3',
            }
            cmd.extend(['-p', priority_map.get(level, '6')])

        result = subprocess.run(cmd, capture_output=True, text=True)

        entries = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                import json
                data = json.loads(line)
                entry = LogEntry(
                    timestamp=datetime.fromtimestamp(
                        int(data.get('__REALTIME_TIMESTAMP', 0)) / 1000000
                    ).isoformat(),
                    level=self._priority_to_level(data.get('PRIORITY', '6')),
                    message=data.get('MESSAGE', ''),
                )
                if search and search.lower() not in entry.message.lower():
                    continue
                entries.append(entry)
            except:
                pass

        return LogsResponse(
            entries=entries,
            total_count=len(entries),
            truncated=len(entries) >= lines,
            oldest_timestamp=entries[0].timestamp if entries else None,
            newest_timestamp=entries[-1].timestamp if entries else None,
        )

    def _parse_log_line(self, line: str) -> LogEntry | None:
        """Parse a log line into structured entry."""
        match = self.LOG_PATTERN.match(line)
        if match:
            return LogEntry(
                timestamp=match.group('timestamp'),
                level=match.group('level'),
                message=match.group('message'),
            )
        return None

    def _priority_to_level(self, priority: str) -> str:
        """Convert syslog priority to log level."""
        mapping = {
            '0': 'CRITICAL', '1': 'CRITICAL', '2': 'CRITICAL',
            '3': 'ERROR', '4': 'WARNING', '5': 'INFO',
            '6': 'INFO', '7': 'DEBUG',
        }
        return mapping.get(priority, 'INFO')
```

### Frontend Component

```typescript
// Log viewer component

const LogViewer: React.FC = () => {
  const [source, setSource] = useState<string>('app');
  const [level, setLevel] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [live, setLive] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);

  const fetchLogs = useCallback(async () => {
    const params = new URLSearchParams({
      source,
      lines: '200',
    });
    if (level !== 'all') params.set('level', level);
    if (search) params.set('search', search);

    const response = await fetch(`/api/admin/logs?${params}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await response.json();
    setLogs(data.entries);
  }, [source, level, search, token]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Live mode polling
  useEffect(() => {
    if (!live) return;
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, [live, fetchLogs]);

  // Auto-scroll in live mode
  useEffect(() => {
    if (live) {
      logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, live]);

  const getLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'info':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="log-viewer">
      {/* Source tabs */}
      <div className="source-tabs">
        {['app', 'print', 'cups', 'system'].map(s => (
          <button
            key={s}
            className={source === s ? 'active' : ''}
            onClick={() => setSource(s)}
          >
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="filters">
        <select value={level} onChange={e => setLevel(e.target.value)}>
          <option value="all">All Levels</option>
          <option value="error">Errors</option>
          <option value="warning">Warnings</option>
          <option value="info">Info</option>
          <option value="debug">Debug</option>
        </select>

        <input
          type="text"
          placeholder="Search..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />

        <label>
          <input
            type="checkbox"
            checked={live}
            onChange={e => setLive(e.target.checked)}
          />
          Live updates
        </label>
      </div>

      {/* Log entries */}
      <div className="log-entries">
        {logs.map((entry, i) => (
          <div key={i} className={`log-entry ${getLevelColor(entry.level)}`}>
            <span className="timestamp">
              {new Date(entry.timestamp).toLocaleTimeString()}
            </span>
            <span className="level">{entry.level}</span>
            <span className="message">{entry.message}</span>
          </div>
        ))}
        <div ref={logEndRef} />
      </div>
    </div>
  );
};
```

---

## Related Use Cases

- **UC-102**: View System Status (quick link to logs)
- **UC-105**: Restart Service (troubleshooting with logs)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
