import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Badge } from '@/packages/ui/components/badge'
import * as formatUtils from '@/packages/utils/format'
import { CSVExporter } from '@/packages/ui/components/CSVExporter'

interface EarningsBreakdown {
  total_earnings: number
  total_deliveries: number
  base_fee_total: number
  distance_fee_total: number
  tip_total: number
  surge_bonus_total: number
  incentives_total: number
  by_day: Array<{
    date: string
    earnings: number
    deliveries: number
  }>
}

interface Wallet {
  id: number
  balance: number
  pending_balance: number
  total_earnings: number
  total_withdrawn: number
  currency: string
}

interface WalletTransaction {
  id: number
  transaction_type: string
  amount: number
  status: string
  created_at: string
  description: string
}

export default function EarningsPage() {
  const queryClient = useQueryClient()
  const [period, setPeriod] = useState<'day' | 'week' | 'month' | 'year'>('week')
  const [exportData, setExportData] = useState<any[]>([])

  // Get wallet
  const { data: wallet } = useQuery({
    queryKey: ['rider-wallet'],
    queryFn: async () => {
      const response = await apiClient.get('/deliveries/wallets/me/')
      return response.data as Wallet
    },
  })

  // Get earnings breakdown
  const { data: breakdown, isLoading: breakdownLoading } = useQuery({
    queryKey: ['earnings-breakdown', period],
    queryFn: async () => {
      const response = await apiClient.get(`/deliveries/wallets/earnings_breakdown/?period=${period}`)
      return response.data.breakdown as EarningsBreakdown
    },
  })

  // Get wallet transactions
  const { data: transactions } = useQuery({
    queryKey: ['wallet-transactions'],
    queryFn: async () => {
      const response = await apiClient.get('/deliveries/wallets/transactions/')
      return (response.data.results || response.data) as WalletTransaction[]
    },
  })

  // Instant payout mutation
  const instantPayoutMutation = useMutation({
    mutationFn: async (amount: number) => {
      const response = await apiClient.post('/deliveries/wallets/instant_payout/', {
        amount,
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rider-wallet'] })
      queryClient.invalidateQueries({ queryKey: ['wallet-transactions'] })
    },
  })

  const handleInstantPayout = () => {
    if (wallet && wallet.balance > 0) {
      if (confirm(`Withdraw ${formatUtils.formatCurrency(wallet.balance, wallet.currency || 'USD')}?`)) {
        instantPayoutMutation.mutate(wallet.balance)
      }
    }
  }

  // Prepare export data
  const handleExport = () => {
    if (breakdown?.by_day) {
      const exportRows = breakdown.by_day.map((day) => ({
        Date: formatUtils.formatDate(day.date),
        Earnings: day.earnings,
        Deliveries: day.deliveries,
        'Avg per Delivery': day.deliveries > 0 ? (day.earnings / day.deliveries).toFixed(2) : '0.00',
      }))
      setExportData(exportRows)
    }
  }

  if (breakdownLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading earnings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Earnings</h1>
        <div className="flex items-center space-x-4">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as typeof period)}
            className="px-4 py-2 border border-gray-300 rounded-md"
          >
            <option value="day">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="year">This Year</option>
          </select>
          <Button onClick={handleExport} variant="outline">
            Export CSV
          </Button>
        </div>
      </div>

      {/* Wallet Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Available Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600 mb-2">
              {formatUtils.formatCurrency(wallet?.balance || 0, wallet?.currency || 'USD')}
            </div>
            <Button
              onClick={handleInstantPayout}
              disabled={!wallet || wallet.balance <= 0 || instantPayoutMutation.isPending}
              className="w-full mt-4 bg-green-600 hover:bg-green-700"
            >
              {instantPayoutMutation.isPending
                ? 'Processing...'
                : `Withdraw ${formatUtils.formatCurrency(wallet?.balance || 0, wallet?.currency || 'USD')}`}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Pending Balance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600 mb-2">
              {formatUtils.formatCurrency(wallet?.pending_balance || 0, wallet?.currency || 'USD')}
            </div>
            <p className="text-sm text-gray-600">
              Earnings waiting to be processed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Total Earnings</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {formatUtils.formatCurrency(wallet?.total_earnings || 0, wallet?.currency || 'USD')}
            </div>
            <p className="text-sm text-gray-600">
              All-time earnings
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Earnings Breakdown */}
      {breakdown && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-semibold">Period Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total Earnings</p>
                  <p className="text-2xl font-bold text-green-600">
                    {formatUtils.formatCurrency(breakdown.total_earnings || 0, wallet?.currency || 'USD')}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Deliveries</p>
                  <p className="text-2xl font-bold">{breakdown.total_deliveries || 0}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Avg per Delivery</p>
                  <p className="text-2xl font-bold">
                    {formatUtils.formatCurrency(
                      (breakdown.total_deliveries || 0) > 0
                        ? (breakdown.total_earnings || 0) / (breakdown.total_deliveries || 1)
                        : 0,
                      wallet?.currency || 'USD'
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total Tips</p>
                  <p className="text-2xl font-bold text-blue-600">
                    {formatUtils.formatCurrency(breakdown.tip_total || 0, wallet?.currency || 'USD')}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
                <div>
                  <p className="text-xs text-gray-500 mb-1">Base Fee</p>
                  <p className="font-semibold">
                    {formatUtils.formatCurrency(breakdown.base_fee_total || 0, wallet?.currency || 'USD')}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">Distance Fee</p>
                  <p className="font-semibold">
                    {formatUtils.formatCurrency(breakdown.distance_fee_total || 0, wallet?.currency || 'USD')}
                  </p>
                </div>
                {breakdown.surge_bonus_total > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Surge Bonus</p>
                    <p className="font-semibold text-orange-600">
                      {formatUtils.formatCurrency(breakdown.surge_bonus_total || 0, wallet?.currency || 'USD')}
                    </p>
                  </div>
                )}
                {breakdown.incentives_total > 0 && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Incentives</p>
                    <p className="font-semibold text-purple-600">
                      {formatUtils.formatCurrency(breakdown.incentives_total || 0, wallet?.currency || 'USD')}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Daily Breakdown Chart */}
          {breakdown.by_day && breakdown.by_day.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-semibold">Daily Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {breakdown.by_day.map((day, index) => (
                    <div key={index} className="flex items-center space-x-4">
                      <div className="w-24 text-sm font-medium text-gray-700">
                        {formatUtils.formatDate(day.date, 'MMM dd')}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-gray-600">
                            {day.deliveries} {day.deliveries === 1 ? 'delivery' : 'deliveries'}
                          </span>
                          <span className="font-semibold text-green-600">
                            {formatUtils.formatCurrency(day.earnings, wallet?.currency || 'USD')}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-600 h-2 rounded-full transition-all"
                            style={{
                              width: `${
                                breakdown.total_earnings > 0
                                  ? (day.earnings / breakdown.total_earnings) * 100
                                  : 0
                              }%`,
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Recent Transactions */}
      {transactions && transactions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg font-semibold">Recent Transactions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {transactions.slice(0, 10).map((transaction) => (
                <div
                  key={transaction.id}
                  className="flex justify-between items-center py-3 border-b last:border-0"
                >
                  <div>
                    <p className="font-medium">{transaction.description || transaction.transaction_type}</p>
                    <p className="text-sm text-gray-600">
                      {formatUtils.formatDate(transaction.created_at)} {formatUtils.formatTime(transaction.created_at)}
                    </p>
                  </div>
                  <div className="text-right">
                    <p
                      className={`font-semibold ${
                        transaction.transaction_type === 'EARNING'
                          ? 'text-green-600'
                          : transaction.transaction_type === 'WITHDRAWAL'
                          ? 'text-red-600'
                          : 'text-gray-600'
                      }`}
                    >
                      {transaction.transaction_type === 'WITHDRAWAL' ? '-' : '+'}
                      {formatUtils.formatCurrency(
                        Math.abs(transaction.amount),
                        wallet?.currency || 'USD'
                      )}
                    </p>
                    <Badge
                      variant={
                        transaction.status === 'COMPLETED'
                          ? 'default'
                          : transaction.status === 'PENDING'
                          ? 'outline'
                          : 'destructive'
                      }
                      className="mt-1"
                    >
                      {transaction.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* CSV Export Component */}
      {exportData.length > 0 && (
        <CSVExporter
          data={exportData}
          filename={`earnings-${period}-${new Date().toISOString().split('T')[0]}.csv`}
          onExportComplete={() => setExportData([])}
        />
      )}
    </div>
  )
}
