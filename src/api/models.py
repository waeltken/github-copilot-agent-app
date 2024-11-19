from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union


class RootModel(BaseModel):
    copilot_thread_id: str
    messages: List[Any]
