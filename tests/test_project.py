# tests/test_project.py
import os
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app import crud, schemas

client = TestClient(app)

# Фикстура, использующая заранее созданного администратора root/123
@pytest.fixture(scope="module")
def admin_token():
    # Выполнение логина через API (endpoint для логина: /api/users/login)
    response = client.post("/api/users/login", data={"username": "root", "password": "123"})
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return token

def test_import_csv(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    csv_file_path = os.path.join(os.path.dirname(__file__), "sample_books.csv")
    with open(csv_file_path, "rb") as f:
        files = {"file": ("sample_books.csv", f, "text/csv")}
        # Используем follow_redirects=False для проверки статуса редиректа
        response = client.post("/admin/import", files=files, headers=headers, follow_redirects=False)
    assert response.status_code == 302, f"CSV import failed: {response.text}"
    
    # Проверяем экспорт в JSON для подтверждения импорта
    response_export = client.get("/admin/export?format=json", headers=headers)
    assert response_export.status_code == 200, f"Export failed: {response_export.text}"
    data = response_export.json()
    titles = [book["title"] for book in data]
    assert "CSV Book" in titles, "CSV Book not found in export"
    assert "CSV Book2" in titles, "CSV Book2 not found in export"

def test_import_json(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    json_file_path = os.path.join(os.path.dirname(__file__), "sample_books.json")
    with open(json_file_path, "rb") as f:
        files = {"file": ("sample_books.json", f, "application/json")}
        response = client.post("/admin/import", files=files, headers=headers, follow_redirects=False)
    assert response.status_code == 302, f"JSON import failed: {response.text}"
    
    response_export = client.get("/admin/export?format=json", headers=headers)
    assert response_export.status_code == 200, f"Export failed: {response_export.text}"
    data = response_export.json()
    titles = [book["title"] for book in data]
    assert "JSON Book" in titles, "JSON Book not found in export"
    assert "JSON Book2" in titles, "JSON Book2 not found in export"

@pytest.fixture(scope="module")
def db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_register_normal_user():
    response = client.post(
        "/api/users/register",
        json={"username": "user1", "password": "secret"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == "user1"
    # Обычный пользователь не имеет прав администратора, поэтому is_admin должно быть False (или отсутствовать)
    assert data.get("is_admin") is False

def test_login_user():
    response = client.post(
        "/api/users/login",
        data={"username": "user1", "password": "secret"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    # Обычный пользователь не является администратором, поэтому их JWT-токен не используется для отображения в админке

def test_create_book():
    # Используем администратора для создания книги
    admin_token = client.post("/api/users/login", data={"username": "root", "password": "123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    book_data = {
        "title": "Test Book",
        "genre": "Fiction",
        "published_year": 2020,
        "authors": ["Author A"]
    }
    response = client.post("/api/books/", json=book_data, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "Test Book"
    assert len(data["authors"]) == 1
    return data["id"]

def test_update_book():
    admin_token = client.post("/api/users/login", data={"username": "root", "password": "123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Создаем книгу для обновления
    book_data = {
        "title": "Old Title",
        "genre": "Fiction",
        "published_year": 2021,
        "authors": ["Author B"]
    }
    response = client.post("/api/books/", json=book_data, headers=headers)
    assert response.status_code == 200, response.text
    book_id = response.json()["id"]

    update_data = {
        "title": "New Title",
        "genre": "Fiction",
        "published_year": 2021,
        "authors": ["Author B"]
    }
    response = client.put(f"/api/books/{book_id}", json=update_data, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["title"] == "New Title"

def test_delete_book():
    admin_token = client.post("/api/users/login", data={"username": "root", "password": "123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    book_data = {
        "title": "To Delete",
        "genre": "Fiction",
        "published_year": 2022,
        "authors": ["Author C"]
    }
    response = client.post("/api/books/", json=book_data, headers=headers)
    assert response.status_code == 200, response.text
    book_id = response.json()["id"]

    response = client.delete(f"/api/books/{book_id}", headers=headers)
    assert response.status_code == 200, response.text

    response = client.get(f"/api/books/{book_id}", headers=headers)
    assert response.status_code == 404, "Deleted book is still accessible"

def test_admin_panel_access():
    # Проверка, что обычный пользователь не имеет доступа к админке
    response = client.post("/api/users/login", data={"username": "user1", "password": "secret"})
    user_token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {user_token}"}
    response = client.get("/admin/", headers=headers)
    assert response.status_code == 403

    # Проверка доступа для администратора (root)
    admin_token = client.post("/api/users/login", data={"username": "root", "password": "123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/admin/", headers=headers)
    assert response.status_code == 200, response.text
