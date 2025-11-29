import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { User } from '@/packages/types'
import apiClient from '@/packages/api/client'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isGuest: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, firstName: string, lastName: string) => Promise<void>
  loginAsGuest: () => void
  logout: () => void
  setUser: (user: User) => void
  setTokens: (access: string, refresh: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isGuest: false,

      login: async (email: string, password: string) => {
        try {
          // Validate inputs
          if (!email || !email.trim()) {
            throw new Error('Email is required')
          }
          if (!password) {
            throw new Error('Password is required')
          }
          
          const normalizedEmail = email.trim().toLowerCase()
          const response = await apiClient.post('/auth/token/', { email: normalizedEmail, password })
          
          // Validate response has tokens
          if (!response.data || !response.data.access || !response.data.refresh) {
            throw new Error('Invalid response from server. Please try again.')
          }
          
          const { access, refresh } = response.data
          
          // Set tokens before making authenticated request
          apiClient.setAuthToken(access)
          apiClient.setRefreshToken(refresh)
          
          try {
            const userResponse = await apiClient.get('/auth/users/me/')
            const user = userResponse.data
            
            set({
              user,
              accessToken: access,
              refreshToken: refresh,
              isAuthenticated: true,
            })
          } catch (userError: any) {
            // If getting user fails, clear tokens and rethrow
            apiClient.clearAuth()
            console.error('Failed to get user after login:', userError)
            throw new Error('Login successful but failed to load user data. Please try again.')
          }
        } catch (error: any) {
          // Clear any partial auth state on error
          apiClient.clearAuth()
          console.error('Login error:', error?.response?.data || error?.message || error)
          
          // Extract error message from various possible response formats
          const errorMessage = error.message || 
                              error.response?.data?.detail || 
                              error.response?.data?.non_field_errors?.[0] ||
                              error.response?.data?.error?.message ||
                              error.response?.data?.error?.details?.detail ||
                              'Login failed. Please check your credentials.'
          throw new Error(errorMessage)
        }
      },

      signup: async (email: string, password: string, firstName: string, lastName: string) => {
        try {
          const normalizedEmail = email.trim().toLowerCase()

          const response = await apiClient.post('/auth/users/register/', {
            email: normalizedEmail,
            password,
            password_confirm: password,
            first_name: firstName,
            last_name: lastName,
            role: 'CUSTOMER',
          })
          
          // Handle response format - could be { user, tokens } or direct user object
          const user = response.data.user || response.data
          const tokens = response.data.tokens || { 
            access: response.data.access, 
            refresh: response.data.refresh 
          }
          
          if (!tokens.access || !tokens.refresh) {
            throw new Error('Invalid response from server. Tokens not received.')
          }
          
          apiClient.setAuthToken(tokens.access)
          apiClient.setRefreshToken(tokens.refresh)
          
          set({
            user,
            accessToken: tokens.access,
            refreshToken: tokens.refresh,
            isAuthenticated: true,
            isGuest: false,
          })
        } catch (error: any) {
          // Clear any partial auth state on error
          apiClient.clearAuth()
          
          const errorMessage = error.response?.data?.email?.[0] ||
                              error.response?.data?.password?.[0] ||
                              error.response?.data?.password_confirm?.[0] ||
                              error.response?.data?.non_field_errors?.[0] ||
                              error.response?.data?.error ||
                              error.response?.data?.detail ||
                              (typeof error.response?.data === 'string' ? error.response.data : null) ||
                              error.message ||
                              'Signup failed. Please check your information.'
          throw new Error(errorMessage)
        }
      },

      loginAsGuest: () => {
        // Clear any existing auth tokens and mark session as guest
        apiClient.clearAuth()
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isGuest: true,
        })
      },

      logout: () => {
        apiClient.clearAuth()
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isGuest: false,
        })
      },

      setUser: (user: User) => {
        set({ user, isAuthenticated: true })
      },
      
      setTokens: (access: string, refresh: string) => {
        apiClient.setAuthToken(access)
        apiClient.setRefreshToken(refresh)
        set({ accessToken: access, refreshToken: refresh })
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

