from app.schemas.response import success_response, paginated_response
from app.schemas.user import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    LoginResponse,
    UpdateProfileRequest,
    ChangePasswordRequest,
)
from app.schemas.course import (
    CourseCreateRequest,
    CourseUpdateRequest,
    CourseResponse,
    JoinCourseRequest,
)
from app.schemas.problem import (
    ProblemCreateRequest,
    ProblemUpdateRequest,
    ProblemResponse,
    ProblemDetailResponse,
    SignatureCreateRequest,
    SignatureResponse,
    TestCaseCreateRequest,
    TestCaseResponse,
)
from app.schemas.assignment import (
    AssignmentCreateRequest,
    AssignmentUpdateRequest,
    AssignmentResponse,
)
from app.schemas.submission import (
    SubmitCodeRequest,
    RunCodeRequest,
    RunCustomRequest,
    SubmissionResponse,
    SubmissionDetailResponse,
)

__all__ = [
    "success_response",
    "paginated_response",
    "RegisterRequest",
    "LoginRequest",
    "UserResponse",
    "LoginResponse",
    "UpdateProfileRequest",
    "ChangePasswordRequest",
    "CourseCreateRequest",
    "CourseUpdateRequest",
    "CourseResponse",
    "JoinCourseRequest",
    "ProblemCreateRequest",
    "ProblemUpdateRequest",
    "ProblemResponse",
    "ProblemDetailResponse",
    "SignatureCreateRequest",
    "SignatureResponse",
    "TestCaseCreateRequest",
    "TestCaseResponse",
    "AssignmentCreateRequest",
    "AssignmentUpdateRequest",
    "AssignmentResponse",
    "SubmitCodeRequest",
    "RunCodeRequest",
    "RunCustomRequest",
    "SubmissionResponse",
    "SubmissionDetailResponse",
]
