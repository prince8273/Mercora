import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * Authentication store using Zustand
 * Manages user authentication state, tokens, and user data
 */
export const useAuthStore = create(
  persist(
    (set, get) => ({
      // State
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      
      setToken: (token) => set({ token }),
      
      setAuth: (user, token) => set({ 
        user, 
        token, 
        isAuthenticated: true,
        error: null 
      }),
      
      setLoading: (isLoading) => set({ isLoading }),
      
      setError: (error) => set({ error }),
      
      clearAuth: () => set({ 
        user: null, 
        token: null, 
        isAuthenticated: false,
        error: null 
      }),

      // Getters
      getUser: () => get().user,
      getToken: () => get().token,
      isAuth: () => get().isAuthenticated,
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
