# app/endpoints/admin.py
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form, UploadFile, File
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from datetime import datetime
from sqlalchemy.orm import Session
import csv, io, json
from .. import crud, auth, database, schemas

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

def get_current_admin(user=Depends(auth.get_current_user)):
    if not user or not user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied. You are not an admin.")
    return user

@router.get("/", response_class=HTMLResponse)
def admin_home(request: Request, db: Session = Depends(database.get_db),
               admin: schemas.UserOut = Depends(get_current_admin)):
    books = crud.get_books(db, skip=0, limit=100)
    return templates.TemplateResponse("admin_home.html", {"request": request, "books": books, "admin": admin})

@router.get("/book/create", response_class=HTMLResponse)
def admin_create_book_get(request: Request, admin: schemas.UserOut = Depends(get_current_admin)):
    return templates.TemplateResponse("admin_create_book.html", {"request": request, "admin": admin, "current_year": datetime.now().year})


@router.post("/book/create", response_class=HTMLResponse)
def admin_create_book_post(
    request: Request,
    title: str = Form(...),
    genre: str = Form(...),
    published_year: int = Form(...),
    authors: str = Form(...),
    db: Session = Depends(database.get_db),
    admin: schemas.UserOut = Depends(get_current_admin)
):
    authors_list = [a.strip() for a in authors.split(",") if a.strip()]
    book_data = schemas.BookCreate(title=title, genre=genre, published_year=published_year, authors=authors_list)
    crud.create_book(db, book_data)
    return RedirectResponse(url="/admin", status_code=302)

@router.get("/book/{book_id}/edit", response_class=HTMLResponse)
def admin_edit_book_get(request: Request, book_id: int, db: Session = Depends(database.get_db),
                        admin: schemas.UserOut = Depends(get_current_admin)):
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return templates.TemplateResponse("admin_edit_book.html", {"request": request, "book": book, "admin": admin, "current_year": datetime.now().year})



@router.post("/book/{book_id}/edit", response_class=HTMLResponse)
def admin_edit_book_post(
    request: Request,
    book_id: int,
    title: str = Form(...),
    genre: str = Form(...),
    published_year: int = Form(...),
    authors: str = Form(...),
    db: Session = Depends(database.get_db),
    admin: schemas.UserOut = Depends(get_current_admin)
):
    authors_list = [a.strip() for a in authors.split(",") if a.strip()]
    update_data = schemas.BookUpdate(title=title, genre=genre, published_year=published_year, authors=authors_list)
    updated_book = crud.update_book(db, book_id, update_data)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return RedirectResponse(url="/admin", status_code=302)

@router.post("/book/{book_id}/delete", response_class=HTMLResponse)
def admin_delete_book(request: Request, book_id: int, db: Session = Depends(database.get_db),
                      admin: schemas.UserOut = Depends(get_current_admin)):
    crud.delete_book(db, book_id)
    return RedirectResponse(url="/admin", status_code=302)

@router.get("/export", response_class=Response)
def admin_export_books(format: str = "json", db: Session = Depends(database.get_db),
                       admin: schemas.UserOut = Depends(get_current_admin)):
    books = crud.get_books(db, skip=0, limit=1000)
    books_data = [schemas.BookOut.from_orm(book).dict() for book in books]
    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "genre", "published_year", "authors"])
        for book in books_data:
            authors = ", ".join([a["name"] for a in book["authors"]])
            writer.writerow([book["id"], book["title"], book["genre"], book["published_year"], authors])
        response = Response(content=output.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=books.csv"
        return response
    else:
        response = JSONResponse(content=books_data)
        response.headers["Content-Disposition"] = "attachment; filename=books.json"
        return response

@router.post("/import", response_class=HTMLResponse)
async def admin_import_books(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    admin: schemas.UserOut = Depends(get_current_admin)
):
    content = await file.read()
    imported = 0
    if file.filename.lower().endswith(".csv"):
        decoded = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))
        for row in reader:
            authors_list = [a.strip() for a in row["authors"].split(",") if a.strip()]
            try:
                book_data = schemas.BookCreate(
                    title=row["title"],
                    genre=row["genre"],
                    published_year=int(row["published_year"]),
                    authors=authors_list
                )
                crud.create_book(db, book_data)
                imported += 1
            except Exception:
                continue
    elif file.filename.lower().endswith(".json"):
        try:
            data = json.loads(content)
            for item in data:
                authors_list = item.get("authors")
                if isinstance(authors_list, list) and authors_list and isinstance(authors_list[0], dict):
                    authors_list = [a["name"] for a in authors_list]
                book_data = schemas.BookCreate(
                    title=item["title"],
                    genre=item["genre"],
                    published_year=int(item["published_year"]),
                    authors=authors_list
                )
                crud.create_book(db, book_data)
                imported += 1
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON format")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    return RedirectResponse(url="/admin", status_code=302)
