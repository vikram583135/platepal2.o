import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Badge } from '@/packages/ui/components/badge'
import * as formatUtils from '@/packages/utils/format'
import { cn } from '@/packages/utils/cn'

interface DeliveryOffer {
  id: number
  delivery: {
    id: number
    order: {
      order_number: string
      total_amount: number
    }
    pickup_address: string
    delivery_address: string
    pickup_latitude: number
    pickup_longitude: number
    delivery_latitude: number
    delivery_longitude: number
    estimated_distance_km: number
    estimated_travel_time_minutes: number
    base_fee: number
    distance_fee: number
    tip_amount: number
    total_earnings: number
    surge_multiplier: number
  }
  status: string
  expires_at: string
  created_at: string
  time_remaining_seconds: number
  is_expired: boolean
}

export default function OffersPage() {
  const queryClient = useQueryClient()
  const [countdowns, setCountdowns] = useState<Record<number, number>>({})

  // Fetch nearby offers
  const { data: offers, isLoading } = useQuery({
    queryKey: ['delivery-offers'],
    queryFn: async () => {
      const response = await apiClient.get('/deliveries/offers/nearby/')
      return (response.data.results || response.data) as DeliveryOffer[]
    },
    refetchInterval: 5000, // Refetch every 5 seconds
  })

  // Auto-accept rules
  const { data: autoAcceptRules } = useQuery({
    queryKey: ['auto-accept-rules'],
    queryFn: async () => {
      const response = await apiClient.get('/deliveries/auto-accept-rules/')
      return response.data.results || response.data
    },
  })

  // Accept offer mutation
  const acceptMutation = useMutation({
    mutationFn: async (offerId: number) => {
      const response = await apiClient.post(`/deliveries/offers/${offerId}/accept/`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['delivery-offers'] })
      queryClient.invalidateQueries({ queryKey: ['deliveries'] })
    },
  })

  // Decline offer mutation
  const declineMutation = useMutation({
    mutationFn: async (offerId: number) => {
      const response = await apiClient.post(`/deliveries/offers/${offerId}/decline/`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['delivery-offers'] })
    },
  })

  // Update countdown timers
  useEffect(() => {
    if (!offers) return

    const interval = setInterval(() => {
      const newCountdowns: Record<number, number> = {}
      offers.forEach((offer) => {
        if (!offer.is_expired && offer.expires_at) {
          const remaining = Math.max(0, Math.floor((new Date(offer.expires_at).getTime() - Date.now()) / 1000))
          newCountdowns[offer.id] = remaining
        }
      })
      setCountdowns(newCountdowns)
    }, 1000)

    return () => clearInterval(interval)
  }, [offers])

  const formatCountdown = (seconds: number) => {
    if (seconds <= 0) return 'Expired'
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading offers...</p>
        </div>
      </div>
    )
  }

  const activeOffers = offers?.filter((offer) => !offer.is_expired && offer.status === 'PENDING') || []
  const expiredOffers = offers?.filter((offer) => offer.is_expired || offer.status !== 'PENDING') || []

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Delivery Offers</h1>
        <Badge variant="default" className="bg-green-100 text-green-800">
          {activeOffers.length} Active Offers
        </Badge>
      </div>

      {/* Auto-Accept Rules */}
      {autoAcceptRules && autoAcceptRules.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Auto-Accept Rules</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {autoAcceptRules.map((rule: any) => (
                <div key={rule.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium">
                      Min Earnings: {formatUtils.formatCurrency(rule.min_earnings || 0, 'INR')}
                    </p>
                    <p className="text-sm text-gray-600">
                      Max Distance: {rule.max_distance_km || '∞'} km
                    </p>
                  </div>
                  <Badge variant={rule.is_active ? 'default' : 'outline'}>
                    {rule.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Offers */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Available Offers</h2>
        {activeOffers.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <div className="text-4xl mb-4">📦</div>
              <p className="text-gray-600">No offers available at the moment</p>
              <p className="text-sm text-gray-500 mt-2">
                Make sure you're on shift and in an active area
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeOffers.map((offer) => {
              const remaining = countdowns[offer.id] ?? offer.time_remaining_seconds ?? 0
              const isExpiring = remaining < 30 && remaining > 0
              const hasSurge = (offer.delivery.surge_multiplier || 1) > 1

              return (
                <Card
                  key={offer.id}
                  className={cn(
                    'transition-all hover:shadow-lg',
                    isExpiring && 'ring-2 ring-red-500',
                    hasSurge && 'ring-2 ring-orange-500'
                  )}
                >
                  <CardHeader>
                    <div className="flex justify-between items-start mb-2">
                      <CardTitle className="text-lg font-semibold">
                        Order #{offer.delivery.order.order_number}
                      </CardTitle>
                      {hasSurge && (
                        <Badge variant="default" className="bg-orange-100 text-orange-800">
                          {offer.delivery.surge_multiplier}x Surge
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge
                        variant={isExpiring ? 'destructive' : 'default'}
                        className={cn(isExpiring && 'animate-pulse')}
                      >
                        {formatCountdown(remaining)}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-1">Pickup</p>
                      <p className="text-sm text-gray-600">{offer.delivery.pickup_address}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-1">Delivery</p>
                      <p className="text-sm text-gray-600">{offer.delivery.delivery_address}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                      <div>
                        <p className="text-xs text-gray-500">Distance</p>
                        <p className="font-semibold">
                          {offer.delivery.estimated_distance_km?.toFixed(1) || 'N/A'} km
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Time</p>
                        <p className="font-semibold">
                          {offer.delivery.estimated_travel_time_minutes || 'N/A'} min
                        </p>
                      </div>
                    </div>

                    <div className="pt-4 border-t">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-sm text-gray-600">Total Earnings</span>
                        <span className="text-2xl font-bold text-green-600">
                          {formatUtils.formatCurrency(offer.delivery.total_earnings || 0, 'INR')}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 space-y-1">
                        <div className="flex justify-between">
                          <span>Base Fee:</span>
                          <span>{formatUtils.formatCurrency(offer.delivery.base_fee || 0, 'INR')}</span>
                        </div>
                        {offer.delivery.distance_fee > 0 && (
                          <div className="flex justify-between">
                            <span>Distance Fee:</span>
                            <span>{formatUtils.formatCurrency(offer.delivery.distance_fee || 0, 'INR')}</span>
                          </div>
                        )}
                        {offer.delivery.tip_amount > 0 && (
                          <div className="flex justify-between">
                            <span>Tip:</span>
                            <span>{formatUtils.formatCurrency(offer.delivery.tip_amount || 0, 'INR')}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex space-x-2 pt-4">
                      <Button
                        onClick={() => acceptMutation.mutate(offer.id)}
                        disabled={acceptMutation.isPending || remaining <= 0}
                        className="flex-1 bg-green-600 hover:bg-green-700"
                      >
                        {acceptMutation.isPending ? 'Accepting...' : 'Accept'}
                      </Button>
                      <Button
                        onClick={() => declineMutation.mutate(offer.id)}
                        disabled={declineMutation.isPending || remaining <= 0}
                        variant="outline"
                        className="flex-1"
                      >
                        Decline
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </div>

      {/* Expired/Completed Offers */}
      {expiredOffers.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold mb-4">Recent Offers</h2>
          <div className="space-y-2">
            {expiredOffers.slice(0, 5).map((offer) => (
              <Card key={offer.id} className="opacity-60">
                <CardContent className="p-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="font-medium">Order #{offer.delivery.order.order_number}</p>
                      <p className="text-sm text-gray-600">
                        {formatUtils.formatCurrency(offer.delivery.total_earnings || 0, 'INR')}
                      </p>
                    </div>
                    <Badge variant="outline">
                      {offer.status === 'ACCEPTED'
                        ? 'Accepted'
                        : offer.status === 'DECLINED'
                        ? 'Declined'
                        : 'Expired'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

