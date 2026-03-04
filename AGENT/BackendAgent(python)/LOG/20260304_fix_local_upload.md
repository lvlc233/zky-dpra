# Fix Local Upload Issues Log

## Issues
1. Local upload failed with `422 Unprocessable Entity` (Field required: file).
   - Cause: Frontend was sending `files` (plural) field in FormData, but backend expected `file` (singular).
   - Backend endpoint `/papers/upload` only accepts a single file.
2. Response type mismatch.
   - Frontend expected `PapersUploadResponse[]` (array) but backend returned `PaperUploadResponse` (single object).
   - Backend `PaperUploadResponse` was missing `title` field required by frontend.

## Changes
### Backend
- Modified `main/backend/src/service/papers/schema.py`:
  - Added `title: str` to `PaperUploadResponse` model.
- Modified `main/backend/src/service/papers/paper_service.py`:
  - Updated `upload_paper` method to populate `title` in the returned `PaperUploadResponse`.

### Frontend
- Modified `main/frontend/src/services/paper.service.ts`:
  - Refactored `uploadLocal` to:
    1. Iterate over the selected files array.
    2. Send a separate POST request to `/papers/upload` for each file (using key `file`).
    3. Use `Promise.all` to wait for all uploads and return an array of responses, matching the expected return type `Promise<PapersUploadResponse[]>`.

## Verification
- Code logic review: 
  - Frontend now correctly matches the backend's single-file upload interface.
  - Backend response now includes the required `title` field.
  - Frontend aggregates multiple single-file upload responses into the expected array format.
