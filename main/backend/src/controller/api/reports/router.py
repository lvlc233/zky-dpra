from uuid import UUID, uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from controller.api.reports.schema import ReportCreate, ReportResponse, ReportListResponse


# 临时 Mock 依赖
def get_current_user_id():
    return UUID("12345678-1234-5678-1234-567812345678")

router = APIRouter(tags=["reports"])

@router.get("/papers/{paper_id}/reports", response_model=ReportListResponse)
async def list_reports(
    paper_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    # TODO: Implement DB list
    return {"reports": []}

@router.post("/papers/{paper_id}/reports", response_model=ReportResponse)
async def create_report(
    paper_id: UUID,
    report_in: ReportCreate,
    user_id: UUID = Depends(get_current_user_id)
):
    # TODO: Trigger Arq task
    return {
        "id": uuid4(),
        "paper_id": paper_id,
        "title": f"Report for {paper_id}",
        "type": report_in.type,
        "status": "generating",
        "created_at": datetime.utcnow()
    }

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    # TODO: Implement DB get
    return {
        "id": report_id,
        "paper_id": uuid4(),
        "title": "Mock Report",
        "type": "deep_research",
        "status": "completed",
        "content": "# Research Report\n\nContent...",
        "created_at": datetime.utcnow()
    }
