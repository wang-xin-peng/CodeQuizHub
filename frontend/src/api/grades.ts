import client from './client';
import type { ApiResponse } from '../types';

export async function getCourseGrades(courseId: string): Promise<ApiResponse<{
  course_id: string;
  course_name: string;
  grades: Array<{
    student_id: string;
    username: string;
    nickname?: string;
    assignments: Record<string, { title: string; score: number }>;
    total_score: number;
  }>;
  statistics: {
    average: number;
    max: number;
    min: number;
    student_count: number;
  };
}>> {
  return client.get(`/grades/courses/${courseId}`);
}

export function getExportUrl(courseId: string, format: 'xlsx' | 'csv' = 'xlsx'): string {
  return `/api/grades/courses/${courseId}/export?format=${format}`;
}
