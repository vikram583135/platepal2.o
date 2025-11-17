import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Button } from '@/packages/ui/components/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/packages/ui/components/card'
import OTPInput from '../components/OTPInput'
import apiClient from '@/packages/api/client'

interface LocationState {
  email?: string
  phone?: string
  type?: 'EMAIL_VERIFICATION' | 'PHONE_VERIFICATION' | 'LOGIN' | 'PASSWORD_RESET'
  fromSignup?: boolean
  redirectTo?: string
}

export default function OTPVerificationPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as LocationState | null

  const [otp, setOtp] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [resendLoading, setResendLoading] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)
  const [expiresAt, setExpiresAt] = useState<Date | null>(null)

  const email = state?.email || ''
  const phone = state?.phone || ''
  const otpType = state?.type || 'EMAIL_VERIFICATION'

  useEffect(() => {
    if (!email && !phone) {
      navigate('/signup')
      return
    }

    // Start countdown timer
    const timer = setInterval(() => {
      if (expiresAt) {
        const now = new Date()
        const diff = Math.max(0, Math.floor((expiresAt.getTime() - now.getTime()) / 1000))
        if (diff === 0) {
          setError('OTP has expired. Please request a new one.')
        }
      }
    }, 1000)

    return () => clearInterval(timer)
  }, [email, phone, navigate, expiresAt])

  useEffect(() => {
    // Auto-verify when OTP is complete
    if (otp.length === 6) {
      handleVerify()
    }
  }, [otp])

  useEffect(() => {
    // Resend cooldown timer
    if (resendCooldown > 0) {
      const timer = setTimeout(() => {
        setResendCooldown(resendCooldown - 1)
      }, 1000)
      return () => clearTimeout(timer)
    }
  }, [resendCooldown])

  const handleVerify = async () => {
    if (otp.length !== 6) {
      setError('Please enter the complete 6-digit code')
      return
    }

    setError('')
    setLoading(true)

    try {
      const response = await apiClient.post('/auth/otp/verify/', {
        email: email || undefined,
        phone: phone || undefined,
        code: otp,
        type: otpType,
      })

      if (response.data.verified) {
        // Navigate to the specified redirect path or default to home
        const redirectPath = state?.redirectTo || '/'
        navigate(redirectPath)
      } else {
        setError(response.data.error || 'Verification failed')
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Verification failed')
    } finally {
      setLoading(false)
    }
  }

  const handleResend = async () => {
    if (resendCooldown > 0) return

    setResendLoading(true)
    setError('')

    try {
      const response = await apiClient.post('/auth/otp/send/', {
        email: email || undefined,
        phone: phone || undefined,
        type: otpType,
      })

      if (response.data.expires_at) {
        setExpiresAt(new Date(response.data.expires_at))
      }

      setResendCooldown(60) // 60 second cooldown
      setOtp('')
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Failed to resend OTP')
    } finally {
      setResendLoading(false)
    }
  }

  const displayValue = email || phone

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Verify Your {email ? 'Email' : 'Phone'}</CardTitle>
          <CardDescription className="text-center">
            Enter the 6-digit code sent to {displayValue}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-4 text-center">
                Verification Code
              </label>
              <OTPInput
                length={6}
                value={otp}
                onChange={setOtp}
                disabled={loading}
              />
            </div>

            <Button
              onClick={handleVerify}
              className="w-full"
              disabled={loading || otp.length !== 6}
            >
              {loading ? 'Verifying...' : 'Verify'}
            </Button>

            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">
                Didn't receive the code?
              </p>
              <Button
                variant="outline"
                onClick={handleResend}
                disabled={resendLoading || resendCooldown > 0}
                className="w-full"
              >
                {resendLoading
                  ? 'Sending...'
                  : resendCooldown > 0
                  ? `Resend in ${resendCooldown}s`
                  : 'Resend Code'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

