import client from './client';
import type { ApiResponse, PaginatedData, Problem } from '../types';

export async function createProblem(data: {
  title: string;
  description: string;
  difficulty: string;
  time_limit: number;
  memory_limit: number;
  tags: string[];
  compare_mode: string;
  signatures: Array<{
    language: string;
    function_name: string;
    parameters: Array<{ name: string; type: string; description: string }>;
    return_type: string;
    code_template: string;
    prelude_code?: string;
    driver_template?: string;
  }>;
  test_cases: Array<{
    input_params: Record<string, unknown>;
    expected_output: unknown;
    is_public: boolean;
    description?: string;
  }>;
}): Promise<ApiResponse<Problem>> {
  return client.post('/problems', data);
}

export async function getProblems(params?: {
  page?: number;
  page_size?: number;
  difficulty?: string;
  language?: string;
  tag?: string;
}): Promise<ApiResponse<PaginatedData<Problem>>> {
  return client.get('/problems', { params });
}

export async function getProblem(id: string): Promise<ApiResponse<Problem>> {
  return client.get(`/problems/${id}`);
}

export async function updateProblem(
  id: string,
  data: Partial<Problem>
): Promise<ApiResponse<Problem>> {
  return client.put(`/problems/${id}`, data);
}

export async function deleteProblem(id: string): Promise<ApiResponse<void>> {
  return client.delete(`/problems/${id}`);
}

export async function getSignature(
  problemId: string,
  language: string
): Promise<ApiResponse<{ code_template: string; prelude_code?: string }>> {
  return client.get(`/problems/${problemId}/signatures/${language}`);
}

export async function runCustomCode(
  problemId: string,
  data: { language: string; code: string; assignment_id: string; custom_input: Record<string, unknown> }
): Promise<ApiResponse<{ output: string; error: string | null }>> {
  return client.post(`/problems/${problemId}/run-custom`, data);
}
