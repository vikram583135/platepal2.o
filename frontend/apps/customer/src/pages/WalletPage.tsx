import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { Badge } from '@/packages/ui/components/badge'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/packages/ui/components/dialog'
import { Wallet, Plus, ArrowDownCircle, ArrowUpCircle, History } from 'lucide-react'
import apiClient from '@/packages/api/client'
import { formatCurrency, formatDate } from '@/packages/utils/format'

export default function WalletPage() {
  const [addMoneyAmount, setAddMoneyAmount] = useState('')
  const [showAddMoneyDialog, setShowAddMoneyDialog] = useState(false)
  const queryClient = useQueryClient()

  const { data: wallet, isLoading: walletLoading } = useQuery({
    queryKey: ['wallet'],
    queryFn: async () => {
      const response = await apiClient.get('/payments/wallet/balance/')
      return response.data
    },
  })

  const { data: transactions, isLoading: transactionsLoading } = useQuery({
    queryKey: ['wallet-history'],
    queryFn: async () => {
      const response = await apiClient.get('/payments/wallet/history/')
      return response.data.transactions || []
    },
  })

  const addMoneyMutation = useMutation({
    mutationFn: async (amount: number) => {
      const response = await apiClient.post('/payments/wallet/add_money/', {
        amount,
        payment_method: 'CARD',
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] })
      queryClient.invalidateQueries({ queryKey: ['wallet-history'] })
      setShowAddMoneyDialog(false)
      setAddMoneyAmount('')
      alert('Money added successfully!')
    },
  })

  const handleAddMoney = () => {
    const amount = parseFloat(addMoneyAmount)
    if (isNaN(amount) || amount <= 0) {
      alert('Please enter a valid amount')
      return
    }
    addMoneyMutation.mutate(amount)
  }

  const getTransactionIcon = (type: string) => {
    return type === 'CREDIT' ? (
      <ArrowDownCircle className="w-5 h-5 text-green-600" />
    ) : (
      <ArrowUpCircle className="w-5 h-5 text-red-600" />
    )
  }

  const getTransactionColor = (type: string) => {
    return type === 'CREDIT' ? 'text-green-600' : 'text-red-600'
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">My Wallet</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Wallet Balance Card */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Wallet className="w-5 h-5" />
                Wallet Balance
              </CardTitle>
            </CardHeader>
            <CardContent>
              {walletLoading ? (
                <Skeleton className="h-16 w-full" />
              ) : (
                <div>
                  <div className="text-4xl font-bold mb-4">
                    {formatCurrency(wallet?.balance || 0, wallet?.currency || 'INR')}
                  </div>
                  <Dialog open={showAddMoneyDialog} onOpenChange={setShowAddMoneyDialog}>
                    <DialogTrigger asChild>
                      <Button className="w-full">
                        <Plus className="w-4 h-4 mr-2" />
                        Add Money
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Add Money to Wallet</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">Amount</label>
                          <Input
                            type="number"
                            placeholder="Enter amount"
                            value={addMoneyAmount}
                            onChange={(e) => setAddMoneyAmount(e.target.value)}
                            min="1"
                            step="0.01"
                          />
                        </div>
                        <div className="flex gap-2">
                          {[100, 500, 1000, 2000].map((amount) => (
                            <Button
                              key={amount}
                              variant="outline"
                              size="sm"
                              onClick={() => setAddMoneyAmount(amount.toString())}
                            >
                              ₹{amount}
                            </Button>
                          ))}
                        </div>
                        <Button
                          className="w-full"
                          onClick={handleAddMoney}
                          disabled={addMoneyMutation.isPending}
                        >
                          {addMoneyMutation.isPending ? 'Processing...' : 'Add Money'}
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Transaction History */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="w-5 h-5" />
                Transaction History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {transactionsLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-20 w-full" />
                </div>
              ) : transactions && transactions.length > 0 ? (
                <div className="space-y-4">
                  {transactions.map((transaction: any) => (
                    <div
                      key={transaction.id}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div className="flex items-center gap-4">
                        {getTransactionIcon(transaction.transaction_type)}
                        <div>
                          <div className="font-medium">{transaction.description || transaction.source.replace('_', ' ')}</div>
                          <div className="text-sm text-gray-600">
                            {formatDate(transaction.created_at)}
                          </div>
                          {transaction.order_number && (
                            <div className="text-xs text-gray-500">
                              Order: {transaction.order_number}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`font-semibold ${getTransactionColor(transaction.transaction_type)}`}>
                          {transaction.transaction_type === 'CREDIT' ? '+' : '-'}
                          {formatCurrency(transaction.amount, 'INR')}
                        </div>
                        <div className="text-xs text-gray-500">
                          Balance: {formatCurrency(transaction.balance_after, 'INR')}
                        </div>
                        <Badge variant="outline" className="mt-1">
                          {transaction.source.replace('_', ' ')}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
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

