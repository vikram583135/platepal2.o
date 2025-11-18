import { Button } from '@/packages/ui/components/button'
import { Loader2, Power, Plus } from 'lucide-react'

interface RestaurantOption {
  id: number
  name: string
  city?: string
  is_online?: boolean
}

interface TopBarProps {
  restaurants: RestaurantOption[]
  selectedRestaurantId: number | null
  isOnline?: boolean
  toggleOnline: () => void
  togglingOnline: boolean
}

export function TopBar({ restaurants, selectedRestaurantId, isOnline, toggleOnline, togglingOnline }: TopBarProps) {
  // Get the selected restaurant name for display
  const selectedRestaurant = restaurants.find((r) => r.id === selectedRestaurantId)
  const restaurantDisplayName = selectedRestaurant 
    ? `${selectedRestaurant.name}${selectedRestaurant.city ? ` • ${selectedRestaurant.city}` : ''}`
    : 'Restaurant'

  return (
    <header className="flex flex-col gap-4 border-b border-slate-100 bg-white/70 backdrop-blur px-4 py-4 shadow-sm sm:flex-row sm:items-center sm:justify-between sm:px-6">
      <div className="flex items-center gap-3">
        <div className="px-3 py-2 text-sm font-medium text-slate-700">
          {restaurantDisplayName}
        </div>
        <div className={`rounded-full px-3 py-1 text-xs font-semibold ${isOnline ? 'bg-green-100 text-green-800' : 'bg-slate-200 text-slate-600'}`}>
          {isOnline ? 'Online' : 'Offline'}
        </div>
        <Button
          size="sm"
          className={`inline-flex items-center gap-2 ${
            isOnline
              ? 'bg-green-600 hover:bg-green-700 text-white'
              : 'bg-zomato-red hover:bg-zomato-darkRed text-white'
          }`}
          onClick={toggleOnline}
          disabled={togglingOnline}
        >
          {togglingOnline ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Power className="h-3.5 w-3.5" />}
          {isOnline ? 'Go Offline' : 'Go Online'}
        </Button>
      </div>
      <div className="flex items-center gap-3">
        <Button 
          variant="secondary" 
          size="sm"
          onClick={() => window.location.href = '/onboarding'}
        >
          Complete Onboarding
        </Button>
        <Button 
          size="sm" 
          className="inline-flex items-center gap-2 bg-zomato-red hover:bg-zomato-darkRed text-white"
          onClick={() => window.location.href = '/orders'}
        >
          <Plus className="h-3.5 w-3.5" />
          New Order
        </Button>
      </div>
    </header>
  )
}


