import pytest

@pytest.mark.asyncio
async def test_access_protected_route(test_client):
    # Login first
    login = await test_client.post("/auth/login", json={
        "email": "user@example.com",
        "password": "password123"
    })
    token = login.json()["access_token"]

    # Call protected route
    response = await test_client.get(
        "/user/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_info"]["email"] == "user@example.com"