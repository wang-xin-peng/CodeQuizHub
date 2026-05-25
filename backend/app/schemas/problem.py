from typing import Any, Literal

from pydantic import BaseModel, Field


class ParameterDef(BaseModel):
    name: str
    type: str
    description: str = ""


class SignatureCreateRequest(BaseModel):
    language: str = Field(..., min_length=1, max_length=20)
    function_name: str = Field(..., max_length=100)
    parameters: list[ParameterDef]
    return_type: str = Field(..., max_length=100)
    code_template: str
    prelude_code: str | None = None
    driver_template: str | None = None


class TestCaseCreateRequest(BaseModel):
    input_params: dict[str, Any]
    expected_output: Any
    is_public: bool = False
    description: str | None = None


class ProblemCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str = Field(..., min_length=1)
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    time_limit: int = Field(default=1000, ge=100, le=30000)
    memory_limit: int = Field(default=256, ge=16, le=1024)
    tags: list[str] = Field(default_factory=list)
    compare_mode: Literal["exact", "unordered", "float", "custom"] = "exact"
    signatures: list[SignatureCreateRequest] = Field(..., min_length=1)
    test_cases: list[TestCaseCreateRequest] = Field(..., min_length=1)


class ProblemUpdateRequest(BaseModel):
    title: str | None = Field(None, max_length=300)
    description: str | None = None
    difficulty: Literal["easy", "medium", "hard"] | None = None
    time_limit: int | None = Field(None, ge=100, le=30000)
    memory_limit: int | None = Field(None, ge=16, le=1024)
    tags: list[str] | None = None
    compare_mode: Literal["exact", "unordered", "float", "custom"] | None = None
    signatures: list[SignatureCreateRequest] | None = None
    test_cases: list[TestCaseCreateRequest] | None = None


class SignatureResponse(BaseModel):
    id: str
    language: str
    function_name: str
    parameters_json: list[dict]
    return_type: str
    code_template: str
    prelude_code: str | None = None

    model_config = {"from_attributes": True}


class TestCaseResponse(BaseModel):
    id: str
    input_params_json: dict
    expected_output_json: Any
    is_public: bool
    order: int
    description: str | None = None

    model_config = {"from_attributes": True}


class ProblemResponse(BaseModel):
    id: str
    title: str
    description: str
    difficulty: str
    time_limit: int
    memory_limit: int
    tags: list[str]
    compare_mode: str
    teacher_id: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class ProblemDetailResponse(ProblemResponse):
    signatures: list[SignatureResponse] = []
    test_cases: list[TestCaseResponse] = []
