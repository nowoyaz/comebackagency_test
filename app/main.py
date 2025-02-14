# app/main.py
from fastapi import FastAPI
from .database import engine, SessionLocal
from . import models, crud, schemas
from .endpoints import books, users, web, admin

# Создаем таблицы, если не используются миграции
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Book Management System API",
    description="API для управления книгами с поддержкой CRUD операций, JWT-аутентификации и дополнительными возможностями импорта/экспорта.",
    version="1.0.0"
)

# Создаем супер-админа root с паролем 123 при запуске (если он не существует)
@app.on_event("startup")
def create_root_admin():
    db = SessionLocal()
    admin = crud.get_user_by_username(db, "root")
    if not admin:
        admin_data = schemas.UserCreate(username="root", password="123")
        crud.create_user(db, admin_data, is_admin=True)
    db.close()

# Подключаем роутеры
app.include_router(books.router)
app.include_router(users.router)
app.include_router(web.router)
app.include_router(admin.router)

@app.get("/api", tags=["root"])
def read_root():
    return {"message": "Welcome to the Book Management System API"}
