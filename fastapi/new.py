from fastapi import FastAPI,Path

app = FastAPI()

students={
    1: {
        "name": "NV",
        "age": 15,
        "class": "10"
    }
}

@app.get("/")
def index():
    return {"name": "first"}

@app.get("/get-student/{student_id}")
def get_student(student_id: int = Path(description="The ID of the student you want to view",gt=0)):
    return students[student_id]

@app.post("/create-student/{student_id}")
def create_student(student_id: int, name: str, age: int, class_: str):
    if student_id in students:
        return {"Error": "Student already exists"}
    students[student_id] = {"name": name, "age": age, "class": class_}
    return students[student_id]
