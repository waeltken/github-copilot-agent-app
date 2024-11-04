from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union


class RefInfo(BaseModel):
    name: str
    type: str


class Language(BaseModel):
    name: str
    percent: float


class RepositoryData(BaseModel):
    type: str
    id: int
    name: str
    ownerLogin: str
    ownerType: str
    readmePath: str
    description: str
    commitOID: str
    ref: str
    refInfo: RefInfo
    visibility: str
    languages: List[Language]


class CurrentUrlData(BaseModel):
    type: str


class Metadata(BaseModel):
    display_name: str
    display_icon: str
    display_url: str


class CopilotReference(BaseModel):
    type: str
    data: Union[RepositoryData, CurrentUrlData]
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
