import { useState, useCallback } from 'react';
import { User } from '../types/types';
import { withBase } from '../services/config';

export function getAuthHeaders() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;
  return token ? { Authorization: `Bearer ${token}` } : undefined;
}

export default function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loginError, setLoginError] = useState<string>('');

  const login = useCallback(async (username: string, password: string) => {
    try {
      const response = await fetch(withBase('/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('authToken', data.access_token);
        setCurrentUser(data.user);
        setIsAuthenticated(true);
        setLoginError('');
        return true;
      } else {
        const errorData = await response.json();
        setLoginError(errorData.detail || 'Login error');
        return false;
      }
    } catch (e) {
      setLoginError('Network error');
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('authToken');
    setIsAuthenticated(false);
    setCurrentUser(null);
  }, []);

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      setIsLoading(false);
      return;
    }
    try {
      const response = await fetch(withBase('/auth/me'), {
        headers: getAuthHeaders(),
      });
      if (response.ok) {
        const user = await response.json();
        setCurrentUser(user);
        setIsAuthenticated(true);
      } else {
        localStorage.removeItem('authToken');
      }
    } catch {
      localStorage.removeItem('authToken');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    isAuthenticated,
    currentUser,
    isLoading,
    loginError,
    login,
    logout,
    checkAuth,
    getAuthHeaders,
  };
}
