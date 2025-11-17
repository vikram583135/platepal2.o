import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { User } from '@/packages/types'
import apiClient from '@/packages/api/client'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, firstName: string, lastName: string) => Promise<void>
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

      login: async (email: string, password: string) => {
        try {
          const normalizedEmail = email.trim().toLowerCase()
          const response = await apiClient.post('/auth/token/', { email: normalizedEmail, password })
          const { access, refresh } = response.data
          
          apiClient.setAuthToken(access)
          apiClient.setRefreshToken(refresh)
          
          const userResponse = await apiClient.get('/auth/users/me/')
          const user = userResponse.data
          
          set({
            user,
            accessToken: access,
            refreshToken: refresh,
            isAuthenticated: true,
          })
        } catch (error: any) {
          console.error('Login error:', error?.response?.data || error?.message || error)
          const errorMessage = error.response?.data?.detail || 
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
          
          const { user, tokens } = response.data
          apiClient.setAuthToken(tokens.access)
          apiClient.setRefreshToken(tokens.refresh)
          
          set({
            user,
            accessToken: tokens.access,
            refreshToken: tokens.refresh,
            isAuthenticated: true,
          })
        } catch (error: any) {
          const errorMessage = error.response?.data?.email?.[0] ||
                              error.response?.data?.password?.[0] ||
                              error.response?.data?.non_field_errors?.[0] ||
                              error.response?.data?.error ||
                              Object.values(error.response?.data || {}).flat()[0] ||
                              'Signup failed. Please check your information.'
          throw new Error(errorMessage)
        }
      },

      logout: () => {
        apiClient.clearAuth()
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
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

