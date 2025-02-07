from fastapi import FastAPI


app=FastAPI()


@app.get("/")
def root():
    return {"message":"Hello World"}


my_posts = [{"title": "Post 1","doc":"hello this is file 1"}, {"title": "Post 2","doc":"hello this is file 2"}]

def find(id:str):
    for i in my_posts:
        if i["title"]==id:
            return i["doc"]
    
    return "Nothing here"

@app.get("/posts/{id}")
def get_posts(id:str):
    return {"data":find(id)}


@app.post("/posts")
def post(title:str,doc:str):
    my_posts.append({"title":title,"doc":doc})
    return {"message":"Post added successfully"}