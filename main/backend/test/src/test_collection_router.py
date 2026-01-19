
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from controller.api.app import create_app
from controller.api.collections.schema import CollectionDetailResponse, CollectionResponse
from service.collections.collection_service import CollectionService, get_collection_service
from controller.api.collections.schema import CollectionUpdate
from base.pg.entity import Collection
from base.pg.service import CollectionRepository, UserRepository
from common.model.enums import PaperStatus
from service.papers.schema import PaperDTO
from controller.api.auth.router import get_current_user
from base.pg.entity import User

@pytest.fixture
def mock_collection_service():
    return AsyncMock(spec=CollectionService)

@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="test@example.com")


@pytest.fixture
def client(mock_collection_service, mock_user):
    app = create_app()

    async def override_get_collection_service():
        return mock_collection_service

    async def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_collection_service] = override_get_collection_service
    app.dependency_overrides[get_current_user] = override_get_current_user
    return TestClient(app)

def test_create_collection(client, mock_collection_service):
    user_id = uuid4()
    data = {
        "name": "My Collection",
        "description": "A test collection"
    }
    
    collection_id = uuid4()
    mock_response = CollectionResponse(
        id=collection_id,
        user_id=user_id,
        name=data["name"],
        description=data["description"],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_collection_service.create_collection.return_value = mock_response
    
    response = client.post(
        "/api/v1/collections",
        json=data,
    )
    
    assert response.status_code == 201
    assert response.json()["id"] == str(collection_id)
    assert response.json()["name"] == data["name"]
    mock_collection_service.create_collection.assert_called_once()

def test_get_collections(client, mock_collection_service):
    user_id = uuid4()
    collection_id = uuid4()
    mock_response = CollectionResponse(
        id=collection_id,
        user_id=user_id,
        name="My Collection",
        description="A test collection",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_collection_service.get_user_collections.return_value = [mock_response]
    
    response = client.get(
        "/api/v1/collections",
    )
    
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(collection_id)
    mock_collection_service.get_user_collections.assert_called_once()

def test_get_collection_detail(client, mock_collection_service):
    user_id = uuid4()
    collection_id = uuid4()
    paper_id = uuid4()
    
    mock_response = CollectionDetailResponse(
        id=collection_id,
        user_id=user_id,
        name="My Collection",
        description="A test collection",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        papers=[
                PaperDTO(
                    id=paper_id,
                    user_id=user_id,
                    title="Test Paper",
                    authors=["Author"],
                    status=PaperStatus.COMPLETED,
                    created_at=datetime.now(),
                    file_key="test.pdf"
                )
            ]
    )
    mock_collection_service.get_collection_detail.return_value = mock_response
    
    response = client.get(
        f"/api/v1/collections/{collection_id}",
    )
    
    assert response.status_code == 200
    assert response.json()["id"] == str(collection_id)
    assert len(response.json()["papers"]) == 1
    assert response.json()["papers"][0]["id"] == str(paper_id)

def test_get_collection_detail_not_found(client, mock_collection_service):
    collection_id = uuid4()
    mock_collection_service.get_collection_detail.return_value = None
    
    response = client.get(
        f"/api/v1/collections/{collection_id}",
    )
    
    assert response.status_code == 404

def test_update_collection(client, mock_collection_service):
    user_id = uuid4()
    collection_id = uuid4()
    data = {"name": "Updated Name"}
    
    mock_response = CollectionResponse(
        id=collection_id,
        user_id=user_id,
        name=data["name"],
        description="Old description",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    mock_collection_service.update_collection.return_value = mock_response
    
    response = client.put(
        f"/api/v1/collections/{collection_id}",
        json=data,
    )
    
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"

def test_delete_collection(client, mock_collection_service):
    user_id = uuid4()
    collection_id = uuid4()
    mock_collection_service.delete_collection.return_value = True
    
    response = client.delete(
        f"/api/v1/collections/{collection_id}",
    )
    
    assert response.status_code == 204

def test_delete_collection_not_found(client, mock_collection_service):
    user_id = uuid4()
    collection_id = uuid4()
    mock_collection_service.delete_collection.return_value = False
    
    response = client.delete(
        f"/api/v1/collections/{collection_id}",
    )
    
    assert response.status_code == 404

def test_add_paper_to_collection(client, mock_collection_service):
    user_id = uuid4()
    collection_id = uuid4()
    paper_id = uuid4()
    data = {"paper_id": str(paper_id)}
    
    mock_collection_service.add_paper_to_collection.return_value = True
    
    response = client.post(
        f"/api/v1/collections/{collection_id}/papers",
        json=data,
    )
    
    assert response.status_code == 201
    assert response.json()["message"] == "添加成功"

def test_add_paper_to_collection_fail(client, mock_collection_service):
    user_id = uuid4()
    collection_id = uuid4()
    paper_id = uuid4()
    data = {"paper_id": str(paper_id)}
    
    mock_collection_service.add_paper_to_collection.return_value = False
    
    response = client.post(
        f"/api/v1/collections/{collection_id}/papers",
        json=data,
    )
    
    assert response.status_code == 400

def test_remove_paper_from_collection(client, mock_collection_service):
    user_id = uuid4()
    collection_id = uuid4()
    paper_id = uuid4()
    
    mock_collection_service.remove_paper_from_collection.return_value = True
    
    response = client.delete(
        f"/api/v1/collections/{collection_id}/papers/{paper_id}",
    )
    
    assert response.status_code == 204

def test_remove_paper_from_collection_fail(client, mock_collection_service):
    user_id = uuid4()
    collection_id = uuid4()
    paper_id = uuid4()
    
    mock_collection_service.remove_paper_from_collection.return_value = False
    
    response = client.delete(
        f"/api/v1/collections/{collection_id}/papers/{paper_id}",
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_collection_service_forbid_rename_default_collection(monkeypatch):
    session = AsyncMock()
    service = CollectionService(session)

    user_id = uuid4()
    collection_id = uuid4()
    collection = Collection(
        id=collection_id,
        user_id=user_id,
        name="默认收藏夹",
        description="系统默认收藏夹",
        is_default=True,
    )

    async def _get_collection_by_id(_session, _collection_id):
        return collection

    monkeypatch.setattr(CollectionRepository, "get_collection_by_id", _get_collection_by_id)

    with pytest.raises(HTTPException) as exc:
        await service.update_collection(
            collection_id,
            user_id,
            CollectionUpdate(name="新名字"),
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_collection_service_forbid_delete_default_collection(monkeypatch):
    session = AsyncMock()
    service = CollectionService(session)

    user_id = uuid4()
    collection_id = uuid4()
    collection = Collection(
        id=collection_id,
        user_id=user_id,
        name="默认收藏夹",
        description="系统默认收藏夹",
        is_default=True,
    )

    async def _get_collection_by_id(_session, _collection_id):
        return collection

    monkeypatch.setattr(CollectionRepository, "get_collection_by_id", _get_collection_by_id)

    with pytest.raises(HTTPException) as exc:
        await service.delete_collection(collection_id, user_id)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_collection_service_ensure_default_collection_creates_when_missing(monkeypatch):
    session = AsyncMock()
    service = CollectionService(session)

    user_id = uuid4()
    monkeypatch.setattr(UserRepository, "get_user_by_id", AsyncMock(return_value=object()))
    created_collection = Collection(
        user_id=user_id,
        name="默认收藏夹",
        description="系统默认收藏夹",
        is_default=True,
    )

    async def _get_default_collection(_session, _user_id):
        return None

    async def _create_collection(_session, collection: Collection):
        return created_collection

    monkeypatch.setattr(CollectionRepository, "get_default_collection", _get_default_collection)
    monkeypatch.setattr(CollectionRepository, "create_collection", _create_collection)

    result = await service.ensure_default_collection(user_id)
    assert result.is_default is True


@pytest.mark.asyncio
async def test_collection_service_ensure_default_collection_falls_back_on_integrity_error(monkeypatch):
    session = AsyncMock()
    service = CollectionService(session)

    user_id = uuid4()
    monkeypatch.setattr(UserRepository, "get_user_by_id", AsyncMock(return_value=object()))
    existing_collection = Collection(
        user_id=user_id,
        name="默认收藏夹",
        description="系统默认收藏夹",
        is_default=True,
    )

    calls = {"count": 0}

    async def _get_default_collection(_session, _user_id):
        calls["count"] += 1
        if calls["count"] == 1:
            return None
        return existing_collection

    async def _create_collection(_session, _collection: Collection):
        raise IntegrityError("stmt", {}, Exception("orig"))

    monkeypatch.setattr(CollectionRepository, "get_default_collection", _get_default_collection)
    monkeypatch.setattr(CollectionRepository, "create_collection", _create_collection)

    result = await service.ensure_default_collection(user_id)
    assert result.is_default is True


@pytest.mark.asyncio
async def test_collection_service_get_user_collections_ensures_default_collection_when_offset_zero(monkeypatch):
    session = AsyncMock()
    service = CollectionService(session)

    user_id = uuid4()
    service.ensure_default_collection = AsyncMock(return_value=Collection(
        user_id=user_id,
        name="默认收藏夹",
        description="系统默认收藏夹",
        is_default=True,
    ))

    collections = [
        Collection(
            id=uuid4(),
            user_id=user_id,
            name="默认收藏夹",
            description="系统默认收藏夹",
            is_default=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    ]

    async def _get_user_collections(_session, _user_id, _limit, _offset):
        return collections

    monkeypatch.setattr(CollectionRepository, "get_user_collections", _get_user_collections)

    await service.get_user_collections(user_id, limit=10, offset=0)
    service.ensure_default_collection.assert_awaited_once()


@pytest.mark.asyncio
async def test_collection_service_get_user_collections_does_not_ensure_default_collection_when_offset_nonzero(monkeypatch):
    session = AsyncMock()
    service = CollectionService(session)

    user_id = uuid4()
    service.ensure_default_collection = AsyncMock()

    async def _get_user_collections(_session, _user_id, _limit, _offset):
        return []

    monkeypatch.setattr(CollectionRepository, "get_user_collections", _get_user_collections)

    await service.get_user_collections(user_id, limit=10, offset=10)
    service.ensure_default_collection.assert_not_awaited()


@pytest.mark.asyncio
async def test_collection_service_allow_update_default_collection_description(monkeypatch):
    session = AsyncMock()
    service = CollectionService(session)

    user_id = uuid4()
    collection_id = uuid4()
    collection = Collection(
        id=collection_id,
        user_id=user_id,
        name="默认收藏夹",
        description="系统默认收藏夹",
        is_default=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    async def _get_collection_by_id(_session, _collection_id):
        return collection

    async def _update_collection(_session, updated_collection: Collection):
        return updated_collection

    monkeypatch.setattr(CollectionRepository, "get_collection_by_id", _get_collection_by_id)
    monkeypatch.setattr(CollectionRepository, "update_collection", _update_collection)

    resp = await service.update_collection(
        collection_id,
        user_id,
        CollectionUpdate(description="新的描述"),
    )

    assert resp is not None
    assert resp.name == "默认收藏夹"
    assert resp.description == "新的描述"
