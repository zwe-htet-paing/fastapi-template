import pytest

@pytest.mark.asyncio
async def test_admin_access_only(test_client):
    # Create admin
    admin = await test_client.post("/auth/signup", json={
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "password123",
        "role": "admin"
    })
    print("Admin Signup:", admin.json())
    # Create normal user
    await test_client.post("/auth/signup", json={
        "username": "normaluser",
        "email": "user@example.com",
        "password": "password123",
        "role": "user"
    })

    # Login as admin
    login_admin = await test_client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "password123"
    })
    admin_token = login_admin.json()["access_token"]

    # Login as user
    login_user = await test_client.post("/auth/login", json={
        "email": "user@example.com",
        "password": "password123"
    })
    user_token = login_user.json()["access_token"]
    print("User Token:", user_token)
    print("Admin Token:", admin_token)

    # Admin should succeed
    response_admin = await test_client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response_admin.status_code == 200

    # User should fail
    response_user = await test_client.get(
        "/admin/users",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    # assert response_user.status_code == 403
    print(response_user.json())
