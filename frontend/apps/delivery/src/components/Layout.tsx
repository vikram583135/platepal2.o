import { useEffect } from 'react'
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useDeliverySocket } from '../hooks/useDeliverySocket'
import { Button } from '@/packages/ui/components/button'
import { cn } from '@/packages/utils/cn'

export default function Layout() {
  const { user, logout, isAuthenticated } = useAuthStore()
  const navigate = useNavigate()
  const location = useLocation()
  
  // Validate user role on mount (defense-in-depth)
  useEffect(() => {
    if (isAuthenticated && user && user.role !== 'DELIVERY') {
      // User has wrong role, logout and redirect
      logout()
      navigate('/login', { replace: true })
    }
  }, [isAuthenticated, user, logout, navigate])
  
  // Initialize WebSocket connection for delivery/rider
  useDeliverySocket(user?.id)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const navItems = [
    { path: '/', label: 'Dashboard', icon: '📊' },
    { path: '/offers', label: 'Offers', icon: '📦' },
    { path: '/orders', label: 'Orders', icon: '🚚' },
    { path: '/earnings', label: 'Earnings', icon: '💰' },
    { path: '/analytics', label: 'Analytics', icon: '📈' },
    { path: '/settings', label: 'Settings', icon: '⚙️' },
  ]

  // Don't render layout for login/signup/onboarding pages - just render the page directly
  if (location.pathname === '/login' || location.pathname === '/signup' || location.pathname.startsWith('/onboarding')) {
    return <Outlet />
  }

  // For protected routes, ProtectedRoute will handle auth checks
  // Layout just provides the UI structure for authenticated users

  return (
    <div className="min-h-screen delivery-page-background">
      {/* Skip to main content link for accessibility */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>
      
      {/* Top Navigation */}
      <nav className="bg-white/90 backdrop-blur shadow-sm border-b border-emerald-100" role="navigation" aria-label="Main navigation">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <Link to="/" className="text-xl font-bold text-emerald-600 hover:text-emerald-700 transition-colors">
                PlatePal Delivery
              </Link>
              <div className="hidden md:flex space-x-4">
                {navItems.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      'px-3 py-2 rounded-md text-sm font-medium transition-all',
                      location.pathname === item.path
                        ? 'delivery-nav-active shadow-sm'
                        : 'text-gray-700 hover:bg-emerald-50 hover:text-emerald-700 border border-transparent hover:border-emerald-100'
                    )}
                  >
                    <span className="mr-2">{item.icon}</span>
                    {item.label}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {user && (
                <span className="text-sm text-gray-700 bg-emerald-50 px-3 py-1 rounded-lg border border-emerald-100">
                  {user.first_name} {user.last_name}
                </span>
              )}
              <Button onClick={handleLogout} variant="outline" size="sm" className="border-emerald-200 text-emerald-700 hover:bg-emerald-50">
                Logout
              </Button>
            </div>
          </div>
        </div>
        
        {/* Mobile Navigation */}
        <div className="md:hidden border-t border-emerald-100">
          <div className="px-2 pt-2 pb-3 space-y-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  'block px-3 py-2 rounded-md text-base font-medium transition-all',
                  location.pathname === item.path
                    ? 'delivery-nav-active'
                    : 'text-gray-700 hover:bg-emerald-50 hover:text-emerald-700'
                )}
              >
                <span className="mr-2">{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main id="main-content" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 delivery-page-content" role="main">
        <Outlet />
      </main>
    </div>
  )
}

