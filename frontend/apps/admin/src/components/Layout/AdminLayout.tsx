import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAdminSocket } from '../../hooks/useAdminSocket'
import { 
  LayoutDashboard, Users, ShoppingBag, CreditCard, 
  Building2, Truck, Settings, FileText, BarChart3,
  Shield, Bell, LogOut
} from 'lucide-react'

interface AdminLayoutProps {
  children: ReactNode
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const location = useLocation()
  
  // Initialize WebSocket connection for admin
  useAdminSocket()

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/users', label: 'Users', icon: Users },
    { path: '/restaurants', label: 'Restaurants', icon: Building2 },
    { path: '/delivery', label: 'Delivery Partners', icon: Truck },
    { path: '/orders', label: 'Orders', icon: ShoppingBag },
    { path: '/financials/transactions', label: 'Financials', icon: CreditCard },
    { path: '/analytics/executive', label: 'Analytics', icon: BarChart3 },
    { path: '/moderation/reviews', label: 'Moderation', icon: Shield },
    { path: '/support', label: 'Support', icon: FileText },
    { path: '/settings/api-tokens', label: 'API Tokens', icon: Settings },
  ]

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-gray-200 min-h-screen">
          <div className="p-4 border-b border-gray-200">
            <h1 className="text-xl font-bold text-gray-900">PlatePal Admin</h1>
          </div>
          <nav className="p-2">
            {menuItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-3 py-2 rounded-md mb-1 ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </nav>
          <div className="absolute bottom-0 w-64 p-4 border-t border-gray-200">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-3 py-2 rounded-md text-gray-700 hover:bg-gray-50 w-full"
            >
              <LogOut className="w-5 h-5" />
              <span>Logout</span>
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1">
          {/* Header */}
          <header className="bg-white border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                {menuItems.find(item => item.path === location.pathname)?.label || 'Admin Panel'}
              </h2>
              <div className="flex items-center gap-4">
                <button className="p-2 text-gray-600 hover:text-gray-900">
                  <Bell className="w-5 h-5" />
                </button>
              </div>
            </div>
          </header>

          {/* Page Content */}
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

