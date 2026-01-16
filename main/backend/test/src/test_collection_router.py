
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient
from controller.api.app import create_app
from service.collections.collection_service import CollectionService, get_collection_service
from controller.api.collections.schema import (
    CollectionResponse, 
    CollectionDetailResponse,
    AddPaperRequest
)
from service.papers.schema import PaperDTO
from common.model.enums import PaperStatus
from controller.api.auth.router import get_current_user
from base.pg.entity import User

@pytest.fixture
def mock_collection_service():
    return AsyncMock(spec=CollectionService)

@pytest.fixture
def current_user():
    return User(id=uuid4(), username="testuser", email="test@example.com", hashed_password="pw")

@pytest.fixture
def client(mock_collection_service, current_user):
    app = create_app()
    app.dependency_overrides[get_collection_service] = lambda: mock_collection_service
    app.dependency_overrides[get_current_user] = lambda: current_user
    return TestClient(app)

def test_create_collection(client, mock_collection_service, current_user):
    data = {
        "name": "My Collection",
        "description": "A test collection"
    }
    
    collection_id = uuid4()
    mock_response = CollectionResponse(
        id=collection_id,
        user_id=current_user.id,
        name=data["name"],
        description=data["description"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_collection_service.create_collection.return_value = mock_response
    
    response = client.post("/api/v1/collections", json=data)
    
    assert response.status_code == 201
    assert response.json()["id"] == str(collection_id)
    assert response.json()["name"] == data["name"]
    mock_collection_service.create_collection.assert_called_once()

def test_get_collections(client, mock_collection_service, current_user):
    collection_id = uuid4()
    mock_response = CollectionResponse(
        id=collection_id,
        user_id=current_user.id,
        name="My Collection",
        description="A test collection",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_collection_service.get_user_collections.return_value = [mock_response]
    
    response = client.get("/api/v1/collections")
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(collection_id)
    mock_collection_service.get_user_collections.assert_called_once()

def test_get_collection_detail(client, mock_collection_service, current_user):
    collection_id = uuid4()
    paper_id = uuid4()
    
    mock_response = CollectionDetailResponse(
        id=collection_id,
        user_id=current_user.id,
        name="My Collection",
        description="A test collection",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        papers=[
                PaperDTO(
                    id=paper_id,
                    user_id=current_user.id,
                    title="Test Paper",
                    authors=["Author"],
                    status=PaperStatus.COMPLETED,
                    created_at=datetime.now(),
                    file_key="test.pdf"
                )
            ]
    )
    mock_collection_service.get_collection_detail.return_value = mock_response
    
    response = client.get(f"/api/v1/collections/{collection_id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == str(collection_id)
    assert len(response.json()["papers"]) == 1
    assert response.json()["papers"][0]["id"] == str(paper_id)

def test_get_collection_detail_not_found(client, mock_collection_service):
    collection_id = uuid4()
    mock_collection_service.get_collection_detail.return_value = None
    
    response = client.get(f"/api/v1/collections/{collection_id}")
    
    assert response.status_code == 404

def test_update_collection(client, mock_collection_service, current_user):
    collection_id = uuid4()
    data = {"name": "Updated Name"}
    
    mock_response = CollectionResponse(
        id=collection_id,
        user_id=current_user.id,
        name=data["name"],
        description="Old description",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_collection_service.update_collection.return_value = mock_response
    
    response = client.put(f"/api/v1/collections/{collection_id}", json=data)
    
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

def test_delete_collection(client, mock_collection_service):
    collection_id = uuid4()
    mock_collection_service.delete_collection.return_value = True
    
    response = client.delete(f"/api/v1/collections/{collection_id}")
    
    assert response.status_code == 204

def test_delete_collection_not_found(client, mock_collection_service):
    collection_id = uuid4()
    mock_collection_service.delete_collection.return_value = False
    
    response = client.delete(f"/api/v1/collections/{collection_id}")
    
    assert response.status_code == 404

def test_add_paper_to_collection(client, mock_collection_service):
    collection_id = uuid4()
    paper_id = uuid4()
    data = {"paper_id": str(paper_id)}
    
    mock_collection_service.add_paper_to_collection.return_value = True
    
    response = client.post(f"/api/v1/collections/{collection_id}/papers", json=data)
    
    assert response.status_code == 201
    assert response.json()["message"] == "添加成功"

def test_add_paper_to_collection_fail(client, mock_collection_service):
    collection_id = uuid4()
    paper_id = uuid4()
    data = {"paper_id": str(paper_id)}
    
    mock_collection_service.add_paper_to_collection.return_value = False
    
    response = client.post(f"/api/v1/collections/{collection_id}/papers", json=data)
    
    assert response.status_code == 400

def test_remove_paper_from_collection(client, mock_collection_service):
    collection_id = uuid4()
    paper_id = uuid4()
    
    mock_collection_service.remove_paper_from_collection.return_value = True
    
    response = client.delete(f"/api/v1/collections/{collection_id}/papers/{paper_id}")
    
    assert response.status_code == 204

def test_remove_paper_from_collection_fail(client, mock_collection_service):
    collection_id = uuid4()
    paper_id = uuid4()
    
    mock_collection_service.remove_paper_from_collection.return_value = False
    
    response = client.delete(f"/api/v1/collections/{collection_id}/papers/{paper_id}")
    
    assert response.status_code == 404
