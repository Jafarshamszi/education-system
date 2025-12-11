'use client';

/**
 * Authentication Context for React
 * Provides authentication state management across the application
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi, UserProfile } from '@/lib/api/auth';

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (pin_code: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize authentication state
  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = localStorage.getItem('token');
        
        if (token) {
          // Verify token is still valid by getting fresh profile
          try {
            const profile = await authApi.getCurrentUser();
            setUser(profile);
          } catch {
            // Token invalid, clear auth state
            localStorage.removeItem('token');
            setUser(null);
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        localStorage.removeItem('token');
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (pin_code: string, password: string) => {
    try {
      const response = await authApi.login({ 
        username: pin_code, 
        password,
        frontend_type: 'admin'
      });
      
      // Store the token
      localStorage.setItem('token', response.access_token);
      if (response.refresh_token) {
        localStorage.setItem('refresh_token', response.refresh_token);
      }
      
      // Set the user profile
      const userProfile: UserProfile = {
        user_id: response.user_id,
        username: response.username,
        user_type: response.user_type,
        first_name: response.first_name,
        last_name: response.last_name,
        email: response.email,
        full_name: response.full_name
      };
      setUser(userProfile);
    } catch (error) {
      throw error; // Re-throw for component error handling
    }
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const profile = await authApi.getCurrentUser();
      setUser(profile);
    } catch (error) {
      logout(); // If refresh fails, logout
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Hook to use authentication context
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Higher-order component for protected routes
export function withAuth<P extends object>(WrappedComponent: React.ComponentType<P>) {
  return function AuthGuard(props: P) {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading...</p>
          </div>
        </div>
      );
    }

    if (!isAuthenticated) {
      // Redirect to login
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      return null;
    }

    return <WrappedComponent {...props} />;
  };
}