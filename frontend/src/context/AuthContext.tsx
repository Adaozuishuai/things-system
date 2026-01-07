import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { login as apiLogin, register as apiRegister, setAuthToken, getMe } from '../api';

interface User {
  id?: string;
  username: string;
  email?: string;
  bio?: string;
  avatar?: string;
  preferences?: {
    theme?: 'light' | 'dark' | 'system';
    [key: string]: any;
  };
}

interface AuthContextType {
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
  applyTheme: (theme: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));

  const applyTheme = (theme: string) => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
  };

  const refreshUser = useCallback(async () => {
    if (!token) return;
    try {
      const userData = await getMe();
      setUser(userData);
      // Update localStorage username if changed
      if (userData.username) {
        localStorage.setItem('username', userData.username);
      }
      // Apply theme
      if (userData.preferences?.theme) {
        applyTheme(userData.preferences.theme);
      }
    } catch (error) {
      console.error("Failed to fetch user info", error);
    }
  }, [token]);


  useEffect(() => {
    if (token) {
      setAuthToken(token);
      
      // Try to get full user profile from backend
      refreshUser();

      // Fallback from localStorage for immediate display
      const storedUser = localStorage.getItem('username');
      if (storedUser && !user) {
        setUser({ username: storedUser });
      }
    } else {
      setAuthToken(null);
      setUser(null);
    }
  }, [token, refreshUser]);

  const login = async (username: string, password: string) => {
    try {
      const data = await apiLogin(username, password);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('username', username);
      setToken(data.access_token);
      // Initial minimal user
      setUser({ username });
      // Fetch full profile
      // refreshUser() will be triggered by token change effect
    } catch (error) {
      throw error;
    }
  };

  const register = async (username: string, password: string) => {
    try {
      const data = await apiRegister(username, password);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('username', username);
      setToken(data.access_token);
      setUser({ username });
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, refreshUser, applyTheme, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
