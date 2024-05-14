from typing import Optional
from pydantic import BaseModel

class SessionData(BaseModel):
    username: str

class TaskSchema(BaseModel):
    id: Optional[int] = None
    title: str
    completed: bool = False
    user_id: int

    class Config:
        orm_mode = True


class UserSchema(BaseModel):
    firebase_uid: str
    email: str
    username: str

class LoginSchema(BaseModel):
    firebase_uid: str