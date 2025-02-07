from fastapi import FastAPI
from enum import Enum
app=FastAPI()


@app.get("/")
def get():
    return {"hello":"world"}

@app.post("/")
def post():
    return {"message from post"}

@app.put("/")
def put():
    return {"message from put"}

@app.get("/items")
def get_items():
    return {"items": "this is items"}

@app.get("/item/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}

class food_enum(str, Enum):
    fruit="apple"
    vegetable="carrot"
    chocolate="twix"
    dairy="milk"
    chips="lays"

@app.get("/food/{food_name}")
async def get_food(food_name: food_enum):
    if food_name==food_enum.fruit:
        return {"food_name": food_name, "message": "this is a fruit"}
    elif food_name.value==food_enum.vegetable.value:
        return {"food_name": food_name, "message": "this is a vegetable"}
    else:
        return {"food_name": food_name, "message": "this is not a fruit or vegetable"}