from fastapi import FastAPI, HTTPException, Request
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from typing import List,Dict
from uuid import uuid4
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from operator import itemgetter
import psycopg2
from psycopg2.extras import RealDictCursor

# Initialize FastAPI app
app = FastAPI()

# Add session middleware with a secret key
app.add_middleware(SessionMiddleware, secret_key="")

# PostgreSQL connection settings
DB_CONFIG = {
    "host": "localhost",
    "dbname": "demo",  # Replace with your actual DB name
    "user": "postgres",  # Replace with your DB user
    "password": "1234",  # Replace with your DB password
    "port": "5432"
}

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

# Database utility functions
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

# Authenticate user
def authenticate_user(username: str, password: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    conn.close()
    return user and user["password"] == password

# Save chat history to the database (store both user and AI messages in the same row)
def save_chat_history(username: str, user_msg: str, ai_msg: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert user message and AI response
    cursor.execute(
        "INSERT INTO chat_history (username, user_msg, ai_msg) VALUES (%s, %s, %s)",
        (username, user_msg, ai_msg),
    )
    
    # # Ensure LIMIT is not negative; delete older messages only if more than 5 messages exist
    # cursor.execute("""
    #     DELETE FROM chat_history
    #     WHERE id IN (
    #         SELECT id FROM chat_history
    #         WHERE username = %s
    #         ORDER BY timestamp ASC
    #         LIMIT GREATEST(0, (SELECT COUNT(*) FROM chat_history WHERE username = %s) - 5)
    #     )
    # """, (username, username))

    conn.commit()
    conn.close()

# Get the last 5 chat history for a user
def get_chat_history(username: str) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_msg, ai_msg FROM chat_history WHERE username = %s ORDER BY timestamp DESC LIMIT 5",
        (username,)
    )
    history = cursor.fetchall()
    conn.close()
    return history[::-1]  # Reverse to show the oldest messages first

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the RAG-based chatbot API"}

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

    # Prepare input for the chain
    chain_input = {"question": chat_request.message}
    
    # Use the chain to get a response
    response_message = chain.invoke(chain_input)

    # Save chat history to the database (store both user and AI messages)
    save_chat_history(username, chat_request.message, response_message)

    # Retrieve the updated chat history (only last 5 messages)
    history = get_chat_history(username)

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
