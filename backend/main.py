from fastapi import FastAPI, Depends, HTTPException, Response, Cookie, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import firebase_admin
from firebase_admin import credentials, auth
from pydantic import BaseModel
from fastapi import FastAPI, Response, Depends, HTTPException
from uuid import UUID, uuid4

from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.session_verifier import SessionVerifier
from database import get_db, engine, Base
from models import User, Task
from crud import *
from schemas import *

app = FastAPI()

# Initialize Firebase Admin
cred_path = credentials.Certificate('todo-gita-firebase-adminsdk-xl91z-cb5dfed5d0.json')
firebase_admin.initialize_app(cred_path)

Base.metadata.create_all(bind=engine)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust as per your front-end URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

def set_session_cookie(response: Response, user_id: str):
    response.set_cookie(key="user_id", value=user_id, httponly=True, max_age=1800)

def get_current_user(response: Response, credential: HTTPAuthorizationCredentials = Depends(security)):
    token = credential.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        set_session_cookie(response, uid)
        return uid
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

async def validate_session_cookie(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user_id

# API endpoints
@app.post("/register", response_model=UserSchema)
def register_user(user_data: UserSchema, db: Session = Depends(get_db)):
    return create_user(db, user_data)

@app.post("/login", response_model=UserSchema)
def login_user(login_data: LoginSchema, db: Session = Depends(get_db)):
    return authenticate_user(db, login_data)

@app.post("/tasks", response_model=TaskSchema)
def create_task_endpoint(task_data: TaskSchema, db: Session = Depends(get_db)):
    return create_task(db, task_data)

@app.get("/tasks", response_model=list[TaskSchema])
def read_tasks_endpoint(db: Session = Depends(get_db)):
    return get_tasks(db)

@app.get("/tasks/{task_id}", response_model=TaskSchema)
def read_task_endpoint(task_id: int, db: Session = Depends(get_db)):
    return get_task(db, task_id)

@app.put("/tasks/{task_id}", response_model=TaskSchema)
def update_task_endpoint(task_id: int, task_data: TaskSchema, db: Session = Depends(get_db)):
    return update_task(db, task_id, task_data)

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task_endpoint(task_id: int, db: Session = Depends(get_db)):
    delete_task(db, task_id)

@app.get("/protected-route")
def protected_route(user_id: str = Depends(validate_session_cookie)):
    return {"message": "You are authorized to access this route", "user_id": user_id}



cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="user_session",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",  # Ensure to replace with a secure secret key in production
    cookie_params=cookie_params,
)

backend = InMemoryBackend[UUID, SessionData]()

class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self, *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: HTTPException
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True

verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)

@app.post("/create_session/{name}")
async def create_session(name: str, response: Response):
    session = uuid4()
    data = SessionData(username=name)
    await backend.create(session, data)
    cookie.attach_to_response(response, session)
    return f"created session for {name}"

@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data

@app.post("/delete_session")
async def del_session(response: Response, session_id: UUID = Depends(cookie)):
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    return "deleted session"

