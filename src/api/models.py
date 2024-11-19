from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union


class RefInfo(BaseModel):
    name: str
    type: str


class Language(BaseModel):
    name: str
    percent: float


class RepositoryData(BaseModel):
    type: Optional[str] = None
    id: Optional[int] = None
    name: Optional[str] = None
    ownerLogin: Optional[str] = None
    ownerType: Optional[str] = None
    readmePath: Optional[str] = None
    description: Optional[str] = None
    commitOID: Optional[str] = None
    ref: Optional[str] = None
    refInfo: Optional[str] = None
    visibility: Optional[str] = None
    languages: Optional[List[Language]] = None


class CurrentUrlData(BaseModel):
    type: Optional[str] = None


class Metadata(BaseModel):
    display_name: str
    display_icon: str
    display_url: str


class CopilotReference(BaseModel):
    type: str
    data: Optional[Union[RepositoryData, CurrentUrlData]] = None
    id: str
    is_implicit: bool
    metadata: Metadata


class Message(BaseModel):
    role: str
    content: str
    copilot_references: List[CopilotReference]
    copilot_confirmations: Optional[Any] = None
    name: Optional[str] = None


class RootModel(BaseModel):
    copilot_thread_id: str
    messages: List[Message]
    stop: Optional[Any] = None
    top_p: float
    temperature: float
    max_tokens: int
    presence_penalty: float
    frequency_penalty: float
    response_format: Optional[Any] = None
    copilot_skills: Optional[Any] = None
    agent: str
    tools: Optional[Any] = None
    functions: Optional[Any] = None
    model: str
    call_next: Optional[Any] = None
