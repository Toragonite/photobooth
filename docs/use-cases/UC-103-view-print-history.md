# UC-103: View Print History

## Summary

Admin views a list of all print jobs with their status, timestamps, and details. Useful for tracking usage, identifying issues, and verifying print completion.

---

## Actors

| Actor | Type | Description |
|-------|------|-------------|
| **Admin** | Primary | Operator reviewing print history |
| **System** | Secondary | Retrieves and displays job data |

---

## Preconditions

| ID | Condition |
|----|-----------|
| PRE-1 | Admin is authenticated |
| PRE-2 | Admin is on dashboard |
| PRE-3 | Database is accessible |

---

## Trigger

Admin taps "Print History" or "View Details" on dashboard.

---

## Main Flow

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ #   │ Step                                                           │
├─────┼────────────────────────────────────────────────────────────────┤
│ 1   │ Admin navigates to Print History section                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 2   │ Frontend requests: GET /api/admin/print-history               │
│     │ - Default: last 7 days                                        │
│     │ - Paginated (20 per page)                                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 3   │ Backend queries print_jobs table:                             │
│     │ - Join with sessions for composite preview                    │
│     │ - Order by created_at DESC (newest first)                     │
├─────┼────────────────────────────────────────────────────────────────┤
│ 4   │ Return paginated job list with summary stats                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5   │ Frontend displays:                                            │
│     │ - Summary statistics (total, success, failed)                 │
│     │ - Job list with status indicators                             │
│     │ - Timestamp for each job                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 6   │ Admin scrolls/paginates through history                       │
├─────┼────────────────────────────────────────────────────────────────┤
│ 7   │ Admin taps job row to see details                             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8   │ Detail view shows:                                            │
│     │ - Composite image thumbnail                                   │
│     │ - Full job timeline                                           │
│     │ - Error details (if failed)                                   │
│     │ - Retry history                                               │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Alternative Flows

### AF-1: Filter by Status

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 5a  │ Admin taps status filter                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5b  │ Options: All, Completed, Failed, Cancelled                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5c  │ Admin selects "Failed"                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5d  │ List updates to show only failed jobs                         │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-2: Filter by Date Range

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 5a  │ Admin taps date filter                                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5b  │ Options: Today, Last 7 Days, Last 30 Days, Custom             │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5c  │ Admin selects date range                                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5d  │ List updates with filtered results                            │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-3: Search by Session ID

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 5a  │ Admin enters session ID in search box                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5b  │ System finds matching job(s)                                  │
├─────┼────────────────────────────────────────────────────────────────┤
│ 5c  │ Display matching results                                      │
└─────┴────────────────────────────────────────────────────────────────┘
```

### AF-4: Retry Failed Job

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ 8a  │ Viewing failed job details                                    │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8b  │ [Retry Print] button available                                │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8c  │ Admin taps retry                                              │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8d  │ New print job created for same session                        │
├─────┼────────────────────────────────────────────────────────────────┤
│ 8e  │ Navigate to job monitoring                                    │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Exception Flows

### EX-1: No Print History

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ No print jobs exist for selected filters                      │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Display empty state:                                          │
│     │ "No print jobs found for this period"                         │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Suggest adjusting filters                                     │
└─────┴────────────────────────────────────────────────────────────────┘
```

### EX-2: Composite Image Missing

```
┌─────┬────────────────────────────────────────────────────────────────┐
│ E1  │ Job references composite file that no longer exists           │
├─────┼────────────────────────────────────────────────────────────────┤
│ E2  │ Display placeholder image with "Image unavailable"            │
├─────┼────────────────────────────────────────────────────────────────┤
│ E3  │ Job metadata still visible                                    │
└─────┴────────────────────────────────────────────────────────────────┘
```

---

## Postconditions

| ID | Condition |
|----|-----------|
| POST-1 | Admin can view print job history |
| POST-2 | Failed jobs identifiable |
| POST-3 | Can retry failed prints if needed |

