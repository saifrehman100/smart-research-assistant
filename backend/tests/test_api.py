"""API endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_upload_text_document(client: AsyncClient):
    """Test text document upload."""
    payload = {
        "type": "text",
        "text": "This is a test document about machine learning and AI.",
        "title": "Test Document",
        "author": "Test Author",
    }

    response = await client.post("/api/documents/upload-text", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Document"
    assert data["type"] == "text"
    assert data["processed"] is False


@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient):
    """Test listing documents."""
    # First, create a document
    payload = {
        "type": "text",
        "text": "Test content",
        "title": "Test Doc",
    }
    await client.post("/api/documents/upload-text", json=payload)

    # Then list documents
    response = await client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient):
    """Test listing conversations."""
    response = await client.get("/api/conversations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
