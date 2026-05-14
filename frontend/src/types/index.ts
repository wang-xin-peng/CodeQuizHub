export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'teacher' | 'student';
  nickname?: string;
  avatar_url?: string;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Course {
  id: string;
  name: string;
  description?: string;
  languages: string[];
  invite_code: string;
  status: string;
  teacher_id: string;
  created_at: string;
  updated_at: string;
}

export interface ParameterDef {
  name: string;
  type: string;
  description: string;
}

export interface FunctionSignature {
  id: string;
  language: string;
  function_name: string;
  parameters_json: ParameterDef[];
  return_type: string;
  code_template: string;
  prelude_code?: string;
}

export interface TestCase {
  id: string;
  input_params_json: Record<string, unknown>;
  expected_output_json: unknown;
  is_public: boolean;
  order: number;
  description?: string;
}

export interface Problem {
  id: string;
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  time_limit: number;
  memory_limit: number;
  tags: string[];
  compare_mode: string;
  teacher_id: string;
  created_at: string;
  updated_at: string;
  signatures?: FunctionSignature[];
  test_cases?: TestCase[];
}

export interface Assignment {
  id: string;
  course_id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  status: string;
  created_at: string;
  problems?: { problem_id: string; score_weight: number; order: number }[];
}

export interface Submission {
  id: string;
  student_id: string;
  problem_id: string;
  assignment_id: string;
  language: string;
  status: string;
  score: number;
  time_used?: number;
  memory_used?: number;
  error_message?: string;
  submitted_at: string;
}

export interface TestResultItem {
  test_case_order: number;
  status: string;
  is_public: boolean;
  input?: Record<string, unknown>;
  expected?: unknown;
  actual?: unknown;
  time_used?: number;
  memory_used?: number;
}

export interface SubmissionDetail extends Submission {
  results: TestResultItem[];
}

export interface ApiResponse<T = unknown> {
  code: number | string;
  data: T;
  message: string;
}

export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}
