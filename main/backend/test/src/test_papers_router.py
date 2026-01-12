import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from controller.api.app import create_app
from base.pg.entity import Paper
from common.model.enums import PaperStatus
from service.papers.schema import PaperUploadResponse, PaperDTO


def _fake_upload_file_response(paper_id: str):
    return PaperUploadResponse(paper_id=paper_id, status=PaperStatus.PENDING.value, message="ok")


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_upload_paper_ok(client):
    paper_id = str(uuid4())

    with patch("controller.api.papers.router.PaperService") as mock_service_cls:
        mock_service = mock_service_cls.return_value
        mock_service.upload_paper = AsyncMock(return_value=_fake_upload_file_response(paper_id))

        files = {"file": ("test.pdf", b"%PDF-1.4 test", "application/pdf")}
        resp = client.post("/papers/upload", files=files)

    assert resp.status_code == 200
    data = resp.json()
    assert data["paper_id"] == paper_id
    assert data["status"] == PaperStatus.PENDING.value


def test_get_paper_status_ok(client):
    paper_id = uuid4()
    user_id = uuid4()
    paper_dto = PaperDTO(
        id=paper_id,
        user_id=user_id,
        title="t",
        authors=[],
        abstract=None,
        file_key="k",
        file_url=None,
        status=PaperStatus.PENDING,
        created_at="2024-01-01T00:00:00"
    )

    with patch("controller.api.papers.router.PaperService") as mock_service_cls:
        mock_service = mock_service_cls.return_value
        mock_service.get_paper_status = AsyncMock(return_value=paper_dto)

        resp = client.get(f"/papers/{paper_id}/status", headers={"X-User-Id": str(user_id)})

    assert resp.status_code == 200
    data = resp.json()
    assert data["paper_id"] == str(paper_id)
    assert data["status"] == PaperStatus.PENDING.value


def test_get_paper_status_invalid_id(client):
    resp = client.get("/papers/not-a-uuid/status")
    assert resp.status_code == 400


def test_arxiv_search_ok(client):
    from service.papers.schema import PaperInfo
    
    with patch("controller.api.papers.router.ArxivService") as mock_service_cls:
        # Mock the instance created by the class
        mock_service = mock_service_cls.return_value
        # Mock the search_papers method
        mock_service.search_papers = AsyncMock(return_value=[
            PaperInfo(title="Test Paper", authors=["Me"], abstract="Test", source_id="123")
        ])
        
        resp = client.get("/papers/search/test")
        
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_count"] == 1
    assert data["papers"][0]["title"] == "Test Paper"
