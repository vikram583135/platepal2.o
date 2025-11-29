import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/packages/ui/components/card'
import apiClient from '@/packages/api/client'
import SocialLoginButtons from '../components/SocialLoginButtons'

export default function SignupPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
    firstName: '',
    lastName: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { signup } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (formData.password !== formData.passwordConfirm) {
      setError('Passwords do not match')
      return
    }

    setLoading(true)

    try {
      // First, send OTP (don't fail signup if OTP sending fails in dev)
      try {
        await apiClient.post('/auth/otp/send/', {
          email: formData.email,
          type: 'EMAIL_VERIFICATION',
        })
      } catch (otpError: any) {
        // Log OTP error but continue with signup
        if (otpError) {
        // OTP sending failed, user can skip or retry
      }
        // In development, we can continue without OTP
        // In production, you might want to fail here
      }

      // Then register the user
      await signup(
        formData.email,
        formData.password,
        formData.firstName,
        formData.lastName
      )

      // Navigate to OTP verification page
      navigate('/verify-otp', {
        state: {
          email: formData.email,
          type: 'EMAIL_VERIFICATION',
          fromSignup: true, // Flag to indicate coming from signup
          redirectTo: '/', // Where to redirect after verification
        },
      })
    } catch (err: any) {
      const errorMessage = err.message || 
                          err.response?.data?.email?.[0] ||
                          err.response?.data?.password?.[0] ||
                          err.response?.data?.password_confirm?.[0] ||
                          err.response?.data?.non_field_errors?.[0] ||
                          err.response?.data?.error ||
                          (typeof err.response?.data === 'string' ? err.response.data : null) ||
                          'Signup failed. Please check your information and try again.'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center page-background py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Create Account</CardTitle>
          <CardDescription className="text-center">
            Sign up to start ordering food online
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
                  First Name
                </label>
                <Input
                  id="firstName"
                  value={formData.firstName}
                  onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                  required
                />
              </div>
              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name
                </label>
                <Input
                  id="lastName"
                  value={formData.lastName}
                  onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <Input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
              />
            </div>

            <div>
              <label htmlFor="passwordConfirm" className="block text-sm font-medium text-gray-700 mb-1">
                Confirm Password
              </label>
              <Input
                id="passwordConfirm"
                type="password"
                value={formData.passwordConfirm}
                onChange={(e) => setFormData({ ...formData, passwordConfirm: e.target.value })}
                required
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Creating account...' : 'Sign Up'}
            </Button>

            <SocialLoginButtons onError={setError} />

            <p className="text-center text-sm text-gray-600">
              Already have an account?{' '}
              <Link to="/login" className="text-primary-600 hover:underline">
                Login
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

