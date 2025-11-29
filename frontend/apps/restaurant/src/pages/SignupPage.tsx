import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import apiClient from '@/packages/api/client'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/packages/ui/components/card'

const CUISINES = ['INDIAN', 'ITALIAN', 'CHINESE', 'FAST_FOOD', 'JAPANESE', 'AMERICAN', 'VEGAN']

export default function SignupPage() {
  const navigate = useNavigate()
  const { login } = useAuthStore()
  const [formState, setFormState] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    password: '',
    restaurantName: '',
    restaurantType: 'NON_VEG',
    address: '',
    city: '',
    state: '',
    postalCode: '',
    country: 'India',
    deliveryRadiusKm: 5,
    otpCode: '',
  })
  const [cuisines, setCuisines] = useState<string[]>(['INDIAN'])
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [otpStatus, setOtpStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const [otpLoading, setOtpLoading] = useState(false)

  const updateField = (field: string, value: string | number) => {
    setFormState((prev) => ({ ...prev, [field]: value }))
  }

  const validatePhone = (phone: string): boolean => {
    // Remove spaces, dashes, and parentheses
    const cleaned = phone.replace(/[\s\-()]/g, '')
    // Check if it's a valid phone number (10-15 digits, optionally starting with +)
    return /^\+?\d{10,15}$/.test(cleaned)
  }

  const handleSendOtp = async () => {
    setOtpLoading(true)
    setOtpStatus('')
    
    // Normalize email
    const normalizedEmail = formState.email.trim().toLowerCase()
    
    // Validate phone if provided
    if (formState.phone && !validatePhone(formState.phone)) {
      setOtpStatus('Please enter a valid phone number (10-15 digits)')
      setOtpLoading(false)
      return
    }
    
    try {
      await apiClient.post('/auth/otp/send/', {
        email: normalizedEmail,
        phone: formState.phone.trim(),
        type: 'EMAIL_VERIFICATION',
      })
      setOtpStatus('OTP sent successfully. Check your inbox (in dev mode the code is logged to the console).')
    } catch (err: any) {
      setOtpStatus(err.response?.data?.error || err.response?.data?.detail || 'Unable to send OTP. Please check the email/phone fields.')
    } finally {
      setOtpLoading(false)
    }
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    setSuccess('')
    
    // Validate phone
    if (formState.phone && !validatePhone(formState.phone)) {
      setError('Please enter a valid phone number (10-15 digits)')
      return
    }
    
    // Normalize email
    const normalizedEmail = formState.email.trim().toLowerCase()
    
    setLoading(true)
    try {
      const response = await apiClient.post('/restaurants/onboarding/signup/', {
        first_name: formState.firstName.trim(),
        last_name: formState.lastName.trim(),
        email: normalizedEmail,
        phone: formState.phone.trim(),
        password: formState.password,
        otp_code: formState.otpCode.trim(),
        otp_type: 'EMAIL_VERIFICATION',
        restaurant_name: formState.restaurantName.trim(),
        restaurant_type: formState.restaurantType,
        cuisine_types: cuisines,
        address: formState.address.trim(),
        city: formState.city.trim(),
        state: formState.state.trim(),
        postal_code: formState.postalCode.trim(),
        country: formState.country.trim(),
        delivery_radius_km: formState.deliveryRadiusKm,
      })
      
      // Login after successful signup
      try {
        const user = await login(normalizedEmail, formState.password)
        setSuccess('Account created! Redirecting you to onboarding…')
        // Give the backend a moment to finalize the restaurant creation
        setTimeout(() => {
          navigate('/onboarding', { replace: true })
        }, 1500)
      } catch (loginErr: any) {
        console.error('Login after signup failed:', loginErr)
        const loginErrorMsg = loginErr.message || loginErr.response?.data?.error || 'Login failed'
        setError(`Account created but login failed: ${loginErrorMsg}. Please try logging in manually.`)
      }
    } catch (err: any) {
      console.error('Signup error:', err)
      
      // Better error handling
      if (!err.response) {
        setError('Network error. Please check if the backend server is running at http://localhost:8000')
      } else if (err.response.status === 400) {
        const data = err.response.data
        const errorMessages = []
        if (data.otp_code) errorMessages.push(`OTP: ${Array.isArray(data.otp_code) ? data.otp_code[0] : data.otp_code}`)
        if (data.email) errorMessages.push(`Email: ${Array.isArray(data.email) ? data.email[0] : data.email}`)
        if (data.phone) errorMessages.push(`Phone: ${Array.isArray(data.phone) ? data.phone[0] : data.phone}`)
        if (data.password) errorMessages.push(`Password: ${Array.isArray(data.password) ? data.password[0] : data.password}`)
        if (data.non_field_errors) errorMessages.push(Array.isArray(data.non_field_errors) ? data.non_field_errors[0] : data.non_field_errors)
        if (data.detail) errorMessages.push(data.detail)
        setError(errorMessages.length > 0 ? errorMessages.join('. ') : 'Validation error. Please check your input.')
      } else if (err.response.status === 500) {
        setError('Server error. Please try again later.')
      } else {
        setError(err.response?.data?.detail || err.response?.data?.error || err.message || 'Signup failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const toggleCuisine = (cuisine: string) => {
    setCuisines((prev) =>
      prev.includes(cuisine) ? prev.filter((c) => c !== cuisine) : [...prev, cuisine]
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center page-background py-16 px-4">
      <Card className="w-full max-w-3xl shadow-xl border border-white/70 bg-white/90 backdrop-blur">
        <CardHeader>
          <CardTitle className="text-3xl font-semibold text-primary-600 text-center">Restaurant Onboarding</CardTitle>
          <CardDescription className="text-center text-slate-600">
            Verify your contact details, create a password, and tell us about your Bangalore kitchen.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">{error}</div>}
            {success && <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-green-700">{success}</div>}
            <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input value={formState.firstName} onChange={(e) => updateField('firstName', e.target.value)} placeholder="First name" required />
              <Input value={formState.lastName} onChange={(e) => updateField('lastName', e.target.value)} placeholder="Last name" />
              <Input type="email" value={formState.email} onChange={(e) => updateField('email', e.target.value)} placeholder="Owner email" required />
              <Input value={formState.phone} onChange={(e) => updateField('phone', e.target.value)} placeholder="WhatsApp / phone" required />
              <Input type="password" value={formState.password} onChange={(e) => updateField('password', e.target.value)} placeholder="Password" required />
              <div className="flex items-center gap-2">
                <Input value={formState.otpCode} onChange={(e) => updateField('otpCode', e.target.value)} placeholder="OTP code" required />
                <Button type="button" variant="outline" onClick={handleSendOtp} disabled={otpLoading || !formState.email}>
                  {otpLoading ? 'Sending…' : 'Send OTP'}
                </Button>
              </div>
            </section>
            {otpStatus && <p className="text-sm text-slate-500">{otpStatus}</p>}

            <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input value={formState.restaurantName} onChange={(e) => updateField('restaurantName', e.target.value)} placeholder="Restaurant name" required />
              <select
                value={formState.restaurantType}
                onChange={(e) => updateField('restaurantType', e.target.value)}
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm"
              >
                <option value="NON_VEG">Non-Veg</option>
                <option value="VEG">Veg</option>
                <option value="PURE_VEG">Pure Veg</option>
              </select>
              <Input value={formState.address} onChange={(e) => updateField('address', e.target.value)} placeholder="Kitchen address" required />
              <Input value={formState.city} onChange={(e) => updateField('city', e.target.value)} placeholder="City" required />
              <Input value={formState.state} onChange={(e) => updateField('state', e.target.value)} placeholder="State" required />
              <Input value={formState.postalCode} onChange={(e) => updateField('postalCode', e.target.value)} placeholder="Postal code" required />
            </section>

            <section>
              <p className="text-sm font-semibold text-slate-600 mb-2">Cuisine Types</p>
              <div className="flex flex-wrap gap-2">
                {CUISINES.map((cuisine) => {
                  const active = cuisines.includes(cuisine)
                  return (
                    <button
                      type="button"
                      key={cuisine}
                      onClick={() => toggleCuisine(cuisine)}
                      className={`rounded-full border px-3 py-1 text-xs font-semibold transition ${
                        active ? 'bg-primary-600 text-white border-primary-600' : 'border-slate-200 text-slate-600'
                      }`}
                    >
                      {cuisine.replace('_', ' ')}
                    </button>
                  )
                })}
              </div>
            </section>

            <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                type="number"
                min={1}
                value={formState.deliveryRadiusKm}
                onChange={(e) => updateField('deliveryRadiusKm', Number(e.target.value))}
                placeholder="Delivery radius (KM)"
              />
              <Input value={formState.country} onChange={(e) => updateField('country', e.target.value)} placeholder="Country" />
            </section>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Creating account…' : 'Create restaurant account'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}


