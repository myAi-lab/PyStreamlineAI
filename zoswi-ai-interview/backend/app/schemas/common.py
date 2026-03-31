from datetime import datetime
from typing import Generic, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    success: Literal[False] = False
    error: ErrorDetail
    request_id: str | None = None


class SuccessResponse(BaseModel, Generic[T]):
    success: Literal[True] = True
    data: T
    request_id: str | None = None


class TimestampedSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    created_at: datetime
    updated_at: datetime | None = None


class UUIDModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
