import axios from 'axios';

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: inject token from sessionStorage (per-tab)
client.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('token');
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
        // Clear this tab's sessionStorage only — other tabs are unaffected
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('user');
        sessionStorage.removeItem('active_account_id');
        // Also clean up the accounts list in shared localStorage so the
        // invalidated account doesn't reappear on next load
        localStorage.removeItem('auth_accounts');
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
