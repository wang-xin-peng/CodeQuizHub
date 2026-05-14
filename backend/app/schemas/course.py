from pydantic import BaseModel, Field


class CourseCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    languages: list[str] = Field(..., min_length=1)


class CourseUpdateRequest(BaseModel):
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    status: str | None = None


class CourseResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    languages: list[str]
    invite_code: str
    status: str
    teacher_id: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class JoinCourseRequest(BaseModel):
    invite_code: str = Field(..., min_length=1, max_length=8)