---

## Business Rules

| ID | Rule |
|----|------|
| HIST-BR-1 | Default view: last 7 days |
| HIST-BR-2 | Maximum history depth: 90 days |
| HIST-BR-3 | Pagination: 20 jobs per page |
| HIST-BR-4 | Sort: newest first |
| HIST-BR-5 | Retry allowed for failed/cancelled jobs only |

---

## UI/UX Requirements

### Print History List

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back                Print History                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─── Summary (Last 7 Days) ────────────────────────────────┐   │
│  │                                                          │   │
│  │   Total: 156    ✅ 149 Success    ❌ 5 Failed    ⊘ 2 Cancel │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── Filters ──────────────────────────────────────────────┐   │
│  │  [All ▼]   [Last 7 Days ▼]   [🔍 Search...]              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── Job List ─────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  ┌────┬──────────────────────────────────────────────┐   │   │
│  │  │ ✅ │  Session abc-123                              │   │   │
│  │  │    │  Today, 14:32 • 1 copy                       │   │   │
│  │  │    │  Completed in 45s                            │ > │   │
│  │  └────┴──────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  ┌────┬──────────────────────────────────────────────┐   │   │
│  │  │ ❌ │  Session def-456                              │   │   │
│  │  │    │  Today, 14:15 • 2 copies                     │   │   │
│  │  │    │  Failed: Printer offline                     │ > │   │
│  │  └────┴──────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  ┌────┬──────────────────────────────────────────────┐   │   │
│  │  │ ✅ │  Session ghi-789                              │   │   │
│  │  │    │  Today, 13:58 • 1 copy                       │   │   │
│  │  │    │  Completed in 52s                            │ > │   │
│  │  └────┴──────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  │  (scroll for more...)                                    │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────┐  Page 1 of 8  ┌─────────┐                         │
│  │  Prev   │               │  Next   │                         │
│  └─────────┘               └─────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Job Detail View

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back                  Job Details                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Session: abc-123-def-456                                │   │
│  │  Status: ❌ FAILED                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── Composite ────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │         ┌─────────────────────────────┐                  │   │
│  │         │                             │                  │   │
│  │         │      [Composite Image]      │                  │   │
│  │         │                             │                  │   │
│  │         └─────────────────────────────┘                  │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── Timeline ─────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  14:15:00  ○ Job Created (1 copy)                        │   │
│  │  14:15:01  ○ Submitted to CUPS                           │   │
│  │  14:15:03  ○ Printer offline detected                    │   │
│  │  14:15:06  ○ Retry 1/3 scheduled                         │   │
│  │  14:15:09  ○ Retry 1 failed - still offline              │   │
│  │  14:15:17  ○ Retry 2 failed - still offline              │   │
│  │  14:15:25  ○ Retry 3 failed - still offline              │   │
│  │  14:15:25  ● Job Failed - max retries exceeded           │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─── Error Details ────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  Error Code:  PRINTER_OFFLINE                            │   │
│  │  Message:     Printer is offline                         │   │
│  │  Retries:     3/3                                        │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│             ┌─────────────────────────────────┐                 │
│             │       🔄 Retry Print            │                 │
│             └─────────────────────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technical Notes

### API Endpoints

```typescript
// GET /api/admin/print-history

interface PrintHistoryRequest {
  page?: number;           // Default: 1
  limit?: number;          // Default: 20, max: 100
  status?: 'all' | 'completed' | 'failed' | 'cancelled';
  from_date?: string;      // ISO 8601
  to_date?: string;        // ISO 8601
  search?: string;         // Session ID search
}

interface PrintHistoryResponse {
  jobs: PrintJobSummary[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
  summary: {
    total: number;
    completed: number;
    failed: number;
    cancelled: number;
    success_rate: number;
  };
}

interface PrintJobSummary {
  id: string;
  session_id: string;
  status: string;
  copies: number;
  created_at: string;
  completed_at?: string;
  duration_seconds?: number;
  error_code?: string;
  error_message?: string;
  composite_thumbnail_url?: string;
}

// GET /api/admin/print-history/{job_id}

interface PrintJobDetailResponse {
  job: PrintJobFull;
  session: SessionSummary;
  timeline: TimelineEvent[];
}

interface TimelineEvent {
  timestamp: string;
  event: string;
  details?: string;
}
```

