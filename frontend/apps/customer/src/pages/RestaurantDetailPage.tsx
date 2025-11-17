import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { useCartStore } from '../stores/cartStore'
import { Button } from '@/packages/ui/components/button'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Badge } from '@/packages/ui/components/badge'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Star, Clock, ShoppingCart, MapPin, Shield, Award, Tag, Info, TrendingUp, Sparkles } from 'lucide-react'
import { formatCurrency } from '@/packages/utils/format'
import MenuSearch from '../components/MenuSearch'
import ItemDetailModal from '../components/ItemDetailModal'
import ReviewCard from '../components/ReviewCard'
import { MenuCache, RestaurantCache } from '../utils/cache'
import { useOffline } from '../hooks/useOffline'

const RESTAURANT_PLACEHOLDER_IMAGE =
  'https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?auto=format&fit=crop&w=1200&q=80'

export default function RestaurantDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { addItem } = useCartStore()
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [showItemModal, setShowItemModal] = useState(false)

  const isOffline = useOffline()

  const { data: restaurant, isLoading } = useQuery({
    queryKey: ['restaurant', id],
    queryFn: async () => {
      // Try cache first if offline
      if (isOffline && id) {
        const cached = RestaurantCache.get(Number(id))
        if (cached) return cached
      }
      
      const response = await apiClient.get(`/restaurants/restaurants/${id}/`)
      const data = response.data
      
      // Cache the restaurant data
      if (id) {
        RestaurantCache.set(Number(id), data)
      }
      
      return data
    },
  })

  const { data: menu, isLoading: menuLoading } = useQuery({
    queryKey: ['restaurant-menu', id],
    queryFn: async () => {
      // Try cache first if offline
      if (isOffline && id) {
        const cached = MenuCache.get(Number(id))
        if (cached) return cached
      }
      
      const response = await apiClient.get(`/restaurants/restaurants/${id}/menu/`)
      const data = response.data
      
      // Cache the menu data
      if (id) {
        MenuCache.set(Number(id), data)
      }
      
      return data
    },
    enabled: !!id,
  })

  const { data: bestsellers } = useQuery({
    queryKey: ['bestsellers', id],
    queryFn: async () => {
      const response = await apiClient.get(`/restaurants/restaurants/${id}/bestsellers/`)
      return response.data.items || []
    },
    enabled: !!id,
  })

  const { data: recommendations } = useQuery({
    queryKey: ['recommendations', id],
    queryFn: async () => {
      const response = await apiClient.get(`/restaurants/restaurants/${id}/recommendations/`)
      return response.data.items || []
    },
    enabled: !!id,
  })

  const { data: reviews } = useQuery({
    queryKey: ['reviews', id],
    queryFn: async () => {
      const response = await apiClient.get(`/orders/reviews/?restaurant_id=${id}`)
      return response.data.results || response.data || []
    },
    enabled: !!id,
  })

  const handleItemClick = (item: any) => {
    setSelectedItem(item)
    setShowItemModal(true)
  }

  const handleAddToCart = (item: any, modifiers: any[], quantity: number) => {
    for (let i = 0; i < quantity; i++) {
      addItem(item, modifiers, restaurant?.id)
    }
  }

  if (isLoading || menuLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Skeleton className="h-64 w-full mb-8" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  const getNumericValue = (value: number | string | undefined) => {
    if (typeof value === 'number') return value
    if (typeof value === 'string') {
      const parsed = parseFloat(value)
      if (!Number.isNaN(parsed)) return parsed
    }
    return 0
  }

  const formatOpeningHours = (hours: any) => {
    if (!hours || typeof hours !== 'object') return 'Hours not available'
    
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    const today = new Date().toLocaleDateString('en-US', { weekday: 'long' })
    
    return days.map(day => {
      const dayLower = day.toLowerCase()
      const dayHours = hours[dayLower]
      if (dayHours && dayHours.open && dayHours.close) {
        const highlight = day === today ? 'font-semibold' : ''
        return (
          <div key={day} className={highlight}>
            {day}: {dayHours.open} - {dayHours.close}
          </div>
        )
      }
      return null
    }).filter(Boolean)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {restaurant && (
        <>
          {/* Enhanced Restaurant Header */}
          <div className="mb-8">
            <div className="relative h-64 md:h-80 rounded-lg overflow-hidden mb-6">
              <img
                src={restaurant.cover_image || restaurant.hero_image_url || RESTAURANT_PLACEHOLDER_IMAGE}
                alt={restaurant.name}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h1 className="text-4xl font-bold">{restaurant.name}</h1>
                      {restaurant.is_pure_veg && (
                        <Badge className="bg-green-600">Pure Veg</Badge>
                      )}
                      {restaurant.is_halal && (
                        <Badge className="bg-blue-600">Halal</Badge>
                      )}
                      {restaurant.hygiene_rating && restaurant.hygiene_rating >= 4.5 && (
                        <Badge className="bg-yellow-600 flex items-center gap-1">
                          <Shield className="w-3 h-3" />
                          Hygiene {restaurant.hygiene_rating.toFixed(1)}
                        </Badge>
                      )}
                    </div>
                    <p className="text-lg text-white/90 mb-4">{restaurant.description}</p>
                    <div className="flex flex-wrap items-center gap-4 text-sm">
                      <div className="flex items-center gap-1">
                        <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
                        <span className="font-semibold">{getNumericValue(restaurant.rating).toFixed(1)}</span>
                        <span className="text-white/80">({restaurant.total_ratings} reviews)</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-5 h-5" />
                        <span>{restaurant.delivery_time_minutes} min delivery</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <MapPin className="w-5 h-5" />
                        <span>{restaurant.city}</span>
                      </div>
                      {restaurant.cost_for_two && (
                        <div className="flex items-center gap-1">
                          <span>₹{restaurant.cost_for_two} for two</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Restaurant Details Card */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Clock className="w-5 h-5 text-primary-600" />
                    <h3 className="font-semibold">Timing</h3>
                  </div>
                  {restaurant.is_open ? (
                    <div className="text-green-600 font-medium">Open Now</div>
                  ) : (
                    <div>
                      <div className="text-red-600 font-medium mb-1">Closed</div>
                      {restaurant.next_opening_time && (
                        <div className="text-sm text-gray-600">Opens {restaurant.next_opening_time}</div>
                      )}
                    </div>
                  )}
                  <div className="mt-2 text-sm text-gray-600">
                    {formatOpeningHours(restaurant.opening_hours)}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Info className="w-5 h-5 text-primary-600" />
                    <h3 className="font-semibold">Delivery Info</h3>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Delivery Fee:</span>
                      <span className="font-medium">{formatCurrency(restaurant.delivery_fee, 'INR')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Min Order:</span>
                      <span className="font-medium">{formatCurrency(restaurant.minimum_order_amount, 'INR')}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Delivery Time:</span>
                      <span className="font-medium">{restaurant.delivery_time_minutes} min</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Award className="w-5 h-5 text-primary-600" />
                    <h3 className="font-semibold">Badges & Certifications</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {restaurant.is_pure_veg && (
                      <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
                        Pure Veg
                      </Badge>
                    )}
                    {restaurant.is_halal && (
                      <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-300">
                        Halal Certified
                      </Badge>
                    )}
                    {restaurant.hygiene_rating && (
                      <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-300">
                        <Shield className="w-3 h-3 mr-1" />
                        Hygiene {restaurant.hygiene_rating.toFixed(1)}
                      </Badge>
                    )}
                    {restaurant.kyc_verified && (
                      <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-300">
                        Verified
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Active Offers */}
            {restaurant.active_promotions && restaurant.active_promotions.length > 0 && (
              <Card className="mb-6">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Tag className="w-5 h-5 text-primary-600" />
                    <h3 className="font-semibold">Active Offers</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {restaurant.active_promotions.map((promo: any) => (
                      <div key={promo.id} className="p-3 bg-primary-50 border border-primary-200 rounded-lg">
                        <div className="font-semibold text-primary-900">{promo.name}</div>
                        <div className="text-sm text-primary-700">
                          {promo.discount_type === 'PERCENTAGE' && `${promo.discount_value}% off`}
                          {promo.discount_type === 'FIXED' && `₹${promo.discount_value} off`}
                          {promo.discount_type === 'BUY_ONE_GET_ONE' && 'Buy 1 Get 1'}
                        </div>
                        {promo.minimum_order_amount > 0 && (
                          <div className="text-xs text-primary-600 mt-1">
                            Min order: {formatCurrency(promo.minimum_order_amount, 'INR')}
                          </div>
                        )}
                        <div className="text-xs text-primary-600 mt-1">Code: {promo.code}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Menu Search */}
          <div className="mb-6">
            <MenuSearch
              restaurantId={id!}
              onItemSelect={(item) => handleItemClick(item)}
            />
          </div>

          {/* Bestsellers Section */}
          {bestsellers && bestsellers.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-6 h-6 text-primary-600" />
                <h2 className="text-2xl font-semibold">Bestsellers</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {bestsellers.map((item: any) => (
                  <Card
                    key={item.id}
                    className="cursor-pointer hover:shadow-lg transition-shadow"
                    onClick={() => handleItemClick(item)}
                  >
                    <CardContent className="p-4">
                      {item.image_url && (
                        <img
                          src={item.image_url}
                          alt={item.name}
                          className="w-full h-32 object-cover rounded mb-2"
                        />
                      )}
                      <h3 className="font-semibold mb-1">{item.name}</h3>
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">{formatCurrency(item.price, 'INR')}</span>
                        <div className="flex items-center gap-1 text-sm">
                          <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                          <span>{parseFloat(item.rating || 0).toFixed(1)}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations Section */}
          {recommendations && recommendations.length > 0 && (
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-6 h-6 text-primary-600" />
                <h2 className="text-2xl font-semibold">Recommended for You</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {recommendations.map((item: any) => (
                  <Card
                    key={item.id}
                    className="cursor-pointer hover:shadow-lg transition-shadow"
                    onClick={() => handleItemClick(item)}
                  >
                    <CardContent className="p-4">
                      {item.image_url && (
                        <img
                          src={item.image_url}
                          alt={item.name}
                          className="w-full h-32 object-cover rounded mb-2"
                        />
                      )}
                      <h3 className="font-semibold mb-1">{item.name}</h3>
                      <div className="flex items-center justify-between">
                        <span className="font-semibold">{formatCurrency(item.price, 'INR')}</span>
                        {item.is_featured && (
                          <Badge variant="outline" className="bg-yellow-50 text-yellow-700">
                            Featured
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Menu Section */}
          {menu && (
            <div className="space-y-8">
              {Array.isArray(menu) && menu.length > 0 ? (
                menu.map((category: any) => (
                  <div key={category.id} className="mb-8">
                    <h2 className="text-2xl font-semibold mb-4">{category.name}</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {category.items?.map((item: any) => {
                        const itemImage = item.image || item.image_url
                        return (
                        <Card key={item.id}>
                          <CardContent className="p-4">
                            <div className="flex gap-4">
                              {itemImage && (
                                <img
                                  src={itemImage}
                                  alt={item.name}
                                  className="w-24 h-24 object-cover rounded"
                                />
                              )}
                              <div className="flex-1">
                                <div className="flex items-start justify-between mb-1">
                                  <h3 className="font-semibold">{item.name}</h3>
                                  <div className="flex gap-1">
                                    {item.is_vegetarian && (
                                      <Badge variant="outline" className="bg-green-50 text-green-700 text-xs">
                                        Veg
                                      </Badge>
                                    )}
                                    {item.is_vegan && (
                                      <Badge variant="outline" className="bg-green-50 text-green-700 text-xs">
                                        Vegan
                                      </Badge>
                                    )}
                                    {item.is_spicy && (
                                      <Badge variant="outline" className="bg-red-50 text-red-700 text-xs">
                                        Spicy
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                                <p className="text-sm text-gray-600 mb-2">{item.description}</p>
                                {item.calories && (
                                  <div className="text-xs text-gray-500 mb-2">{item.calories} calories</div>
                                )}
                                <div className="flex items-center justify-between">
                                  <span className="font-semibold">
                                    {formatCurrency(item.price, 'INR')}
                                  </span>
                                  <Button
                                    size="sm"
                                    onClick={() => handleItemClick(item)}
                                    disabled={!item.is_available}
                                  >
                                    <ShoppingCart className="w-4 h-4 mr-1" />
                                    {item.is_available ? 'View Details' : 'Sold Out'}
                                  </Button>
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      )})}
                    </div>
                  </div>
                ))
              ) : menu.categories ? (
                menu.categories.map((category: any) => (
                  <div key={category.id} className="mb-8">
                    <h2 className="text-2xl font-semibold mb-4">{category.name}</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {category.items?.map((item: any) => {
                        const itemImage = item.image || item.image_url
                        return (
                        <Card key={item.id}>
                          <CardContent className="p-4">
                            <div className="flex gap-4">
                              {itemImage && (
                                <img
                                  src={itemImage}
                                  alt={item.name}
                                  className="w-24 h-24 object-cover rounded"
                                />
                              )}
                              <div className="flex-1">
                                <div className="flex items-start justify-between mb-1">
                                  <h3 className="font-semibold">{item.name}</h3>
                                  <div className="flex gap-1">
                                    {item.is_vegetarian && (
                                      <Badge variant="outline" className="bg-green-50 text-green-700 text-xs">
                                        Veg
                                      </Badge>
                                    )}
                                    {item.is_vegan && (
                                      <Badge variant="outline" className="bg-green-50 text-green-700 text-xs">
                                        Vegan
                                      </Badge>
                                    )}
                                    {item.is_spicy && (
                                      <Badge variant="outline" className="bg-red-50 text-red-700 text-xs">
                                        Spicy
                                      </Badge>
                                    )}
                                  </div>
                                </div>
                                <p className="text-sm text-gray-600 mb-2">{item.description}</p>
                                {item.calories && (
                                  <div className="text-xs text-gray-500 mb-2">{item.calories} calories</div>
                                )}
                                <div className="flex items-center justify-between">
                                  <span className="font-semibold">
                                    {formatCurrency(item.price, 'INR')}
                                  </span>
                                  <Button
                                    size="sm"
                                    onClick={() => handleItemClick(item)}
                                    disabled={!item.is_available}
                                  >
                                    <ShoppingCart className="w-4 h-4 mr-1" />
                                    {item.is_available ? 'View Details' : 'Sold Out'}
                                  </Button>
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      )})}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-600">No menu items available</p>
              )}
            </div>
          )}

          {/* Reviews Section */}
          {reviews && reviews.length > 0 && (
            <div className="mb-8">
              <h2 className="text-2xl font-semibold mb-4">Customer Reviews</h2>
              <div className="space-y-4">
                {reviews.slice(0, 5).map((review: any) => (
                  <ReviewCard key={review.id} review={review} />
                ))}
              </div>
              {reviews.length > 5 && (
                <Button variant="outline" className="mt-4">
                  View All Reviews ({reviews.length})
                </Button>
              )}
            </div>
          )}

          {/* Item Detail Modal */}
          {selectedItem && (
            <ItemDetailModal
              item={selectedItem}
              isOpen={showItemModal}
              onClose={() => {
                setShowItemModal(false)
                setSelectedItem(null)
              }}
              onAddToCart={handleAddToCart}
              restaurantId={restaurant.id}
            />
          )}
        </>
      )}
    </div>
  )
}
