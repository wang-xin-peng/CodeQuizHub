import client from './client';
import type { ApiResponse, PaginatedData, Submission, SubmissionDetail } from '../types';

export async function submitCode(data: {
  assignment_id: string;
  problem_id: string;
  language: string;
  code: string;
}): Promise<ApiResponse<{ submission_id: string; status: string }>> {
  return client.post('/submissions', data);
}

export async function getSubmission(id: string): Promise<ApiResponse<SubmissionDetail>> {
  return client.get(`/submissions/${id}`);
}

export async function getAssignmentSubmissions(
  assignmentId: string,
  params?: { page?: number; page_size?: number }
): Promise<ApiResponse<PaginatedData<Submission>>> {
  return client.get(`/submissions/assignment/${assignmentId}`, { params });
}

export async function runCode(
  problemId: string,
  data: { language: string; code: string; assignment_id: string }
): Promise<ApiResponse<{ results: Array<{ test_case_order: number; status: string; input: unknown; expected: unknown; actual: unknown; time_used: number; memory_used: number }>; compile_error: string | null }>> {
  return client.post(`/problems/${problemId}/run`, data);
}

export async function saveDraft(data: {
  problem_id: string;
  assignment_id: string;
  language: string;
  code: string;
}): Promise<ApiResponse<void>> {
  return client.put('/submissions/drafts', null, { params: data });
}

export async function getDraft(
  problemId: string,
  params: { assignment_id: string; language: string }
): Promise<ApiResponse<{ code: string | null }>> {
  return client.get(`/submissions/drafts/${problemId}`, { params });
}
