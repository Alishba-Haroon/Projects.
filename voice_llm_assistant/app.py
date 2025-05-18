from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from jose import JWTError, jwt
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import asyncio
import uvicorn

# HuggingFace and Chroma imports
from sentence_transformers import SentenceTransformer
import chromadb

# SECRET for JWT
SECRET_KEY = "Enter_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

app = FastAPI()

# In-memory "databases"
fake_users_db = {
    "user1": {
        "username": "user1",
        "hashed_password": "password"
    }
}

sessions_memory: Dict[str, Dict[str, Any]] = {}

# Initialize embedding model and vector db
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.Client()
collection = client.get_or_create_collection("kb")

# -------------------
# Models
# -------------------

class User(BaseModel):
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    question: str

class Task(BaseModel):
    title: str
    when: str
    description: Optional[str] = None

class TaskAction(BaseModel):
    action: str
    task: Optional[Task] = None

# -------------------
# Auth Helpers
# -------------------

def fake_hash_password(password: str):
    return "fakehashed" + password

def verify_password(plain_password, hashed_password):
    return fake_hash_password(plain_password) == hashed_password

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(OAuth2PasswordRequestForm)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.username, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = fake_users_db.get(username)
    if user is None:
        raise credentials_exception
    return user

# -------------------
# Helper: Vector Search (retrieve_docs)
# -------------------

def retrieve_docs(query: str):
    embedding = embedding_model.encode(query).tolist()
    results = collection.query(query_embeddings=[embedding], n_results=3)
    docs = []
    for doc in results['documents'][0]:
        idx = results['documents'][0].index(doc)
        meta = results['metadatas'][0][idx]
        docs.append({
            "content": doc,
            "source": meta.get("source", "unknown"),
            "metadata": meta
        })
    return {"docs": docs, "query": query}

# -------------------
# Helper: Self-Grading
# -------------------

async def self_grade(question: str, docs: List[Dict]):
    # Dummy grading: Check if docs contain the question keywords
    content_concat = " ".join([d['content'] for d in docs]).lower()
    q_words = set(question.lower().split())
    match_count = sum(1 for w in q_words if w in content_concat)
    relevance = min(1.0, match_count / len(q_words))
    coverage = relevance  # Simplify, use same score
    return {"relevance": relevance, "coverage": coverage}

# -------------------
# Helper: Task Manager (in-memory)
# -------------------

def manage_tasks(session_id: str, action: str, task: Optional[Task] = None):
    session = sessions_memory.setdefault(session_id, {})
    tasks = session.setdefault("tasks", [])
    if action == "add" and task:
        tasks.append(task.dict())
        return {"message": f"Task '{task.title}' added."}
    elif action == "list":
        return {"tasks": tasks}
    else:
        return {"error": "Invalid action"}

# -------------------
# Self-Reflection: Feedback management
# -------------------

def update_feedback(session_id: str, feedback: str):
    session = sessions_memory.setdefault(session_id, {})
    score = session.get("feedback_score", 0.0)
    decay = 0.5
    # Apply decay before updating
    score = score * decay
    if feedback == "/good_answer":
        score += 1
    elif feedback == "/bad_answer":
        score -= 1
    session["feedback_score"] = score
    return score

def get_feedback_prompt_modifier(score: float) -> str:
    if score < 0:
        return "Be more concise and cite sources explicitly."
    else:
        return "Maintain current style, user is satisfied."

# -------------------
# Routes
# -------------------

@app.post("/register")
async def register(user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username taken")
    fake_users_db[user.username] = {"username": user.username, "hashed_password": fake_hash_password("password")}
    return {"msg": "User registered"}

@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user['username']}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/concierge/chat")
async def chat(request: ChatRequest, token: str = Depends(OAuth2PasswordRequestForm)):
    user = await get_current_user(token)
    session_id = user["username"]
    question = request.question

    # Check for feedback commands
    if question in ["/good_answer", "/bad_answer"]:
        score = update_feedback(session_id, question)
        return {"feedback_score": score}

    # Self reflection prompt adjustment
    feedback_score = sessions_memory.get(session_id, {}).get("feedback_score", 0.0)
    system_modifier = get_feedback_prompt_modifier(feedback_score)

    # Retrieve docs
    result = retrieve_docs(question)
    grading = await self_grade(question, result['docs'])

    if grading['relevance'] < 0.6 or grading['coverage'] < 0.6:
        # Try refined query (simplified)
        refined_query = " ".join(question.split()[::-1])
        result = retrieve_docs(refined_query)
        grading = await self_grade(question, result['docs'])
        if grading['relevance'] < 0.6 or grading['coverage'] < 0.6:
            return {"response": "My knowledge base does not cover that topic."}

    # Build response with citations
    answer = "Answer based on docs:\n"
    for doc in result['docs']:
        answer += f"{doc['content']} [Source: {doc['source']}]\n"

    return {"response": answer, "grading": grading, "modifier": system_modifier}

@app.post("/concierge/tasks")
async def tasks(action: TaskAction, token: str = Depends(OAuth2PasswordRequestForm)):
    user = await get_current_user(token)
    session_id = user["username"]

    if action.action == "add" and action.task:
        result = manage_tasks(session_id, "add", action.task)
        return result
    elif action.action == "list":
        return manage_tasks(session_id, "list")
    else:
        raise HTTPException(status_code=400, detail="Invalid task action")

# Run app
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
