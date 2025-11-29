import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { BackendStatus } from '../components/BackendStatus'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const user = await login(email, password)
      
      // Check if user has restaurant or admin role
      if (user && (user.role === 'RESTAURANT' || user.role === 'ADMIN')) {
        navigate('/')
      } else {
        setError('Access denied. This portal is for restaurant owners only. Please use restaurant@platepal.com to login.')
        useAuthStore.getState().logout()
      }
    } catch (err: any) {
      console.error('Login error:', err)
      const errorMsg = err.message || err.response?.data?.error || 'Login failed. Please check your credentials.'
      setError(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center page-background py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md page-content">
        <BackendStatus />
        <Card className="w-full bg-white/95 backdrop-blur shadow-xl border-red-100">
        <CardHeader className="bg-gradient-to-r from-zomato-red to-zomato-darkRed text-white rounded-t-lg">
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
              <span className="text-zomato-red font-bold text-xl">P</span>
            </div>
            <CardTitle className="text-2xl text-white">PlatePal Restaurant</CardTitle>
          </div>
          <CardDescription className="text-white/90 text-center">
            Enter your credentials to access the restaurant portal
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                {error}
              </div>
            )}
            
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
                placeholder="restaurant@platepal.com"
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
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-zomato-red hover:bg-zomato-darkRed text-white font-semibold py-3"
              disabled={loading}
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>

            <p className="text-center text-sm text-zomato-gray">
              New to PlatePal?{' '}
              <Link to="/signup" className="text-zomato-red font-semibold hover:underline">
                Start onboarding
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
      </div>
    </div>
  )
}

