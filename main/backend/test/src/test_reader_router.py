import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime

from controller.api.app import create_app
from base.pg.entity import User
from service.reader.schema import LayerResponse, LayerListResponse, AnnotationResponse, LayerCreate, AnnotationCreate
from service.reader.reader_service import get_reader_service, ReaderService
from controller.api.auth.router import get_current_user

@pytest.fixture
def mock_reader_service():
    service = AsyncMock(spec=ReaderService)
    return service

@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="test@example.com", hashed_password="pw")

@pytest.fixture
def client(mock_reader_service, mock_user):
    app = create_app()
    
    # Override dependencies
    async def override_get_reader_service():
        return mock_reader_service
        
    async def override_get_current_user():
        return mock_user
        
    app.dependency_overrides[get_reader_service] = override_get_reader_service
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    return TestClient(app)

def test_get_paper_layers(client, mock_reader_service, mock_user):
    paper_id = uuid4()
    layer_id = uuid4()
    
    mock_layers = LayerListResponse(layers=[
        LayerResponse(
            id=layer_id,
            paper_id=paper_id,
            user_id=mock_user.id,
            name="Test Layer",
            type="user",
            visible=True,
            created_at=datetime.now(),
            annotations=[]
        )
    ])
    
    mock_reader_service.get_layers_by_paper.return_value = mock_layers
    
    resp = client.get(f"/api/v1/reader/papers/{paper_id}/layers")
    
    assert resp.status_code == 200
    
    data = resp.json()
    assert data["code"] == 200
    assert len(data["data"]["layers"]) == 1
    assert data["data"]["layers"][0]["id"] == str(layer_id)

def test_create_layer(client, mock_reader_service, mock_user):
    paper_id = uuid4()
    layer_in = {"name": "New Layer", "type": "user", "visible": True}
    
    mock_response = LayerResponse(
        id=uuid4(),
        paper_id=paper_id,
        user_id=mock_user.id,
        name="New Layer",
        type="user",
        visible=True,
        created_at=datetime.now(),
        annotations=[]
    )
    
    mock_reader_service.create_layer.return_value = mock_response
    
    resp = client.post(f"/api/v1/reader/papers/{paper_id}/layers", json=layer_in)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert data["data"]["name"] == "New Layer"

def test_create_annotation(client, mock_reader_service):
    layer_id = uuid4()
    anno_in = {
        "type": "highlight",
        "rects": [{"x": 10, "y": 10, "width": 100, "height": 20, "pageIndex": 1}],
        "content": "Note",
        "color": "#FFFF00"
    }
    
    mock_response = AnnotationResponse(
        id=uuid4(),
        layer_id=layer_id,
        type="highlight",
        rects=[{"x": 10, "y": 10, "width": 100, "height": 20, "pageIndex": 1}],
        content="Note",
        color="#FFFF00",
        created_at=datetime.now()
    )
    
    mock_reader_service.create_annotation.return_value = mock_response
    
    resp = client.post(f"/api/v1/reader/layers/{layer_id}/annotations", json=anno_in)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert data["data"]["content"] == "Note"

def test_update_layer(client, mock_reader_service, mock_user):
    layer_id = uuid4()
    layer_in = {"name": "Updated Layer", "visible": False}
    
    mock_response = LayerResponse(
        id=layer_id,
        paper_id=uuid4(),
        user_id=mock_user.id,
        name="Updated Layer",
        type="user",
        visible=False,
        created_at=datetime.now(),
        annotations=[]
    )
    
    mock_reader_service.update_layer.return_value = mock_response
    
    resp = client.put(f"/api/v1/reader/layers/{layer_id}", json=layer_in)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert data["data"]["name"] == "Updated Layer"
    assert data["data"]["visible"] is False

def test_delete_layer(client, mock_reader_service):
    layer_id = uuid4()
    mock_reader_service.delete_layer.return_value = True
    
    resp = client.delete(f"/api/v1/reader/layers/{layer_id}")
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] == 200
    assert data["message"] == "Layer deleted successfully"

def test_delete_layer_not_found(client, mock_reader_service):
    layer_id = uuid4()
    mock_reader_service.delete_layer.return_value = False
    
    resp = client.delete(f"/api/v1/reader/layers/{layer_id}")
    
    assert resp.status_code == 404
