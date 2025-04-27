from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_login_get_user():
    # Регистрация нового пользователя
    register_data = {
        "first_name": "Test",
        "second_name": "User",
        "birthdate": "1990-01-01",
        "biography": "Testing user creation",
        "city": "Nowhere",
        "password": "testpassword123"
    }
    response = client.post("/user/register", json=register_data)
    assert response.status_code == 200
    user_id = response.json()["user_id"]
    assert user_id is not None

    # Логин
    login_data = {
        "id": user_id,
        "password": "testpassword123"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 200
    token = response.json()["token"]
    assert token is not None

    # Получение анкеты
    response = client.get(f"/user/get/{user_id}")
    assert response.status_code == 200
    user_info = response.json()
    assert user_info["first_name"] == "Test"
    assert user_info["second_name"] == "User"

def test_login_with_invalid_credentials():
    # Пытаемся залогиниться с левыми данными
    login_data = {
        "id": "00000000-0000-0000-0000-000000000000",  # фейковый id
        "password": "wrongpassword"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 404 or response.status_code == 400    