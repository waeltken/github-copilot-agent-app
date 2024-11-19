from pydantic import BaseModel
from typing import List, Any


class RootModel(BaseModel):
    copilot_thread_id: str
    messages: List[Any]
