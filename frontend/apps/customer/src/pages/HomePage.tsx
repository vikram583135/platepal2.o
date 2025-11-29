
import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/packages/ui/components/button'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Badge } from '@/packages/ui/components/badge'
import { Search, MapPin, Navigation, ChevronDown, TrendingUp, Star, ShoppingCart, ArrowRight } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import LocationPicker from '../components/LocationPicker'
import SearchSuggestions from '../components/SearchSuggestions'
import { useAuthStore } from '../stores/authStore'
import { useCartStore } from '../stores/cartStore'
import { formatCurrency } from '@/packages/utils/format'
import SkeletonLoader from '../components/SkeletonLoader'
import PullToRefresh from '../components/PullToRefresh'

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
              address: `${response.data.address}, ${response.data.city} `,
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
      // Save search (non-blocking)
      apiClient.post('/restaurants/search/save/', {
        query: q.trim(),
        type: 'general',
      }).catch(() => { }) // Ignore errors for better UX

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
    navigate(`/ restaurants ? lat = ${savedLoc.latitude}& lng=${savedLoc.longitude} `)
  }

  const handleRefresh = async () => {
    await refetchTrending()
  }

  return (
    <PullToRefresh onRefresh={handleRefresh}>
      <div className="min-h-screen page-background pb-20">
        {/* Hero Section */}
        <section className="relative overflow-hidden bg-gradient-to-r from-zomato-red to-zomato-darkRed pb-32 pt-20 lg:pt-32">
          <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&q=80')] bg-cover bg-center opacity-10" />
          <div className="absolute inset-0 bg-gradient-to-b from-transparent to-background" />

          <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
            <h1 className="mb-6 text-4xl font-bold tracking-tight text-primary-foreground sm:text-6xl animate-fade-in">
              Delicious Food,<br />
              <span className="text-white/90">Delivered to You.</span>
            </h1>
            <p className="mb-10 text-lg text-primary-foreground/80 sm:text-xl animate-slide-up">
              Discover the best restaurants and cuisines in your area.
            </p>

            <div className="mx-auto max-w-3xl animate-slide-up" style={{ animationDelay: '0.1s' }}>
              <div className="flex flex-col gap-2 rounded-xl bg-card/95 p-2 shadow-2xl backdrop-blur-sm sm:flex-row">
                <div className="relative flex-1">
                  <div className="flex h-12 items-center gap-3 rounded-lg bg-muted/50 px-4 transition-colors hover:bg-muted/80">
                    <MapPin className="h-5 w-5 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Enter your location"
                      value={location?.address || 'Detecting location...'}
                      readOnly
                      onClick={() => setShowLocationPicker(true)}
                      className="flex-1 bg-transparent text-sm font-medium outline-none placeholder:text-muted-foreground cursor-pointer"
                    />
                    <button
                      onClick={() => setShowSavedLocations(!showSavedLocations)}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <ChevronDown className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Saved Locations Dropdown */}
                  {showSavedLocations && savedLocations && savedLocations.length > 0 && (
                    <div className="absolute left-0 right-0 top-full z-20 mt-2 divide-y rounded-lg border bg-popover shadow-lg animate-in fade-in zoom-in-95">
                      {savedLocations.map((loc: any) => (
                        <button
                          key={loc.id}
                          onClick={() => handleSavedLocationSelect(loc)}
                          className="flex w-full flex-col px-4 py-3 text-left hover:bg-accent transition-colors first:rounded-t-lg last:rounded-b-lg"
                        >
                          <span className="font-medium">{loc.label}</span>
                          <span className="text-xs text-muted-foreground">{loc.address}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                <div className="relative flex-[1.5]">
                  <div className="flex h-12 items-center gap-3 rounded-lg bg-muted/50 px-4 transition-colors hover:bg-muted/80">
                    <Search className="h-5 w-5 text-muted-foreground" />
                    <input
                      ref={searchInputRef}
                      type="text"
                      placeholder="Search for food, restaurants..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                      className="flex-1 bg-transparent text-sm font-medium outline-none placeholder:text-muted-foreground"
                    />
                    <SearchSuggestions
                      query={searchQuery}
                      onSelect={(query) => {
                        setSearchQuery(query)
                        handleSearch(query)
                      }}
                      onVoiceSearch={() => { }}
                    />
                  </div>
                </div>

                <Button size="lg" onClick={() => handleSearch()} className="h-12 px-8 text-base shadow-lg">
                  Search
                </Button>
              </div>

              <div className="mt-6 flex justify-center gap-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowLocationPicker(true)}
                  className="border-primary-foreground/20 bg-primary-foreground/10 text-primary-foreground hover:bg-primary-foreground/20 backdrop-blur-sm"
                >
                  <Navigation className="mr-2 h-4 w-4" />
                  Use Current Location
                </Button>
              </div>
            </div>
          </div>
        </section>

        {/* Location Picker Modal */}
        {showLocationPicker && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm animate-in fade-in">
            <div className="w-full max-w-2xl overflow-hidden rounded-xl bg-background shadow-2xl animate-in zoom-in-95">
              <div className="flex items-center justify-between border-b p-4">
                <h2 className="text-lg font-semibold">Select Location</h2>
                <Button variant="ghost" size="icon" onClick={() => setShowLocationPicker(false)}>×</Button>
              </div>
              <div className="max-h-[80vh] overflow-y-auto p-4">
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
        <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="mb-8 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                <TrendingUp className="h-5 w-5 text-primary" />
              </div>
              <h2 className="text-2xl font-bold tracking-tight">Trending Now</h2>
            </div>
            <Link to="/restaurants" className="group flex items-center text-sm font-medium text-primary hover:text-primary/80">
              View all <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
          </div>

          {trendingLoading ? (
            <SkeletonLoader variant="list" count={4} />
          ) : trendingDishes && trendingDishes.length > 0 ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {trendingDishes.map((dish: any) => (
                <Card
                  key={dish.id}
                  className="group cursor-pointer overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-xl border-border/50"
                  onClick={() => navigate(`/ restaurants / ${dish.restaurant || dish.category?.menu?.restaurant} `)}
                >
                  <CardContent className="p-0">
                    <div className="relative aspect-[4/3] overflow-hidden">
                      {dish.image_url ? (
                        <img
                          src={dish.image_url}
                          alt={dish.name}
                          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                        />
                      ) : (
                        <div className="h-full w-full bg-muted flex items-center justify-center">
                          <span className="text-muted-foreground">No Image</span>
                        </div>
                      )}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />
                      {dish.is_featured && (
                        <Badge className="absolute left-3 top-3 bg-yellow-500 hover:bg-yellow-600 border-none shadow-lg">
                          Featured
                        </Badge>
                      )}
                      <div className="absolute bottom-3 right-3 translate-y-4 opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100">
                        <Button
                          size="sm"
                          className="h-8 w-8 rounded-full p-0 shadow-lg"
                          onClick={(e) => {
                            e.stopPropagation()
                            addItem(dish, [], dish.restaurant || dish.category?.menu?.restaurant)
                          }}
                        >
                          <ShoppingCart className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    <div className="p-4">
                      <div className="mb-2 flex items-start justify-between gap-2">
                        <h3 className="font-semibold leading-tight line-clamp-1 group-hover:text-primary transition-colors">
                          {dish.name}
                        </h3>
                        <div className="flex items-center gap-1 rounded-md bg-green-50 px-1.5 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/20 dark:text-green-400">
                          <Star className="h-3 w-3 fill-current" />
                          {parseFloat(dish.rating || 0).toFixed(1)}
                        </div>
                      </div>

                      {dish.restaurant_name && (
                        <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                          {dish.restaurant_name}
                        </p>
                      )}

                      <p className="mb-4 line-clamp-2 text-sm text-muted-foreground">
                        {dish.description}
                      </p>

                      <div className="flex items-center justify-between border-t pt-3">
                        <div className="flex items-baseline gap-1">
                          <span className="text-lg font-bold text-primary">
                            {formatCurrency(dish.price, 'INR')}
                          </span>
                          {dish.calories && (
                            <span className="text-xs text-muted-foreground">
                              / {dish.calories} cal
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-muted py-20 text-center">
              <div className="mb-4 rounded-full bg-muted p-4">
                <TrendingUp className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold">No trending dishes yet</h3>
              <p className="text-muted-foreground">Check back later for popular items</p>
            </div>
          )}
        </section>

        {/* Features Section */}
        <section className="bg-muted/30 py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid gap-8 md:grid-cols-3">
              {[
                { icon: Search, title: 'Search', desc: 'Find your favorite restaurants and cuisines' },
                { icon: MapPin, title: 'Order', desc: 'Place your order with just a few clicks' },
                { icon: Navigation, title: 'Track', desc: 'Track your order in real-time' },
              ].map((feature, i) => (
                <div key={i} className="group relative overflow-hidden rounded-2xl bg-background p-8 text-center shadow-sm transition-all hover:shadow-md hover:-translate-y-1">
                  <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                    <feature.icon className="h-8 w-8 text-primary transition-colors group-hover:text-primary-foreground" />
                  </div>
                  <h3 className="mb-3 text-xl font-semibold">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="relative overflow-hidden py-24">
          <div className="absolute inset-0 bg-primary" />
          <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&q=80')] bg-cover bg-center opacity-10 mix-blend-overlay" />
          <div className="relative mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">
            <h2 className="mb-6 text-3xl font-bold text-primary-foreground sm:text-4xl">
              Ready to satisfy your cravings?
            </h2>
            <p className="mb-10 text-lg text-primary-foreground/80">
              Explore thousands of restaurants and get food delivered to your doorstep.
            </p>
            <Link to="/restaurants">
              <Button size="lg" variant="secondary" className="h-14 px-8 text-lg shadow-xl transition-transform hover:scale-105">
                Browse Restaurants
              </Button>
            </Link>
          </div>
        </section>
      </div>
    </PullToRefresh>
  )
}

