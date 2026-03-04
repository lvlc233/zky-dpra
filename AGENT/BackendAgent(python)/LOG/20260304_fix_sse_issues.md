# Fix SSE Issues Log

## Issues
1. Frontend `Uncaught SyntaxError: "undefined" is not valid JSON` in `use-job-progress.ts`.
   - Cause: `addEventListener('error', ...)` was catching native SSE connection errors (which have no data), but treating them as message events with JSON payload.
2. Progress updates not showing (spinning indefinitely).
   - Cause: Backend was sending capitalized event names (`JobProgress`, `JobEnd`), but frontend was listening for lowercase names (`progress`, `end`).

## Changes
### Backend
- Modified `main/backend/src/service/reader/job_service.py`:
  - Updated `_format_sse` to send lowercase event names (`start`, `progress`, `end`).
  - Mapped `error` state to `job_error` event name to avoid conflict with native SSE error event.

### Frontend
- Modified `main/frontend/src/hooks/use-job-progress.ts`:
  - Changed `addEventListener('error', ...)` to `addEventListener('job_error', ...)` to match the new backend event name and avoid catching connection errors.
  - Connection errors are now handled solely by `eventSource.onerror`.

## Verification
- Code logic review: Event names now align between frontend and backend.
- Native error handling is separated from custom job error messages.
