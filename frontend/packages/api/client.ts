/**
 * API client configuration
 */
import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

// Log API URL in development
if (import.meta.env.DEV) {
  console.log('API Base URL:', API_BASE_URL)
}

class ApiClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000, // 10 second timeout
    })

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token')
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor to handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
              const response = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, {
                refresh: refreshToken,
              })

              const { access } = response.data
              localStorage.setItem('access_token', access)

              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${access}`
              }

              return this.client(originalRequest)
            }
          } catch (refreshError) {
            // Refresh failed, clear tokens
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            // Don't redirect here - let the component handle navigation
            // This prevents issues with React Router
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  get instance(): AxiosInstance {
    return this.client
  }

  setAuthToken(token: string) {
    localStorage.setItem('access_token', token)
  }

  setRefreshToken(token: string) {
    localStorage.setItem('refresh_token', token)
  }

  clearAuth() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // Wrapper methods for easier usage
  get(url: string, config?: any) {
    return this.client.get(url, config)
  }

  post(url: string, data?: any, config?: any) {
    return this.client.post(url, data, config)
  }

  put(url: string, data?: any, config?: any) {
    return this.client.put(url, data, config)
  }

  patch(url: string, data?: any, config?: any) {
    return this.client.patch(url, data, config)
  }

  delete(url: string, config?: any) {
    return this.client.delete(url, config)
  }
}

export const apiClient = new ApiClient()
export default apiClient

