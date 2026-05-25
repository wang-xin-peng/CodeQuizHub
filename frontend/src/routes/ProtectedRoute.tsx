import { useEffect } from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

interface Props {
  allowedRoles?: string[];
}

export function ProtectedRoute({ allowedRoles }: Props) {
  const { user, token } = useAuthStore();

  // Ensure THIS tab's Zustand state matches its own sessionStorage on mount.
  // Each browser tab has independent sessionStorage, so this prevents any
  // cross-tab interference.
  useEffect(() => {
    const current = useAuthStore.getState();
    const storedToken = sessionStorage.getItem('token');
    const storedUser = sessionStorage.getItem('user');

    if (storedToken && storedUser) {
      const parsed = JSON.parse(storedUser);
      if (current.user?.id !== parsed.id || current.token !== storedToken) {
        current.loadUser();
      }
    }
  }, []);

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
