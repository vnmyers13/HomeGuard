/**
 * Auth store - zustand state management for authentication.
 * 
 * CP-10 Compliance: JWT tokens are NEVER stored in localStorage.
 * All auth state exists in memory only. On page refresh, users must re-authenticate.
 */

import { create } from 'zustand';
import { authApi, setTokens, clearTokens, getAccessToken } from '../lib/api';

export const useAuthStore = create((set, get) => ({
  // State
  user: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,

  // Register a new user
  register: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.register({ username, password });
      const data = response.data?.data;
      
      setTokens(data.access_token, data.refresh_token);
      
      set({
        user: {
          user_id: data.user_id,
          username: data.username,
          role: data.role,
        },
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  // Login with credentials
  login: async (username, password) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.login({ username, password });
      const data = response.data?.data;
      
      setTokens(data.access_token, data.refresh_token);
      
      set({
        user: {
          user_id: data.user_id,
          username: data.username,
          role: data.role,
        },
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  // Verify current session
  verify: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.verify();
      const data = response.data?.data;
      
      set({
        user: {
          user_id: data.user_id,
          username: data.username,
          role: data.role,
        },
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      clearTokens();
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null, // Silent fail - just not authenticated
      });
    }
  },

  // Logout
  logout: async () => {
    try {
      await authApi.logout();
    } finally {
      clearTokens();
      set({
        user: null,
        isAuthenticated: false,
        error: null,
      });
    }
  },

  // Change password
  changePassword: async (currentPassword, newPassword) => {
    set({ isLoading: true, error: null });
    try {
      await authApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      set({ isLoading: false, error: null });
      return { success: true };
    } catch (error) {
      const message = error.response?.data?.detail || 'Password change failed';
      set({ error: message, isLoading: false });
      throw error;
    }
  },

  // Clear error state
  clearError: () => set({ error: null }),
}));

export default useAuthStore;