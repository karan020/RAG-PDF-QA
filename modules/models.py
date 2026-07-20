from datetime import datetime
from typing import Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls,v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls,field_schema):
        field_schema.update(type="string")

    
class Conversation(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    chat_id: str
    question: str
    answer: str
    sources: Optional[List[Dict]] = []
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True


class Chat(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    name: str
    pdf_filename: str
    pdf_path: str
    conversation_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True


class User(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    username: str
    email: Optional[str] = None
    chat_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        populate_by_name = True


class UserCreatedRequest(BaseModel):
    username: str
    email: Optional[str] = None


class ChatCreateRequest(BaseModel):
    user_id: str
    name: str
    pdf_filename: str


class ChatRenameRequest(BaseModel):
    chat_id: str
    new_name: str


class ConversationRequest(BaseModel):
    chat_id: str
    question: str
    top_k: Optional[int] = 5


class ChatResponse(BaseModel):
    id: str
    name: str
    pdf_filename: str
    conversation_count: str
    created_at: datetime
    updated_at: datetime


class ConversationResponse(BaseModel):
    id: str
    question: str
    answer: str
    sources: List[Dict]
    created_at: datetime


__all__ = [
    "UserCreatedRequest",
    "ChatCreateRequest",
    "ChatRenameRequest",
    "ConversationRequest",
    "ChatResponse",
    "ConversationResponse",
    "User",
    "Chat",
    "Conversation",
]