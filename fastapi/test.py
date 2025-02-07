from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID

app = FastAPI()

class Book(BaseModel):
    id:UUID
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    year: int = Field(ge=1900, le=2100)
    discription: str = Field(min_length=1)
    rating: float = Field(ge=0, le=5)

BOOKS=[]


@app.get("/")
def read_api():
    return BOOKS

@app.post("/")
def create_book(book: Book):
    BOOKS.append(book)
    return book

def update_book(id: UUID, book: Book):
    for i, b in enumerate(BOOKS):
        if b.id == id:
            BOOKS[i] = book
            return book
    raise HTTPException(status_code=404, detail="Book not found")