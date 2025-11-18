import { useState } from 'react'
import { Button } from '@/packages/ui/components/button'
import apiClient from '@/packages/api/client'
import { useAuthStore } from '../stores/authStore'
import { useNavigate } from 'react-router-dom'

interface SocialLoginButtonsProps {
  onError?: (error: string) => void
}

export default function SocialLoginButtons({ onError }: SocialLoginButtonsProps) {
  const [loading, setLoading] = useState<'google' | 'apple' | 'facebook' | null>(null)
  const { setUser } = useAuthStore()
  const navigate = useNavigate()

  const handleSocialLogin = async (provider: 'google' | 'apple' | 'facebook') => {
    setLoading(provider)
    
    try {
      // In production, this would use OAuth SDKs (Google Sign-In, Apple Sign-In, Facebook SDK)
      // For now, we'll create a mock implementation that accepts user data
      
      // Mock OAuth flow - in production, this would:
      // 1. Open OAuth popup/redirect
      // 2. Get authorization code/token from provider
      // 3. Send to backend for verification
      
      // For development, we'll use a simple prompt
      const email = prompt(`Enter email for ${provider} login (mock):`)
      if (!email) {
        setLoading(null)
        return
      }

      const mockData: any = {
        email,
        [`${provider}_id`]: `mock_${provider}_${Date.now()}`,
        first_name: 'Test',
        last_name: 'User',
      }

      if (provider === 'google') {
        mockData.id_token = 'mock_token'
        mockData.google_id = mockData[`${provider}_id`]
      } else if (provider === 'apple') {
        mockData.identity_token = 'mock_token'
        mockData.apple_id = mockData[`${provider}_id`]
      } else if (provider === 'facebook') {
        mockData.access_token = 'mock_token'
        mockData.facebook_id = mockData[`${provider}_id`]
      }

      let response
      try {
        response = await apiClient.post(`/auth/oauth/${provider}/`, mockData)
      } catch (e: any) {
        // Gracefully handle environments where social auth isn't configured
        const status = e?.response?.status
        if (status === 404 || status === 501) {
          throw new Error(`${provider[0].toUpperCase() + provider.slice(1)} login is not configured for this environment.`)
        }
        throw e
      }
      
      const { user, tokens } = response.data
      
      apiClient.setAuthToken(tokens.access)
      apiClient.setRefreshToken(tokens.refresh)
      
      setUser(user)
      
      navigate('/')
    } catch (err: any) {
      const errorMsg = err.response?.data?.error || err.message || `${provider} login failed`
      if (onError) {
        onError(errorMsg)
      } else {
        alert(errorMsg)
      }
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="space-y-3">
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="px-2 bg-white text-gray-500">Or continue with</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={() => handleSocialLogin('google')}
          disabled={loading !== null}
          className="w-full"
        >
          {loading === 'google' ? (
            '...'
          ) : (
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="currentColor"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="currentColor"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="currentColor"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
          )}
        </Button>

        <Button
          type="button"
          variant="outline"
          onClick={() => handleSocialLogin('apple')}
          disabled={loading !== null}
          className="w-full"
        >
          {loading === 'apple' ? (
            '...'
          ) : (
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
            </svg>
          )}
        </Button>

        <Button
          type="button"
          variant="outline"
          onClick={() => handleSocialLogin('facebook')}
          disabled={loading !== null}
          className="w-full"
        >
          {loading === 'facebook' ? (
            '...'
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
            </svg>
          )}
        </Button>
      </div>
    </div>
  )
}

