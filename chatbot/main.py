from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import List, Dict
from uuid import uuid4
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from operator import itemgetter
import os
import json

# Initialize FastAPI app
app = FastAPI()

# Add session middleware with a secret key
app.add_middleware(SessionMiddleware, secret_key="164bca8ca3e15c34036736330473fa990edfe9a40da0100b77a9ab255b0c9011")

# Initialize LangChain components
MODEL = "llama2"
model = Ollama(model=MODEL)  # Load LLM
embeddings = OllamaEmbeddings(model=MODEL)  # Load embeddings

# Path for Chroma vector store
vectorstore_path = r"D:\project\ragollama\chroma_db"
vectorstore = Chroma(persist_directory=vectorstore_path, embedding_function=embeddings)
retriever = vectorstore.as_retriever()  # Create retriever from vectorstore

# Prompt template
template = """
Answer the question based on the context below. If you cannot 
answer the question, reply "I do not know".

Context: {context}

Question: {question}
"""
prompt = PromptTemplate.from_template(template)

# Chain definition for RAG pipeline
chain = {
    "context": itemgetter("question") | retriever,
    "question": itemgetter("question"),
} | prompt | model

# Models for API requests
class UserCredentials(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str

# In-memory user database (can be replaced with a real DB)
users_db = {"user1": "password1", "user2": "password2"}

# Persistent storage for chat histories
def get_chat_history(username: str) -> List[str]:
    history_path = f"chat_histories/{username}.json"
    if os.path.exists(history_path):
        with open(history_path, 'r') as f:
            return json.load(f)
    return []

def save_chat_history(username: str, history: List[str]):
    # Keep only the last 10 messages (5 user and 5 AI messages)
    truncated_history = history[-10:]
    os.makedirs("chat_histories", exist_ok=True)
    history_path = f"chat_histories/{username}.json"
    with open(history_path, 'w') as f:
        json.dump(truncated_history, f)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the RAG-based chatbot API"}

# Authenticate user
def authenticate_user(username: str, password: str) -> bool:
    return users_db.get(username) == password

# Login endpoint
@app.post("/login")
def login(credentials: UserCredentials, request: Request):
    if not authenticate_user(credentials.username, credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    session_id = str(uuid4())  # Generate a unique session ID
    request.session["session_id"] = session_id
    request.session["username"] = credentials.username
    return {"message": "Login successful", "session_id": session_id}

# Chat endpoint using the RAG chain
@app.post("/chat")
def chat(chat_request: ChatRequest, request: Request):
    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="User not logged in")
    
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="No username found in session")

    # Retrieve chat history from persistent storage
    history = get_chat_history(username)

    # Prepare input for the chain
    chain_input = {"question": chat_request.message}

    # Use the chain to get a response
    response_message = chain.invoke(chain_input)

    # Update chat history
    history.append(f"User: {chat_request.message}")
    history.append(f"AI: {response_message}")
    
    # Save updated chat history (only last 10 messages)
    save_chat_history(username, history)

    return {"response": response_message, "chat_history": history}

# Chat history endpoint
@app.get("/history")
def get_history(request: Request):
    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="User not logged in")
    
    username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="No username found in session")

    history = get_chat_history(username)
    return {"chat_history": history}

# Logout endpoint
@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logout successful"}
