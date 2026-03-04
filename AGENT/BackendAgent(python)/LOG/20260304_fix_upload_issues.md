# Fix Upload Issues Log

## Issues
1. Local upload failed with 404 (Endpoint mismatch).
2. URL upload stuck in "spinning" state (Background task not triggered/Job ID not returned).

## Changes
### Frontend
- Modified `main/frontend/src/services/paper.service.ts`:
  - Changed `uploadLocal` endpoint from `/papers/upload/local` to `/papers/upload`.

### Backend
- Modified `main/backend/src/service/papers/paper_service.py`:
  - In `upload_paper` method:
    - Uncommented `_trigger_process_task` to auto-start parsing task upon upload.
    - Updated `PaperUploadResponse` to return the valid `job_id` instead of `None`.

## Verification
- Checked code logic: `upload_paper` now correctly starts the `process_pdf_task` and returns the ID.
- Frontend now points to the correct existing backend route.