### Backend Implementation

```python
# Print history repository query

class PrintHistoryRepository:
    async def get_history(
        self,
        page: int = 1,
        limit: int = 20,
        status: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
        search: str | None = None,
    ) -> tuple[list[PrintJob], int]:
        """Get paginated print history with filters."""

        query = """
            SELECT j.*, s.composite_path
            FROM print_jobs j
            LEFT JOIN sessions s ON j.session_id = s.id
            WHERE 1=1
        """
        params = []

        if status and status != 'all':
            query += " AND j.status = ?"
            params.append(status.upper())

        if from_date:
            query += " AND j.created_at >= ?"
            params.append(from_date.isoformat())

        if to_date:
            query += " AND j.created_at < ?"
            params.append((to_date + timedelta(days=1)).isoformat())

        if search:
            query += " AND (j.id LIKE ? OR j.session_id LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])

        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query})"
        total = await self._db.fetchone(count_query, params)

        # Add pagination
        query += " ORDER BY j.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, (page - 1) * limit])

        rows = await self._db.fetchall(query, params)
        jobs = [self._row_to_job(row) for row in rows]

        return jobs, total[0]

    async def get_summary(
        self,
        from_date: date,
        to_date: date,
    ) -> dict:
        """Get summary statistics for date range."""

        query = """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'CANCELLED' THEN 1 ELSE 0 END) as cancelled
            FROM print_jobs
            WHERE created_at >= ? AND created_at < ?
        """

        row = await self._db.fetchone(query, [
            from_date.isoformat(),
            (to_date + timedelta(days=1)).isoformat(),
        ])

        total = row['total'] or 0
        completed = row['completed'] or 0

        return {
            'total': total,
            'completed': completed,
            'failed': row['failed'] or 0,
            'cancelled': row['cancelled'] or 0,
            'success_rate': (completed / total * 100) if total > 0 else 100,
        }
```

### Frontend Hook

```typescript
// usePrintHistory hook

interface UsePrintHistoryOptions {
  initialPage?: number;
  limit?: number;
}

const usePrintHistory = (options: UsePrintHistoryOptions = {}) => {
  const [page, setPage] = useState(options.initialPage ?? 1);
  const [filters, setFilters] = useState({
    status: 'all',
    dateRange: 'last7days',
    search: '',
  });
  const [data, setData] = useState<PrintHistoryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { token } = useAdminAuth();

  const fetchHistory = useCallback(async () => {
    setIsLoading(true);

    const params = new URLSearchParams({
      page: page.toString(),
      limit: (options.limit ?? 20).toString(),
    });

    if (filters.status !== 'all') {
      params.set('status', filters.status);
    }

    // Convert date range to dates
    const { from, to } = getDateRange(filters.dateRange);
    params.set('from_date', from.toISOString());
    params.set('to_date', to.toISOString());

    if (filters.search) {
      params.set('search', filters.search);
    }

    try {
      const response = await fetch(
        `/api/admin/print-history?${params}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      const data = await response.json();
      setData(data);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    } finally {
      setIsLoading(false);
    }
  }, [page, filters, token, options.limit]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  return {
    data,
    isLoading,
    page,
    setPage,
    filters,
    setFilters,
    refetch: fetchHistory,
  };
};
```

---

## Related Use Cases

- **UC-101**: Admin Login (prerequisite)
- **UC-102**: View System Status (linked from dashboard)
- **UC-007**: Retry Failed Print (can retry from history)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-01-13 | System | Initial version |
