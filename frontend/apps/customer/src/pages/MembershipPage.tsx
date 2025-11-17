import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Badge } from '@/packages/ui/components/badge'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Crown, Check, Star, Zap, Gift, Shield } from 'lucide-react'
import apiClient from '@/packages/api/client'
import { formatCurrency } from '@/packages/utils/format'
import { useAuthStore } from '../stores/authStore'

const benefitIcons: Record<string, any> = {
  free_delivery: Gift,
  discount_percentage: Star,
  priority_support: Shield,
  exclusive_offers: Crown,
  cashback_percentage: Zap,
}

export default function MembershipPage() {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()

  const { data: plans, isLoading: plansLoading } = useQuery({
    queryKey: ['membership-plans'],
    queryFn: async () => {
      const response = await apiClient.get('/subscriptions/plans/')
      return response.data.results || response.data || []
    },
  })

  const { data: currentSubscription } = useQuery({
    queryKey: ['current-subscription'],
    queryFn: async () => {
      const response = await apiClient.get('/subscriptions/subscriptions/current/')
      return response.data
    },
    enabled: !!user,
  })

  const subscribeMutation = useMutation({
    mutationFn: async (planId: number) => {
      // In production, create payment intent first
      const response = await apiClient.post('/subscriptions/subscriptions/subscribe/', {
        plan_id: planId,
        payment_transaction_id: `TXN_${Date.now()}`, // Mock transaction ID
        auto_renew: true,
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-subscription'] })
      queryClient.invalidateQueries({ queryKey: ['membership-plans'] })
      alert('Subscription activated successfully!')
    },
  })

  const cancelMutation = useMutation({
    mutationFn: async (subscriptionId: number) => {
      const response = await apiClient.post(`/subscriptions/subscriptions/${subscriptionId}/cancel/`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-subscription'] })
      alert('Subscription cancelled successfully')
    },
  })

  if (plansLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Membership Plans</h1>

      {/* Current Subscription */}
      {currentSubscription && (
        <Card className="mb-8 border-primary-300 bg-primary-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Crown className="w-5 h-5 text-primary-600" />
              Your Active Subscription
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-semibold mb-1">{currentSubscription.plan.name}</h3>
                <p className="text-gray-600">
                  {currentSubscription.plan.plan_type} Plan
                </p>
                {currentSubscription.end_date && (
                  <p className="text-sm text-gray-500 mt-1">
                    Expires: {new Date(currentSubscription.end_date).toLocaleDateString()}
                  </p>
                )}
                {currentSubscription.auto_renew && (
                  <Badge className="mt-2">Auto-renew enabled</Badge>
                )}
              </div>
              <Button
                variant="outline"
                onClick={() => cancelMutation.mutate(currentSubscription.id)}
                disabled={cancelMutation.isPending}
              >
                Cancel Subscription
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Available Plans */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plans && plans.length > 0 ? (
          plans.map((plan: any) => {
            const isSubscribed = plan.is_subscribed || false
            const isCurrentPlan = currentSubscription?.plan?.id === plan.id
            
            return (
              <Card
                key={plan.id}
                className={`relative ${plan.is_featured ? 'border-primary-500 border-2' : ''} ${
                  isCurrentPlan ? 'opacity-75' : ''
                }`}
              >
                {plan.is_featured && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-primary-600">Most Popular</Badge>
                  </div>
                )}
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Crown className="w-5 h-5" />
                    {plan.name}
                  </CardTitle>
                  <div className="mt-4">
                    <div className="text-3xl font-bold">
                      {formatCurrency(plan.price, plan.currency)}
                    </div>
                    <div className="text-sm text-gray-600">
                      {plan.plan_type === 'MONTHLY' && '/month'}
                      {plan.plan_type === 'YEARLY' && '/year'}
                      {plan.plan_type === 'LIFETIME' && ' one-time'}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-6">{plan.description}</p>
                  
                  {/* Benefits */}
                  <div className="space-y-3 mb-6">
                    {plan.benefits && Object.entries(plan.benefits).map(([key, value]: [string, any]) => {
                      if (!value) return null
                      const IconComponent = benefitIcons[key] || Check
                      return (
                        <div key={key} className="flex items-center gap-2">
                          <IconComponent className="w-4 h-4 text-green-600" />
                          <span className="text-sm">
                            {key === 'free_delivery' && value && 'Free delivery on all orders'}
                            {key === 'discount_percentage' && value && `${value}% discount on all orders`}
                            {key === 'priority_support' && value && 'Priority customer support'}
                            {key === 'exclusive_offers' && value && 'Exclusive offers and deals'}
                            {key === 'cashback_percentage' && value && `${value}% cashback on orders`}
                            {key === 'max_free_deliveries_per_month' && value && `${value} free deliveries per month`}
                          </span>
                        </div>
                      )
                    })}
                  </div>

                  {isCurrentPlan ? (
                    <Button className="w-full" disabled>
                      Current Plan
                    </Button>
                  ) : isSubscribed ? (
                    <Button variant="outline" className="w-full" disabled>
                      Already Subscribed
                    </Button>
                  ) : (
                    <Button
                      className="w-full"
                      onClick={() => subscribeMutation.mutate(plan.id)}
                      disabled={subscribeMutation.isPending}
                    >
                      {subscribeMutation.isPending ? 'Processing...' : 'Subscribe Now'}
                    </Button>
                  )}
                </CardContent>
              </Card>
            )
          })
        ) : (
          <div className="col-span-3 text-center py-12">
            <p className="text-gray-600">No membership plans available</p>
          </div>
        )}
      </div>
    </div>
  )
}

