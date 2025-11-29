import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { User } from '@/packages/types'
import apiClient from '@/packages/api/client'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<User>
  logout: () => void
  setUser: (user: User) => void
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
          // Normalize email (trim and lowercase) for consistent authentication
          const normalizedEmail = email.trim().toLowerCase()
          const response = await apiClient.post('/auth/token/', { email: normalizedEmail, password })
          const { access, refresh } = response.data

          if (!access || !refresh) {
            throw new Error('Invalid response from server')
          }

          apiClient.setAuthToken(access)
          apiClient.setRefreshToken(refresh)

          const userResponse = await apiClient.get('/auth/users/me/')
          const user = userResponse.data

          if (!user) {
            throw new Error('Failed to retrieve user information')
          }

          set({
            user,
            accessToken: access,
            refreshToken: refresh,
            isAuthenticated: true,
          })

          // Return user for role checking
          return user
        } catch (error: any) {
          console.error('Login error:', error)

          // Handle network errors
          if (!error.response) {
            const apiUrl = (import.meta as any).env.VITE_API_BASE_URL || 'http://localhost:8000/api'
            const errorMsg = error.code === 'ECONNREFUSED'
              ? `Cannot connect to backend server at ${apiUrl}. Please ensure the Django backend is running on port 8000.`
              : error.message || `Network error. Please check if the backend server is running at ${apiUrl}`
            throw new Error(errorMsg)
          }

          // Handle different error formats
          const errorMessage = error.response?.data?.detail ||
            error.response?.data?.non_field_errors?.[0] ||
            error.response?.data?.error ||
            error.response?.data?.message ||
            (error.response?.status === 401 ? 'Invalid email or password' : 'Login failed. Please check your credentials.')
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
        set({ user })
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

