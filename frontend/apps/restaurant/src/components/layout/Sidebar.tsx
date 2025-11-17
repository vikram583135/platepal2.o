import { NavLink } from 'react-router-dom'
import { LayoutDashboard, Receipt, ListChecks, Boxes, Star, Wallet, Megaphone, Users, MessageCircle, BarChart2, Settings, MonitorPlay } from 'lucide-react'

const navLinks = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Orders', to: '/orders', icon: Receipt },
  { label: 'Menu', to: '/menu', icon: ListChecks },
  { label: 'Inventory', to: '/inventory', icon: Boxes },
  { label: 'Reviews', to: '/reviews', icon: Star },
  { label: 'Finance', to: '/finance', icon: Wallet },
  { label: 'Promotions', to: '/promotions', icon: Megaphone },
  { label: 'Staff', to: '/staff', icon: Users },
  { label: 'Communication', to: '/communications', icon: MessageCircle },
  { label: 'Analytics', to: '/analytics', icon: BarChart2 },
  { label: 'Settings', to: '/settings', icon: Settings },
  { label: 'KDS', to: '/kds', icon: MonitorPlay },
]

export function Sidebar() {
  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-64 border-r border-slate-100 bg-white/90 backdrop-blur">
      <div className="px-6 py-6 border-b border-gray-200 bg-zomato-red">
        <div className="text-2xl font-bold text-white tracking-tight">PlatePal</div>
        <p className="text-sm text-white/90">Restaurant Dashboard</p>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-4 space-y-1">
        {navLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 px-4 py-2 rounded-xl text-sm font-medium transition',
                isActive
                  ? 'bg-zomato-red text-white shadow-sm'
                  : 'text-zomato-gray hover:bg-zomato-lightGray hover:text-zomato-dark',
              ].join(' ')
            }
          >
            <link.icon className="w-4 h-4" />
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}


