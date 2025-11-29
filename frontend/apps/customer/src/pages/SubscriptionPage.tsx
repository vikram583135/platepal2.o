import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Badge } from '@/packages/ui/components/badge'
import { Crown, Check, X, Calendar, CreditCard, AlertCircle } from 'lucide-react'
import { cn } from '@/packages/utils/cn'

export default function SubscriptionPage() {
    const queryClient = useQueryClient()
    const [showCancelModal, setShowCancelModal] = useState(false)

    // Fetch current subscription
    const subscriptionQuery = useQuery({
        queryKey: ['current-subscription'],
        queryFn: async () => {
            try {
                const response = await apiClient.get('/subscriptions/current/')
                return response.data
            } catch (error: any) {
                if (error.response?.status === 404) {
                    return null
                }
                throw error
            }
        },
    })

    // Fetch available plans
    const plansQuery = useQuery({
        queryKey: ['subscription-plans'],
        queryFn: async () => {
            const response = await apiClient.get('/subscriptions/plans/')
            const data = response.data
            return Array.isArray(data) ? data : (data?.results || [])
        },
    })

    // Subscribe mutation
    const subscribeMutation = useMutation({
        mutationFn: async (planId: number) => {
            return apiClient.post('/subscriptions/subscribe/', {
                plan_id: planId,
                payment_transaction_id: `MOCK_${Date.now()}`,
                auto_renew: true,
            })
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['current-subscription'] })
            alert('Successfully subscribed!')
        },
        onError: (error: any) => {
            console.error('Failed to subscribe:', error)
            const errorMsg = error.response?.data?.error || error.message || 'Failed to subscribe'
            alert(errorMsg)
        },
    })

    // Cancel mutation
    const cancelMutation = useMutation({
        mutationFn: async (subscriptionId: number) => {
            return apiClient.post(`/subscriptions/${subscriptionId}/cancel/`)
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['current-subscription'] })
            setShowCancelModal(false)
            alert('Subscription cancelled successfully')
        },
        onError: (error: any) => {
            console.error('Failed to cancel subscription:', error)
            const errorMsg = error.response?.data?.error || error.message || 'Failed to cancel subscription'
            alert(errorMsg)
        },
    })

    if (plansQuery.isLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <p className="text-zomato-gray">Loading subscription plans...</p>
            </div>
        )
    }

    const currentSubscription = subscriptionQuery.data
    const plans = plansQuery.data || []

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
        })
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0,
        }).format(amount)
    }

    return (
        <div className="min-h-screen page-background p-6">
            <div className="max-w-6xl mx-auto space-y-6">
                {/* Header */}
                <header>
                    <h1 className="text-3xl font-bold text-zomato-dark">Subscription Plans</h1>
                    <p className="text-sm text-zomato-gray mt-1">Unlock exclusive benefits and save on every order</p>
                </header>

                {/* Current Subscription Status */}
                {currentSubscription && (
                    <Card className="bg-gradient-to-br from-purple-600 to-purple-800 text-white shadow-lg">
                        <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <Crown className="h-6 w-6" />
                                        <h2 className="text-2xl font-bold">{currentSubscription.plan.name}</h2>
                                    </div>
                                    <p className="text-sm opacity-90">Active Subscription</p>
                                    <div className="mt-4 space-y-1 text-sm">
                                        <p className="flex items-center gap-2">
                                            <Calendar className="h-4 w-4" />
                                            Started: {formatDate(currentSubscription.start_date)}
                                        </p>
                                        {currentSubscription.end_date && (
                                            <p className="flex items-center gap-2">
                                                <Calendar className="h-4 w-4" />
                                                Expires: {formatDate(currentSubscription.end_date)}
                                            </p>
                                        )}
                                        <p className="flex items-center gap-2">
                                            <CreditCard className="h-4 w-4" />
                                            Auto-renewal: {currentSubscription.auto_renew ? 'Enabled' : 'Disabled'}
                                        </p>
                                    </div>
                                </div>
                                <Button
                                    variant="outline"
                                    className="bg-white/20 hover:bg-white/30 text-white border-white/30"
                                    onClick={() => setShowCancelModal(true)}
                                >
                                    Cancel Subscription
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Available Plans */}
                <div>
                    <h2 className="text-2xl font-bold text-zomato-dark mb-4">
                        {currentSubscription ? 'Upgrade Your Plan' : 'Choose Your Plan'}
                    </h2>
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {plans.map((plan: any) => {
                            const isCurrentPlan = currentSubscription?.plan.id === plan.id
                            const benefits = plan.benefits || {}

                            return (
                                <Card
                                    key={plan.id}
                                    className={cn(
                                        'bg-white shadow-md relative',
                                        isCurrentPlan && 'border-2 border-purple-600'
                                    )}
                                >
                                    {isCurrentPlan && (
                                        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                                            <Badge className="bg-purple-600 text-white px-4 py-1">Current Plan</Badge>
                                        </div>
                                    )}

                                    <CardHeader>
                                        <CardTitle className="text-xl">{plan.name}</CardTitle>
                                        <CardDescription>{plan.description}</CardDescription>
                                        <div className="mt-4">
                                            <div className="flex items-baseline gap-1">
                                                <span className="text-3xl font-bold text-zomato-dark">
                                                    {formatCurrency(Number(plan.price))}
                                                </span>
                                                <span className="text-sm text-zomato-gray">
                                                    /{plan.plan_type === 'MONTHLY' ? 'month' : plan.plan_type === 'YEARLY' ? 'year' : 'lifetime'}
                                                </span>
                                            </div>
                                        </div>
                                    </CardHeader>

                                    <CardContent className="space-y-4">
                                        {/* Benefits */}
                                        <div className="space-y-2">
                                            {benefits.free_delivery && (
                                                <div className="flex items-center gap-2 text-sm">
                                                    <Check className="h-4 w-4 text-green-600" />
                                                    <span>Free delivery on all orders</span>
                                                </div>
                                            )}
                                            {benefits.discount_percentage && (
                                                <div className="flex items-center gap-2 text-sm">
                                                    <Check className="h-4 w-4 text-green-600" />
                                                    <span>{benefits.discount_percentage}% off on every order</span>
                                                </div>
                                            )}
                                            {benefits.priority_support && (
                                                <div className="flex items-center gap-2 text-sm">
                                                    <Check className="h-4 w-4 text-green-600" />
                                                    <span>Priority customer support</span>
                                                </div>
                                            )}
                                            {benefits.points_multiplier && (
                                                <div className="flex items-center gap-2 text-sm">
                                                    <Check className="h-4 w-4 text-green-600" />
                                                    <span>{benefits.points_multiplier}x reward points</span>
                                                </div>
                                            )}
                                            {benefits.exclusive_offers && (
                                                <div className="flex items-center gap-2 text-sm">
                                                    <Check className="h-4 w-4 text-green-600" />
                                                    <span>Exclusive member-only offers</span>
                                                </div>
                                            )}
                                        </div>

                                        <Button
                                            className="w-full bg-zomato-red hover:bg-zomato-darkRed text-white"
                                            disabled={isCurrentPlan || subscribeMutation.isPending}
                                            onClick={() => subscribeMutation.mutate(plan.id)}
                                        >
                                            {isCurrentPlan ? 'Current Plan' : subscribeMutation.isPending ? 'Processing...' : 'Subscribe Now'}
                                        </Button>
                                    </CardContent>
                                </Card>
                            )
                        })}
                    </div>
                </div>

                {/* Benefits Info */}
                <Card className="bg-white shadow-md">
                    <CardHeader>
                        <CardTitle>Why Subscribe?</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-green-100 rounded-full">
                                    <Check className="h-5 w-5 text-green-600" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-zomato-dark">Save on Every Order</h3>
                                    <p className="text-sm text-zomato-gray mt-1">
                                        Get exclusive discounts and free delivery on all your orders
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-purple-100 rounded-full">
                                    <Crown className="h-5 w-5 text-purple-600" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-zomato-dark">Premium Benefits</h3>
                                    <p className="text-sm text-zomato-gray mt-1">
                                        Enjoy priority support and exclusive member-only offers
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-blue-100 rounded-full">
                                    <CreditCard className="h-5 w-5 text-blue-600" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-zomato-dark">Flexible Plans</h3>
                                    <p className="text-sm text-zomato-gray mt-1">
                                        Choose monthly, yearly, or lifetime plans that suit your needs
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <div className="p-2 bg-orange-100 rounded-full">
                                    <AlertCircle className="h-5 w-5 text-orange-600" />
                                </div>
                                <div>
                                    <h3 className="font-semibold text-zomato-dark">Cancel Anytime</h3>
                                    <p className="text-sm text-zomato-gray mt-1">
                                        No long-term commitments. Cancel your subscription anytime
                                    </p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Cancel Confirmation Modal */}
                {showCancelModal && currentSubscription && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                        <Card className="bg-white max-w-md w-full">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <CardTitle>Cancel Subscription</CardTitle>
                                    <Button variant="ghost" onClick={() => setShowCancelModal(false)}>
                                        <X className="h-4 w-4" />
                                    </Button>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="text-center py-4">
                                    <AlertCircle className="h-16 w-16 text-orange-600 mx-auto mb-4" />
                                    <p className="text-lg font-semibold text-zomato-dark">
                                        Are you sure you want to cancel?
                                    </p>
                                    <p className="text-sm text-zomato-gray mt-2">
                                        You'll lose access to all premium benefits including free delivery and exclusive discounts.
                                    </p>
                                    {currentSubscription.end_date && (
                                        <p className="text-xs text-zomato-gray mt-2">
                                            Your subscription will remain active until {formatDate(currentSubscription.end_date)}
                                        </p>
                                    )}
                                </div>
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        className="flex-1"
                                        onClick={() => setShowCancelModal(false)}
                                    >
                                        Keep Subscription
                                    </Button>
                                    <Button
                                        className="flex-1 bg-red-600 hover:bg-red-700 text-white"
                                        onClick={() => cancelMutation.mutate(currentSubscription.id)}
                                        disabled={cancelMutation.isPending}
                                    >
                                        {cancelMutation.isPending ? 'Cancelling...' : 'Yes, Cancel'}
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}
            </div>
        </div>
    )
}
