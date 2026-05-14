from datetime import datetime

from pydantic import BaseModel, Field


class AssignmentCreateRequest(BaseModel):
    course_id: str
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    start_time: datetime
    end_time: datetime
    problem_ids: list[str] = Field(..., min_length=1)
    score_weights: list[int] | None = None


class AssignmentUpdateRequest(BaseModel):
    title: str | None = Field(None, max_length=300)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: str | None = None


class AssignmentResponse(BaseModel):
    id: str
    course_id: str
    title: str
    description: str | None = None
    start_time: str
    end_time: str
    status: str
    created_at: str

    model_config = {"from_attributes": True}
