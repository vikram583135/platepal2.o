import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useAuthStore } from '../stores/authStore'
import apiClient from '@/packages/api/client'
import { Button } from '@/packages/ui/components/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/packages/ui/components/card'
import { Input } from '@/packages/ui/components/input'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [twoFactorCode, setTwoFactorCode] = useState('')
  const [requires2FA, setRequires2FA] = useState(false)
  const [error, setError] = useState('')
  const [useBiometric, setUseBiometric] = useState(false)

  const loginMutation = useMutation({
    mutationFn: async (data: { email: string; password: string; two_factor_code?: string }) => {
      try {
        const user = await login(data.email, data.password, data.two_factor_code)
        return user
      } catch (error: any) {
        if (error.message === '2FA_REQUIRED') {
          setRequires2FA(true)
          throw error
        }
        throw error
      }
    },
    onSuccess: () => {
      // Check onboarding status
      checkOnboardingStatus()
    },
    onError: (err: any) => {
      if (err.message !== '2FA_REQUIRED') {
        setError(err.message || 'Login failed')
      }
    }
  })

  const biometricLoginMutation = useMutation({
    mutationFn: async () => {
      // In production, get biometric ID from device
      const biometricId = localStorage.getItem('biometric_id')
      if (!biometricId) {
        throw new Error('Biometric not registered')
      }
      return await useAuthStore.getState().biometricLogin(biometricId)
    },
    onSuccess: () => {
      checkOnboardingStatus()
    },
    onError: (err: any) => {
      setError(err.message || 'Biometric login failed')
      setUseBiometric(false)
    }
  })

  const checkOnboardingStatus = async () => {
    try {
      const response = await apiClient.get('/deliveries/onboarding/status/')
      const onboarding = response.data
      
      // Check if onboarding status is APPROVED (backend returns 'APPROVED' status)
      if (onboarding.status === 'APPROVED') {
        navigate('/')
      } else {
        navigate('/onboarding')
      }
    } catch (error) {
      // If onboarding doesn't exist or API call fails, redirect to onboarding
      navigate('/onboarding')
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    loginMutation.mutate({
      email,
      password,
      ...(requires2FA && { two_factor_code: twoFactorCode })
    })
  }

  const handleBiometricLogin = () => {
    setUseBiometric(true)
    biometricLoginMutation.mutate()
  }

  // Check if biometric is available
  const biometricAvailable = localStorage.getItem('biometric_id') !== null

  return (
    <div className="min-h-screen flex items-center justify-center delivery-page-background px-4">
      <Card className="w-full max-w-md delivery-card border-emerald-200">
        <CardHeader className="bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-t-lg">
          <CardTitle className="text-2xl font-bold text-center text-white">Delivery Rider Login</CardTitle>
          <CardDescription className="text-center text-white/90">
            Sign in to your delivery account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!requires2FA ? (
              <>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="rider@example.com"
                    className="w-full"
                  />
                </div>
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                    Password
                  </label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="••••••••"
                    className="w-full"
                  />
                </div>
                {error && (
                  <div className="text-red-600 text-sm">{error}</div>
                )}
                <Button
                  type="submit"
                  className="w-full delivery-button-primary"
                  disabled={loginMutation.isPending}
                >
                  {loginMutation.isPending ? 'Logging in...' : 'Login'}
                </Button>
                
                {biometricAvailable && (
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={handleBiometricLogin}
                    disabled={biometricLoginMutation.isPending}
                  >
                    {biometricLoginMutation.isPending ? 'Authenticating...' : '🔒 Use Biometric Login'}
                  </Button>
                )}
                
                <div className="text-center text-sm">
                  <Link to="/signup" className="text-green-600 hover:underline">
                    Don't have an account? Sign up
                  </Link>
                </div>
              </>
            ) : (
              <>
                <div>
                  <label htmlFor="2fa" className="block text-sm font-medium text-gray-700 mb-1">
                    Two-Factor Authentication Code
                  </label>
                  <Input
                    id="2fa"
                    type="text"
                    value={twoFactorCode}
                    onChange={(e) => setTwoFactorCode(e.target.value)}
                    required
                    placeholder="Enter 6-digit code"
                    className="w-full"
                    maxLength={6}
                  />
                </div>
                {error && (
                  <div className="text-red-600 text-sm">{error}</div>
                )}
                <Button
                  type="submit"
                  className="w-full"
                  disabled={loginMutation.isPending}
                >
                  {loginMutation.isPending ? 'Verifying...' : 'Verify & Login'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setRequires2FA(false)
                    setTwoFactorCode('')
                    setError('')
                  }}
                >
                  Back
                </Button>
              </>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

