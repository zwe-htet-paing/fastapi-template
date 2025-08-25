import pytest


@pytest.mark.asyncio
async def test_signup(test_client):
    # Signup
    response = await test_client.post("/auth/signup", json={
        "username": "testuser",
        "email": "user@example.com", 
        "password": "password123"}
        )
    assert response.status_code == 200
    assert "id" in response.json()['user']

@pytest.mark.asyncio
async def test_login(test_client): 
    # Login
    response = await test_client.post("/auth/login", json={
        "email": "user@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    