from typing import List, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None
    history: Optional[List[ChatMessage]] = None
    model: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    model: str