import client from './client';
import type { ApiResponse, Assignment, PaginatedData } from '../types';

export async function createAssignment(data: {
  course_id: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  problem_ids: string[];
  score_weights?: number[];
}): Promise<ApiResponse<Assignment>> {
  return client.post('/assignments', data);
}

export async function getAssignment(id: string): Promise<ApiResponse<Assignment>> {
  return client.get(`/assignments/${id}`);
}

export async function updateAssignment(
  id: string,
  data: Partial<Assignment> & { problem_ids?: string[] }
): Promise<ApiResponse<Assignment>> {
  return client.put(`/assignments/${id}`, data);
}

export async function getCourseAssignments(
  courseId: string,
  params?: { page?: number; page_size?: number }
): Promise<ApiResponse<PaginatedData<Assignment>>> {
  return client.get(`/assignments/course/${courseId}`, { params });
}

export async function deleteAssignment(id: string): Promise<ApiResponse<void>> {
  return client.delete(`/assignments/${id}`);
}
