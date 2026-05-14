import client from './client';
import type { ApiResponse, Course, PaginatedData } from '../types';

export async function createCourse(data: {
  name: string;
  description?: string;
  languages: string[];
}): Promise<ApiResponse<Course>> {
  return client.post('/courses', data);
}

export async function getCourses(params?: {
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<PaginatedData<Course>>> {
  return client.get('/courses', { params });
}

export async function getCourse(id: string): Promise<ApiResponse<Course>> {
  return client.get(`/courses/${id}`);
}

export async function updateCourse(
  id: string,
  data: { name?: string; description?: string; status?: string }
): Promise<ApiResponse<Course>> {
  return client.put(`/courses/${id}`, data);
}

export async function deleteCourse(id: string): Promise<ApiResponse<void>> {
  return client.delete(`/courses/${id}`);
}

export async function joinCourse(invite_code: string): Promise<ApiResponse<{ course_id: string; course_name: string }>> {
  return client.post('/courses/join', { invite_code });
}

export async function leaveCourse(courseId: string): Promise<ApiResponse<void>> {
  return client.delete(`/courses/${courseId}/leave`);
}

export async function getCourseStudents(
  courseId: string,
  params?: { page?: number; page_size?: number }
): Promise<ApiResponse<PaginatedData<{ id: string; username: string; email: string; nickname?: string }>>> {
  return client.get(`/courses/${courseId}/students`, { params });
}

export async function removeStudent(courseId: string, studentId: string): Promise<ApiResponse<void>> {
  return client.delete(`/courses/${courseId}/students/${studentId}`);
}
