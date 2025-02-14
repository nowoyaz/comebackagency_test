# app/endpoints/web.py
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .. import crud, auth, database, schemas
from datetime import timedelta

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def home(request: Request, page: int = 1, sort_by: str = None, order: str = "asc",
         db: Session = Depends(database.get_db),
         user = Depends(auth.get_current_user)):
    books = crud.get_books(db, skip=(page - 1) * 10, limit=10, sort_by=sort_by, order=order)
    total_books = crud.count_books(db)
    total_pages = (total_books + 9) // 10

    # Показываем JWT-токен только если пользователь существует и является администратором
    token = request.cookies.get("access_token") if (user and user.is_admin) else None

    return templates.TemplateResponse("index.html", {
        "request": request,
        "books": books,
        "page": page,
        "total_pages": total_pages,
        "sort_by": sort_by,
        "order": order,
        "user": user,
        "token": token
    })

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, user = Depends(auth.get_current_user)):
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request, "message": None})

@router.post("/login", response_class=HTMLResponse)
def login(request: Request, username: str = Form(...), password: str = Form(...),
          db: Session = Depends(database.get_db)):
    user = crud.get_user_by_username(db, username=username)
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    if not user or not pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "message": "Invalid credentials"})
    access_token = auth.create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=30))
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, user = Depends(auth.get_current_user)):
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("register.html", {"request": request, "message": None})

@router.post("/register", response_class=HTMLResponse)
def register(request: Request, username: str = Form(...), password: str = Form(...),
             db: Session = Depends(database.get_db)):
    if crud.get_user_by_username(db, username=username):
        return templates.TemplateResponse("register.html", {"request": request, "message": "User already exists"})
    user_data = schemas.UserCreate(username=username, password=password)
    crud.create_user(db, user_data, is_admin=False)
    return RedirectResponse(url="/login", status_code=302)

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response
