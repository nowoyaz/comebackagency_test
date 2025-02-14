from sqlalchemy.orm import Session
from sqlalchemy import desc
from . import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Пользователи
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate, is_admin: bool = False):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password, is_admin=is_admin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Книги
def get_book(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.id == book_id).first()

def get_books(db: Session, skip: int = 0, limit: int = 10, sort_by: str = None, order: str = "asc"):
    query = db.query(models.Book)
    if sort_by:
        # Поддерживаем сортировку по title и published_year
        if sort_by == "title":
            sort_column = models.Book.title
        elif sort_by == "published_year":
            sort_column = models.Book.published_year
        else:
            sort_column = None

        if sort_column:
            if order == "desc":
                sort_column = desc(sort_column)
            query = query.order_by(sort_column)
    return query.offset(skip).limit(limit).all()

def count_books(db: Session):
    return db.query(models.Book).count()

def create_book(db: Session, book: schemas.BookCreate):
    authors_instances = []
    for author_name in book.authors:
        author = db.query(models.Author).filter(models.Author.name == author_name).first()
        if not author:
            author = models.Author(name=author_name)
            db.add(author)
            db.commit()
            db.refresh(author)
        authors_instances.append(author)
    db_book = models.Book(
        title=book.title,
        genre=book.genre,
        published_year=book.published_year,
        authors=authors_instances
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def update_book(db: Session, book_id: int, book_update: schemas.BookUpdate):
    db_book = get_book(db, book_id)
    if not db_book:
        return None
    if book_update.title is not None:
        db_book.title = book_update.title
    if book_update.genre is not None:
        db_book.genre = book_update.genre
    if book_update.published_year is not None:
        db_book.published_year = book_update.published_year
    if book_update.authors is not None:
        authors_instances = []
        for author_name in book_update.authors:
            author = db.query(models.Author).filter(models.Author.name == author_name).first()
            if not author:
                author = models.Author(name=author_name)
                db.add(author)
                db.commit()
                db.refresh(author)
            authors_instances.append(author)
        db_book.authors = authors_instances
    db.commit()
    db.refresh(db_book)
    return db_book

def delete_book(db: Session, book_id: int):
    db_book = get_book(db, book_id)
    if db_book:
        db.delete(db_book)
        db.commit()
    return db_book
