import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { User } from '@/packages/types'
import apiClient from '@/packages/api/client'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  login: (email: string, password: string, twoFactorCode?: string) => Promise<User>
  signup: (email: string, password: string, firstName: string, lastName: string) => Promise<void>
  logout: () => void
  setUser: (user: User) => void
  setTokens: (access: string, refresh: string) => void
  biometricLogin: (biometricId: string, challengeResponse?: string) => Promise<User>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,

      login: async (email: string, password: string, twoFactorCode?: string) => {
        try {
          const normalizedEmail = email.trim().toLowerCase()
          const response = await apiClient.post('/auth/token/', { 
            email: normalizedEmail, 
            password,
            ...(twoFactorCode && { two_factor_code: twoFactorCode })
          })
          
          // Check if 2FA is required
          if (response.data.requires_2fa) {
            throw new Error('2FA_REQUIRED')
          }
          
          const { access, refresh } = response.data
          
          apiClient.setAuthToken(access)
          apiClient.setRefreshToken(refresh)
          
          const userResponse = await apiClient.get('/auth/users/me/')
          const user = userResponse.data
          
          // Validate that user has DELIVERY role
          if (user.role !== 'DELIVERY') {
            // Clear tokens if role is incorrect
            apiClient.clearAuth()
            throw new Error('This account is not authorized for delivery portal. Please use the correct portal for your account type.')
          }
          
          set({
            user,
            accessToken: access,
            refreshToken: refresh,
            isAuthenticated: true,
          })
          
          return user
        } catch (error: any) {
          if (error.message === '2FA_REQUIRED') {
            throw error
          }
          console.error('Login error:', error?.response?.data || error?.message || error)
          const errorMessage = error.response?.data?.detail || 
                              error.response?.data?.non_field_errors?.[0] ||
                              'Login failed. Please check your credentials.'
          throw new Error(errorMessage)
        }
      },

      biometricLogin: async (biometricId: string, challengeResponse?: string) => {
        try {
          const response = await apiClient.post('/auth/biometric-auth/login/', {
            biometric_id: biometricId,
            challenge_response: challengeResponse,
            device_id: navigator.userAgent,
            device_name: 'Mobile Device',
            device_type: 'MOBILE_ANDROID'
          })
          
          const { tokens, user } = response.data
          
          // Validate that user has DELIVERY role
          if (user.role !== 'DELIVERY') {
            // Don't set tokens if role is incorrect
            throw new Error('This account is not authorized for delivery portal. Please use the correct portal for your account type.')
          }
          
          apiClient.setAuthToken(tokens.access)
          apiClient.setRefreshToken(tokens.refresh)
          
          set({
            user,
            accessToken: tokens.access,
            refreshToken: tokens.refresh,
            isAuthenticated: true,
          })
          
          return user
        } catch (error: any) {
          const errorMessage = error.response?.data?.error ||
                              error.response?.data?.detail ||
                              'Biometric login failed'
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
            role: 'DELIVERY',
          })
          
          const { user, tokens } = response.data
          
          // Validate that user has DELIVERY role (should always be DELIVERY for signup, but verify)
          if (user.role !== 'DELIVERY') {
            throw new Error('Invalid account type. Delivery signup must create a DELIVERY account.')
          }
          
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
      name: 'delivery-auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
)

