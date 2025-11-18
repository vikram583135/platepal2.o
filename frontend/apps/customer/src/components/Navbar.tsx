import { Link } from 'react-router-dom'
import { ShoppingCart, User, Settings, Bell } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import { useCartStore } from '../stores/cartStore'
import { Button } from '@/packages/ui/components/button'
import { Badge } from '@/packages/ui/components/badge'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'

export default function Navbar() {
  const { isAuthenticated, isGuest, logout } = useAuthStore()
  const { getItemCount } = useCartStore()
  const cartCount = getItemCount()

  const { data: unreadCount } = useQuery({
    queryKey: ['notifications-unread'],
    queryFn: async () => {
      const response = await apiClient.get('/notifications/notifications/unread_count/')
      return response.data.count || 0
    },
    enabled: isAuthenticated,
    refetchInterval: 30000, // Poll every 30 seconds
  })

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-2xl font-bold text-primary-600">
            PlatePal
          </Link>

          <div className="flex items-center gap-4">
                <Link to="/restaurants" className="text-gray-700 hover:text-primary-600">
                  Restaurants
                </Link>
                <Link to="/offers" className="text-gray-700 hover:text-primary-600">
                  Offers
                </Link>
                <Link to="/wallet" className="text-gray-700 hover:text-primary-600">
                  Wallet
                </Link>
                <Link to="/membership" className="text-gray-700 hover:text-primary-600">
                  Membership
                </Link>
                <Link to="/rewards" className="text-gray-700 hover:text-primary-600">
                  Rewards
                </Link>
                <Link to="/support" className="text-gray-700 hover:text-primary-600">
                  Support
                </Link>

            {isAuthenticated ? (
              <>
                <Link to="/orders" className="text-gray-700 hover:text-primary-600">
                  Orders
                </Link>
                {isAuthenticated && (
                  <Link to="/notifications" className="relative">
                    <Bell className="w-6 h-6 text-gray-700" />
                    {unreadCount > 0 && (
                      <Badge className="absolute -top-2 -right-2 h-5 w-5 flex items-center justify-center p-0">
                        {unreadCount > 9 ? '9+' : unreadCount}
                      </Badge>
                    )}
                  </Link>
                )}
                <Link to="/cart" className="relative">
                  <ShoppingCart className="w-6 h-6 text-gray-700" />
                  {cartCount > 0 && (
                    <span className="absolute -top-2 -right-2 bg-primary-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {cartCount > 9 ? '9+' : cartCount}
                    </span>
                  )}
                </Link>
                <Link to="/profile">
                  <User className="w-6 h-6 text-gray-700" />
                </Link>
                <Link to="/settings">
                  <Settings className="w-6 h-6 text-gray-700" />
                </Link>
                <Button variant="outline" size="sm" onClick={logout}>
                  Logout
                </Button>
              </>
            ) : (
              <>
                {isGuest && (
                  <div className="flex items-center gap-2 bg-yellow-50 border border-yellow-200 px-3 py-1 rounded-md text-xs text-yellow-800">
                    Guest Mode: limited features
                    <Link to="/login" className="underline font-medium">Login</Link>
                  </div>
                )}
                {!isGuest && (
                  <>
                    <Link to="/login">
                      <Button variant="ghost" size="sm">Login</Button>
                    </Link>
                    <Link to="/signup">
                      <Button size="sm">Sign Up</Button>
                    </Link>
                  </>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

