import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import apiClient from '@/packages/api/client'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Star, Clock, MapPin, Filter } from 'lucide-react'
import { formatCurrency } from '@/packages/utils/format'
import RestaurantFilters from '../components/RestaurantFilters'

const RESTAURANT_PLACEHOLDER_IMAGE =
  'https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?auto=format&fit=crop&w=900&q=80'

interface FilterState {
  cuisines: string[]
  minRating: number | null
  maxRating: number | null
  maxDeliveryTime: number | null
  vegOnly: boolean
  pureVeg: boolean
  hasOffers: boolean
  minCost: number | null
  maxCost: number | null
  minHygiene: number | null
  sortBy: string
}

export default function RestaurantsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState<FilterState>({
    cuisines: [],
    minRating: null,
    maxRating: null,
    maxDeliveryTime: null,
    vegOnly: false,
    pureVeg: false,
    hasOffers: false,
    minCost: null,
    maxCost: null,
    minHygiene: null,
    sortBy: searchParams.get('ordering') || 'relevance',
  })

  // Build query params from filters
  const buildQueryParams = () => {
    const params: Record<string, string> = {}
    
    if (searchParams.get('search')) {
      params.search = searchParams.get('search')!
    }
    
    if (filters.cuisines.length > 0) {
      params.cuisines = filters.cuisines.join(',')
    }
    
    if (filters.minRating !== null) {
      params.min_rating = filters.minRating.toString()
    }
    
    if (filters.maxRating !== null) {
      params.max_rating = filters.maxRating.toString()
    }
    
    if (filters.maxDeliveryTime !== null) {
      params.max_delivery_time = filters.maxDeliveryTime.toString()
    }
    
    if (filters.vegOnly) {
      params.veg_only = 'true'
    }
    
    if (filters.pureVeg) {
      params.pure_veg = 'true'
    }
    
    if (filters.hasOffers) {
      params.has_offers = 'true'
    }
    
    if (filters.minCost !== null) {
      params.min_cost = filters.minCost.toString()
    }
    
    if (filters.maxCost !== null) {
      params.max_cost = filters.maxCost.toString()
    }
    
    if (filters.minHygiene !== null) {
      params.min_hygiene = filters.minHygiene.toString()
    }
    
    if (filters.sortBy && filters.sortBy !== 'relevance') {
      params.ordering = filters.sortBy
    }
    
    return params
  }

  const { data: restaurants, isLoading, error } = useQuery({
    queryKey: ['restaurants', buildQueryParams()],
    queryFn: async () => {
      const params = buildQueryParams()
      const queryString = new URLSearchParams(params).toString()
      const url = queryString ? `/restaurants/restaurants/?${queryString}` : '/restaurants/restaurants/'
      const response = await apiClient.get(url)
      return response.data.results || response.data || []
    },
  })

  const handleFiltersChange = (newFilters: FilterState) => {
    setFilters(newFilters)
    // Update URL params
    const params = buildQueryParams()
    setSearchParams(params, { replace: true })
  }

  const activeFiltersCount = 
    filters.cuisines.length +
    (filters.minRating !== null ? 1 : 0) +
    (filters.maxRating !== null ? 1 : 0) +
    (filters.maxDeliveryTime !== null ? 1 : 0) +
    (filters.vegOnly ? 1 : 0) +
    (filters.pureVeg ? 1 : 0) +
    (filters.hasOffers ? 1 : 0) +
    (filters.minCost !== null ? 1 : 0) +
    (filters.maxCost !== null ? 1 : 0) +
    (filters.minHygiene !== null ? 1 : 0)

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <Skeleton className="h-48 w-full" />
              <CardContent className="p-4">
                <Skeleton className="h-6 w-3/4 mb-2" />
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h1 className="text-3xl font-bold mb-8">Restaurants</h1>
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          Failed to load restaurants. Please try again later.
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">
          {searchParams.get('search') ? `Search Results for "${searchParams.get('search')}"` : 'Restaurants'}
        </h1>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            Filters
            {activeFiltersCount > 0 && (
              <span className="bg-primary-600 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs">
                {activeFiltersCount}
              </span>
            )}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Filters Sidebar */}
        {(showFilters || activeFiltersCount > 0) && (
          <div className="lg:col-span-1">
            <RestaurantFilters
              filters={filters}
              onFiltersChange={handleFiltersChange}
              onClose={() => setShowFilters(false)}
            />
          </div>
        )}

        {/* Restaurants Grid */}
        <div className={showFilters || activeFiltersCount > 0 ? 'lg:col-span-3' : 'lg:col-span-4'}>
          {!restaurants || restaurants.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg mb-4">
                {searchParams.get('search') 
                  ? `No restaurants found for "${searchParams.get('search')}"` 
                  : 'No restaurants found.'}
              </p>
              {activeFiltersCount > 0 && (
                <Button variant="outline" onClick={() => handleFiltersChange({
                  cuisines: [],
                  minRating: null,
                  maxRating: null,
                  maxDeliveryTime: null,
                  vegOnly: false,
                  pureVeg: false,
                  hasOffers: false,
                  minCost: null,
                  maxCost: null,
                  minHygiene: null,
                  sortBy: 'relevance',
                })}>
                  Clear All Filters
                </Button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {restaurants.map((restaurant: any) => {
                const ratingValue =
                  typeof restaurant.rating === 'number'
                    ? restaurant.rating
                    : restaurant.rating
                    ? parseFloat(restaurant.rating)
                    : 0
                const ratingDisplay = Number.isFinite(ratingValue) ? ratingValue.toFixed(1) : 'N/A'
                const coverImage = restaurant.cover_image || restaurant.hero_image_url || RESTAURANT_PLACEHOLDER_IMAGE

                return (
                  <Link key={restaurant.id} to={`/restaurants/${restaurant.id}`}>
                    <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                      {coverImage && (
                        <img
                          src={coverImage}
                          alt={restaurant.name}
                          className="w-full h-48 object-cover rounded-t-lg"
                        />
                      )}
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="text-xl font-semibold">{restaurant.name}</h3>
                          {restaurant.is_pure_veg && (
                            <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">Pure Veg</span>
                          )}
                        </div>
                        <p className="text-gray-600 text-sm mb-3">{restaurant.cuisine_type}</p>
                        
                        <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                          <div className="flex items-center gap-1">
                            <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                            <span>{ratingDisplay}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            <span>{restaurant.delivery_time_minutes} min</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <MapPin className="w-4 h-4" />
                            <span>{restaurant.city}</span>
                          </div>
                        </div>
                        
                        <div className="pt-3 border-t flex justify-between items-center">
                          <span className="text-sm font-medium">
                            Delivery: {formatCurrency(restaurant.delivery_fee, 'INR')}
                          </span>
                          {restaurant.cost_for_two && (
                            <span className="text-sm text-gray-600">
                              ₹{restaurant.cost_for_two} for two
                            </span>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
