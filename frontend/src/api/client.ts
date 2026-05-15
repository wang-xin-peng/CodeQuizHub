import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: inject token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle errors
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      const { status, data } = error.response;

      if (status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }

      // Extract error message: support both custom format (code/message) and FastAPI 422 (detail[])
      let message = data?.message || '请求失败';
      if (!data?.message && data?.detail && Array.isArray(data.detail)) {
        message = data.detail.map((d: { msg: string }) => d.msg.replace(/^Value error,\s*/, '')).join('; ');
      }

      return Promise.reject({
        code: data?.code || 'UNKNOWN_ERROR',
        message,
        status,
      });
    }

    return Promise.reject({
      code: 'NETWORK_ERROR',
      message: '网络错误，请检查网络连接',
      status: 0,
    });
  }
);

export default client;
