from pydantic import BaseModel, Field


class SubmitCodeRequest(BaseModel):
    assignment_id: str
    problem_id: str
    language: str = Field(..., max_length=20)
    code: str = Field(..., min_length=1)


class RunCodeRequest(BaseModel):
    language: str = Field(..., max_length=20)
    code: str = Field(..., min_length=1)
    assignment_id: str


class RunCustomRequest(BaseModel):
    language: str = Field(..., max_length=20)
    code: str = Field(..., min_length=1)
    assignment_id: str
    custom_input: dict


class SubmissionResponse(BaseModel):
    id: str
    student_id: str
    problem_id: str
    assignment_id: str
    language: str
    status: str
    score: int
    time_used: int | None = None
    memory_used: int | None = None
    error_message: str | None = None
    submitted_at: str

    model_config = {"from_attributes": True}


class TestResultItem(BaseModel):
    test_case_order: int
    status: str
    is_public: bool
    input: dict | None = None
    expected: object | None = None
    actual: object | None = None
    time_used: int | None = None
    memory_used: int | None = None


class SubmissionDetailResponse(SubmissionResponse):
    results: list[TestResultItem] = []
