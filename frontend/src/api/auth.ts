import client from './client';
import type { ApiResponse, LoginResponse, User } from '../types';

export async function register(data: {
  username: string;
  email: string;
  password: string;
  role: 'teacher' | 'student';
}): Promise<ApiResponse<User>> {
  return client.post('/auth/register', data);
}

export async function login(data: {
  email: string;
  password: string;
}): Promise<ApiResponse<LoginResponse>> {
  return client.post('/auth/login', data);
}

export async function getMe(): Promise<ApiResponse<User>> {
  return client.get('/users/me');
}

export async function updateProfile(data: {
  nickname?: string;
  avatar_url?: string;
}): Promise<ApiResponse<User>> {
  return client.put('/users/me', data);
}

export async function changePassword(data: {
  old_password: string;
  new_password: string;
}): Promise<ApiResponse<void>> {
  return client.put('/users/me/password', data);
}
