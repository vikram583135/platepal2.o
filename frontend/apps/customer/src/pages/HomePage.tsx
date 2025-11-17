import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/packages/ui/components/button'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Badge } from '@/packages/ui/components/badge'
import { Search, MapPin, Navigation, ChevronDown, TrendingUp, Star, ShoppingCart } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import LocationPicker from '../components/LocationPicker'
import SearchSuggestions from '../components/SearchSuggestions'
import { useAuthStore } from '../stores/authStore'
import { useCartStore } from '../stores/cartStore'
import { formatCurrency } from '@/packages/utils/format'
import SkeletonLoader from '../components/SkeletonLoader'
import PullToRefresh from '../components/PullToRefresh'
import { RestaurantCache } from '../utils/cache'
import { useOffline } from '../hooks/useOffline'

export default function HomePage() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuthStore()
  const { addItem } = useCartStore()
  const [location, setLocation] = useState<{ lat: number; lng: number; address?: string } | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showLocationPicker, setShowLocationPicker] = useState(false)
  const [showSavedLocations, setShowSavedLocations] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)

  const { data: savedLocations } = useQuery({
    queryKey: ['saved-locations'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/saved-locations/')
      return response.data.results || response.data
    },
    enabled: isAuthenticated,
  })

  const { data: trendingDishes, isLoading: trendingLoading, refetch: refetchTrending } = useQuery({
    queryKey: ['trending-dishes'],
    queryFn: async () => {
      const response = await apiClient.get('/restaurants/search/trending/?limit=8')
      return response.data.dishes || []
    },
  })

  useEffect(() => {
    // Auto-detect location on mount
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = pos.coords.latitude
          const lng = pos.coords.longitude
          
          try {
            const response = await apiClient.post('/restaurants/location/detect/', {
              latitude: lat,
              longitude: lng,
            })
            setLocation({
              lat,
              lng,
              address: `${response.data.address}, ${response.data.city}`,
            })
          } catch (error) {
            setLocation({ lat, lng })
          }
        },
        () => {
          // Geolocation failed, use default
          setLocation({ lat: 19.0760, lng: 72.8777, address: 'Mumbai, Maharashtra' })
        }
      )
    } else {
      setLocation({ lat: 19.0760, lng: 72.8777, address: 'Mumbai, Maharashtra' })
    }
  }, [])

  const handleSearch = (query?: string) => {
    const q = query || searchQuery
    if (q.trim()) {
      // Save search
      apiClient.post('/restaurants/search/save/', {
        query: q.trim(),
        type: 'general',
      }).catch(() => {}) // Ignore errors
      
      navigate(`/restaurants?search=${encodeURIComponent(q.trim())}`)
    } else {
      navigate('/restaurants')
    }
  }

  const handleLocationSelect = (loc: { lat: number; lng: number; address?: string }) => {
    setLocation(loc)
    setShowLocationPicker(false)
    // Filter restaurants by location
    navigate(`/restaurants?lat=${loc.lat}&lng=${loc.lng}`)
  }

  const handleSavedLocationSelect = (savedLoc: any) => {
    setLocation({
      lat: savedLoc.latitude,
      lng: savedLoc.longitude,
      address: savedLoc.address,
    })
    setShowSavedLocations(false)
    navigate(`/restaurants?lat=${savedLoc.latitude}&lng=${savedLoc.longitude}`)
  }

  const handleRefresh = async () => {
    await refetchTrending()
  }

  return (
    <PullToRefresh onRefresh={handleRefresh}>
      <div className="min-h-screen">
        {/* Hero Section */}
      <section className="bg-gradient-to-r from-primary-600 to-primary-800 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-5xl font-bold mb-4">Order Food Online</h1>
          <p className="text-xl mb-8">Discover amazing restaurants near you</p>
          
          <div className="max-w-2xl mx-auto">
            <div className="flex gap-2 bg-white rounded-lg p-2">
              <div className="flex-1 relative">
                <div className="flex items-center gap-2 px-4">
                  <MapPin className="w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Enter your location"
                    value={location?.address || ''}
                    readOnly
                    onClick={() => setShowLocationPicker(true)}
                    className="flex-1 outline-none text-gray-900 cursor-pointer"
                  />
                  <button
                    onClick={() => setShowSavedLocations(!showSavedLocations)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <ChevronDown className="w-5 h-5" />
                  </button>
                </div>
                
                {/* Saved Locations Dropdown */}
                {showSavedLocations && savedLocations && savedLocations.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg z-10">
                    {savedLocations.map((loc: any) => (
                      <button
                        key={loc.id}
                        onClick={() => handleSavedLocationSelect(loc)}
                        className="w-full text-left px-4 py-3 hover:bg-gray-50 border-b last:border-0"
                      >
                        <div className="font-medium text-gray-900">{loc.label}</div>
                        <div className="text-sm text-gray-600">{loc.address}</div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="flex-1 relative flex items-center gap-2 px-4 border-l">
                <Search className="w-5 h-5 text-gray-400" />
                <input
                  ref={searchInputRef}
                  type="text"
                  placeholder="Search for food, restaurants, dishes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  onFocus={() => {
                    // Show suggestions on focus
                  }}
                  className="flex-1 outline-none text-gray-900"
                />
                <SearchSuggestions
                  query={searchQuery}
                  onSelect={(query) => {
                    setSearchQuery(query)
                    handleSearch(query)
                  }}
                  onVoiceSearch={() => {
                    // Voice search handled in component
                  }}
                />
              </div>
              <Button onClick={() => handleSearch()}>Search</Button>
            </div>
            
            <div className="mt-4 flex gap-2 justify-center">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowLocationPicker(true)}
                className="bg-white/10 text-white border-white/20 hover:bg-white/20"
              >
                <Navigation className="w-4 h-4 mr-2" />
                Pick on Map
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Location Picker Modal */}
      {showLocationPicker && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold">Select Location</h2>
                <Button variant="ghost" onClick={() => setShowLocationPicker(false)}>×</Button>
              </div>
              <LocationPicker
                onLocationSelect={handleLocationSelect}
                initialLocation={location ? { lat: location.lat, lng: location.lng } : undefined}
                showSavedLocations={isAuthenticated}
              />
            </div>
          </div>
        </div>
      )}

        {/* Trending Dishes Section */}
        <section className="py-16 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-2 mb-8">
              <TrendingUp className="w-6 h-6 text-primary-600" />
              <h2 className="text-3xl font-bold">Trending Dishes</h2>
            </div>
            {trendingLoading ? (
              <SkeletonLoader variant="list" count={4} />
            ) : trendingDishes && trendingDishes.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {trendingDishes.map((dish: any) => (
                  <Card
                    key={dish.id}
                    className="cursor-pointer hover:shadow-lg transition-all duration-300 hover:scale-105"
                    onClick={() => navigate(`/restaurants/${dish.restaurant || dish.category?.menu?.restaurant}`)}
                  >
                    <CardContent className="p-0">
                      {dish.image_url && (
                        <img
                          src={dish.image_url}
                          alt={dish.name}
                          className="w-full h-48 object-cover rounded-t-lg"
                        />
                      )}
                      <div className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className="font-semibold text-lg flex-1">{dish.name}</h3>
                          {dish.is_featured && (
                            <Badge variant="outline" className="bg-yellow-50 text-yellow-700 text-xs">
                              Hot
                            </Badge>
                          )}
                        </div>
                        {dish.restaurant_name && (
                          <p className="text-sm text-gray-600 mb-2">{dish.restaurant_name}</p>
                        )}
                        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{dish.description}</p>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-lg">{formatCurrency(dish.price, 'INR')}</span>
                            {dish.calories && (
                              <span className="text-xs text-gray-500">{dish.calories} cal</span>
                            )}
                          </div>
                          <div className="flex items-center gap-1">
                            <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                            <span className="text-sm">{parseFloat(dish.rating || 0).toFixed(1)}</span>
                          </div>
                        </div>
                        <Button
                          size="sm"
                          className="w-full mt-3"
                          onClick={(e) => {
                            e.stopPropagation()
                            addItem(dish, [], dish.restaurant || dish.category?.menu?.restaurant)
                            alert('Added to cart!')
                          }}
                        >
                          <ShoppingCart className="w-4 h-4 mr-2" />
                          Add to Cart
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <p className="text-center text-gray-600">No trending dishes available</p>
            )}
          </div>
        </section>

        {/* Features Section */}
        <section className="py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="w-8 h-8 text-primary-600" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Search</h3>
                <p className="text-gray-600">Find your favorite restaurants and cuisines</p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <MapPin className="w-8 h-8 text-primary-600" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Order</h3>
                <p className="text-gray-600">Place your order with just a few clicks</p>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="w-8 h-8 text-primary-600" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Track</h3>
                <p className="text-gray-600">Track your order in real-time</p>
              </div>
            </div>
          </div>
        </section>

      {/* CTA Section */}
      <section className="bg-gray-100 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to order?</h2>
          <p className="text-gray-600 mb-8">Browse our selection of restaurants</p>
          <Link to="/restaurants">
            <Button size="lg">Browse Restaurants</Button>
          </Link>
        </div>
      </section>
      </div>
    </PullToRefresh>
  )
}
