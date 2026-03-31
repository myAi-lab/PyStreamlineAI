from pydantic import BaseModel, Field


class WSClientMessage(BaseModel):
    type: str = Field(pattern="^(start|respond|ping)$")
    answer: str | None = None


class WSServerMessage(BaseModel):
    type: str
    payload: dict

