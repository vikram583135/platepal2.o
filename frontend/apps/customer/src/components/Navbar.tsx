import { Link, useLocation } from 'react-router-dom'
import { ShoppingCart, User, Settings, Bell, Menu, X } from 'lucide-react'
import { useAuthStore } from '../stores/authStore'
import { useCartStore } from '../stores/cartStore'
import { Button } from '@/packages/ui/components/button'
import { Badge } from '@/packages/ui/components/badge'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { cn } from '@/packages/ui/utils/cn'
import { useState } from 'react'

export default function Navbar() {
  const { isAuthenticated, isGuest, logout } = useAuthStore()
  const { getItemCount } = useCartStore()
  const cartCount = getItemCount()
  const location = useLocation()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const { data: unreadCount } = useQuery({
    queryKey: ['notifications-unread'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/notifications/notifications/unread_count/')
        return response.data.count || 0
      } catch (error) {
        console.error('Failed to fetch unread notifications count:', error)
        return 0
      }
    },
    enabled: isAuthenticated,
    refetchInterval: 30000,
    retry: 1,
  })

  const navLinks = [
    { href: '/restaurants', label: 'Restaurants' },
    { href: '/offers', label: 'Offers' },
    { href: '/wallet', label: 'Wallet' },
    { href: '/membership', label: 'Membership' },
    { href: '/rewards', label: 'Rewards' },
    { href: '/support', label: 'Support' },
  ]

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-red-100 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="text-2xl font-bold text-zomato-red tracking-tight hover:opacity-90 transition-opacity">
              PlatePal
            </Link>
            <div className="hidden md:flex items-center gap-6">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  to={link.href}
                    className={cn(
                    "text-sm font-medium transition-colors hover:text-zomato-red",
                    location.pathname === link.href ? "text-zomato-red font-semibold" : "text-zomato-gray"
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <>
                <div className="hidden md:flex items-center gap-2">
                  <Link to="/orders">
                    <Button variant="ghost" size="sm" className="text-muted-foreground">Orders</Button>
                  </Link>
                  <Link to="/notifications" className="relative">
                    <Button variant="ghost" size="icon" className="relative">
                      <Bell className="h-5 w-5" />
                      {unreadCount > 0 && (
                        <Badge className="absolute -top-1 -right-1 h-4 w-4 p-0 flex items-center justify-center text-[10px]">
                          {unreadCount > 9 ? '9+' : unreadCount}
                        </Badge>
                      )}
                    </Button>
                  </Link>
                  <Link to="/cart">
                    <Button variant="ghost" size="icon" className="relative">
                      <ShoppingCart className="h-5 w-5" />
                      {cartCount > 0 && (
                        <Badge className="absolute -top-1 -right-1 h-4 w-4 p-0 flex items-center justify-center text-[10px]">
                          {cartCount > 9 ? '9+' : cartCount}
                        </Badge>
                      )}
                    </Button>
                  </Link>
                  <Link to="/profile">
                    <Button variant="ghost" size="icon">
                      <User className="h-5 w-5" />
                    </Button>
                  </Link>
                  <Link to="/settings">
                    <Button variant="ghost" size="icon">
                      <Settings className="h-5 w-5" />
                    </Button>
                  </Link>
                  <Button variant="outline" size="sm" onClick={logout} className="ml-2">
                    Logout
                  </Button>
                </div>
              </>
            ) : (
              <div className="hidden md:flex items-center gap-4">
                {isGuest && (
                  <div className="flex items-center gap-2 bg-yellow-500/10 border border-yellow-500/20 px-3 py-1 rounded-full text-xs text-yellow-600 font-medium">
                    Guest Mode
                    <Link to="/login" className="underline hover:text-yellow-700">Login</Link>
                  </div>
                )}
                {!isGuest && (
                  <>
                    <Link to="/login">
                      <Button variant="ghost" size="sm">Login</Button>
                    </Link>
                    <Link to="/signup">
                      <Button size="sm" className="bg-zomato-red hover:bg-zomato-darkRed text-white">Sign Up</Button>
                    </Link>
                  </>
                )}
              </div>
            )}

            {/* Mobile Menu Button */}
            <button
              className="md:hidden p-2 text-muted-foreground hover:text-foreground"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t bg-background p-4 space-y-4 animate-in slide-in-from-top-5">
          <div className="flex flex-col space-y-2">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                to={link.href}
                className="px-4 py-2 text-sm font-medium text-zomato-gray hover:text-zomato-red hover:bg-red-50 rounded-md"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          </div>
          <div className="border-t pt-4">
            {isAuthenticated ? (
              <div className="grid grid-cols-2 gap-2">
                <Link to="/orders" onClick={() => setIsMobileMenuOpen(false)}>
                  <Button variant="ghost" className="w-full justify-start">Orders</Button>
                </Link>
                <Link to="/cart" onClick={() => setIsMobileMenuOpen(false)}>
                  <Button variant="ghost" className="w-full justify-start">Cart ({cartCount})</Button>
                </Link>
                <Link to="/profile" onClick={() => setIsMobileMenuOpen(false)}>
                  <Button variant="ghost" className="w-full justify-start">Profile</Button>
                </Link>
                <Button variant="outline" onClick={logout} className="w-full">Logout</Button>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                <Link to="/login" onClick={() => setIsMobileMenuOpen(false)}>
                  <Button variant="ghost" className="w-full">Login</Button>
                </Link>
                <Link to="/signup" onClick={() => setIsMobileMenuOpen(false)}>
                  <Button className="w-full bg-zomato-red hover:bg-zomato-darkRed text-white">Sign Up</Button>
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}

