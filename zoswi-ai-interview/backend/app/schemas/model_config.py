from pydantic import BaseModel


class ModelConfigResponse(BaseModel):
    provider: str
    default_model: str
    max_retries: int
    timeout_seconds: float
    interview_max_turns: int

