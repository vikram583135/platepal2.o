import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Badge } from '@/packages/ui/components/badge'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/packages/ui/components/dialog'
// Using native select
import { Trophy, Gift, History } from 'lucide-react'
import apiClient from '@/packages/api/client'
import { formatCurrency, formatDate } from '@/packages/utils/format'
import { useNavigate } from 'react-router-dom'

export default function RewardsPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showRedeemModal, setShowRedeemModal] = useState(false)
  const [redeemType, setRedeemType] = useState('DISCOUNT')
  const [redeemPoints, setRedeemPoints] = useState(100)

  const { data: loyalty, isLoading: loyaltyLoading } = useQuery({
    queryKey: ['loyalty-balance'],
    queryFn: async () => {
      const response = await apiClient.get('/rewards/loyalty/balance/')
      return response.data
    },
  })

  const { data: history } = useQuery({
    queryKey: ['reward-history'],
    queryFn: async () => {
      const response = await apiClient.get('/rewards/loyalty/history/')
      return response.data.transactions || []
    },
  })

  const { data: tiers } = useQuery({
    queryKey: ['loyalty-tiers'],
    queryFn: async () => {
      const response = await apiClient.get('/rewards/tiers/')
      return response.data.results || response.data || []
    },
  })

  const redeemMutation = useMutation({
    mutationFn: async (data: { reward_type: string; points: number }) => {
      const response = await apiClient.post('/rewards/redemptions/redeem/', data)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['loyalty-balance'] })
      queryClient.invalidateQueries({ queryKey: ['reward-history'] })
      setShowRedeemModal(false)
      alert(`Successfully redeemed! ${data.coupon_code ? `Coupon code: ${data.coupon_code}` : ''}`)
    },
  })

  const handleRedeem = () => {
    if (redeemPoints < 100) {
      alert('Minimum 100 points required for redemption')
      return
    }
    if (loyalty && loyalty.available_points < redeemPoints) {
      alert('Insufficient points')
      return
    }
    redeemMutation.mutate({
      reward_type: redeemType,
      points: redeemPoints,
    })
  }

  if (loyaltyLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Rewards & Loyalty</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Points Balance */}
        <div className="lg:col-span-2">
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="w-5 h-5" />
                Your Points
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <div className="text-6xl font-bold text-primary-600 mb-2">
                  {loyalty?.available_points || 0}
                </div>
                <div className="text-gray-600 mb-4">Available Points</div>
                
                {loyalty?.current_tier && (
                  <div className="mb-4">
                    <Badge className="text-lg px-4 py-2">
                      {loyalty.current_tier.name} Member
                    </Badge>
                  </div>
                )}

                {loyalty?.next_tier && (
                  <div className="mt-4">
                    <p className="text-sm text-gray-600 mb-2">
                      {loyalty.points_to_next_tier} points to {loyalty.next_tier.name}
                    </p>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all"
                        style={{
                          width: `${Math.min(100, ((loyalty.total_points / loyalty.next_tier.min_points) * 100))}%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4 mt-6">
                  <div>
                    <div className="text-2xl font-semibold">{loyalty?.total_points || 0}</div>
                    <div className="text-sm text-gray-600">Total Points</div>
                  </div>
                  <div>
                    <div className="text-2xl font-semibold">{loyalty?.lifetime_points_earned || 0}</div>
                    <div className="text-sm text-gray-600">Lifetime Earned</div>
                  </div>
                </div>

                <Dialog open={showRedeemModal} onOpenChange={setShowRedeemModal}>
                  <DialogTrigger asChild>
                    <Button className="mt-6">
                      <Gift className="w-4 h-4 mr-2" />
                      Redeem Points
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Redeem Points</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">Reward Type</label>
                        <select
                          value={redeemType}
                          onChange={(e) => setRedeemType(e.target.value)}
                          className="w-full p-3 border rounded-lg"
                        >
                          <option value="DISCOUNT">Discount Coupon</option>
                          <option value="CASHBACK">Cashback</option>
                          <option value="FREE_DELIVERY">Free Delivery</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">Points to Redeem</label>
                        <input
                          type="number"
                          min="100"
                          step="100"
                          value={redeemPoints}
                          onChange={(e) => setRedeemPoints(parseInt(e.target.value) || 100)}
                          className="w-full p-3 border rounded-lg"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          {redeemPoints} points = {formatCurrency(redeemPoints * 0.01, 'INR')}
                        </p>
                      </div>
                      <Button
                        className="w-full"
                        onClick={handleRedeem}
                        disabled={redeemMutation.isPending || (loyalty?.available_points || 0) < redeemPoints}
                      >
                        {redeemMutation.isPending ? 'Processing...' : 'Redeem'}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>

          {/* Loyalty Tiers */}
          {tiers && tiers.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Loyalty Tiers</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {tiers.map((tier: any) => (
                    <div
                      key={tier.id}
                      className={`p-4 border rounded-lg ${
                        loyalty?.current_tier?.id === tier.id ? 'border-primary-500 bg-primary-50' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-semibold">{tier.name}</h3>
                            {loyalty?.current_tier?.id === tier.id && (
                              <Badge>Current Tier</Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mt-1">
                            {tier.min_points} - {tier.max_points || '∞'} points
                          </p>
                          {tier.benefits && (
                            <div className="mt-2 space-y-1">
                              {tier.benefits.points_multiplier && (
                                <p className="text-xs text-gray-600">
                                  {tier.benefits.points_multiplier}x points multiplier
                                </p>
                              )}
                              {tier.benefits.discount_percentage && (
                                <p className="text-xs text-gray-600">
                                  {tier.benefits.discount_percentage}% discount
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                        <Trophy className="w-8 h-8 text-yellow-500" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Transaction History */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="w-5 h-5" />
                Points History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {history && history.length > 0 ? (
                <div className="space-y-3">
                  {history.slice(0, 10).map((transaction: any) => (
                    <div key={transaction.id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">
                          {transaction.transaction_type === 'EARNED' ? (
                            <span className="text-green-600">+{transaction.points}</span>
                          ) : (
                            <span className="text-red-600">-{Math.abs(transaction.points)}</span>
                          )}
                        </span>
                        <span className="text-xs text-gray-500">
                          {formatDate(transaction.created_at)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600">{transaction.description}</p>
                      {transaction.order_number && (
                        <button
                          onClick={() => navigate(`/orders/${transaction.order}`)}
                          className="text-xs text-primary-600 hover:underline mt-1"
                        >
                          Order #{transaction.order_number}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-600">No transactions yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

