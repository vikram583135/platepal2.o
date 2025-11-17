import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Order } from '@/packages/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Badge } from '@/packages/ui/components/badge'
import { Button } from '@/packages/ui/components/button'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/packages/ui/components/dialog'
import { MapPin, Package, RefreshCw, Download, FileText, CreditCard, Star } from 'lucide-react'
import { formatCurrency, formatDate } from '@/packages/utils/format'
import ReviewModal from '../components/ReviewModal'

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [showTransactionModal, setShowTransactionModal] = useState(false)
  const [showReviewModal, setShowReviewModal] = useState(false)
  const queryClient = useQueryClient()

  const { data: order, isLoading } = useQuery<Order>({
    queryKey: ['order', id],
    queryFn: async () => {
      const response = await apiClient.get(`/orders/orders/${id}/`)
      return response.data
    },
  })

  const { data: invoice } = useQuery({
    queryKey: ['invoice', id],
    queryFn: async () => {
      const response = await apiClient.get(`/orders/orders/${id}/invoice/`)
      return response.data
    },
    enabled: !!order,
  })

  const { data: transaction } = useQuery({
    queryKey: ['transaction', id],
    queryFn: async () => {
      const response = await apiClient.get(`/orders/orders/${id}/transaction/`)
      return response.data
    },
    enabled: showTransactionModal && !!order,
  })

  const { data: review } = useQuery({
    queryKey: ['review', id],
    queryFn: async () => {
      const response = await apiClient.get(`/orders/reviews/?order_id=${id}`)
      const reviews = response.data.results || response.data
      return reviews.length > 0 ? reviews[0] : null
    },
    enabled: !!order && order.status === 'DELIVERED',
  })

  const repeatOrderMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/orders/orders/${id}/repeat/`)
      return response.data
    },
    onSuccess: (data) => {
      navigate(`/orders/${data.id}`)
    },
  })

  const handleDownloadInvoice = () => {
    if (invoice) {
      // In production, generate PDF on backend and download
      const invoiceText = `
INVOICE
Order Number: ${invoice.order_number}
Date: ${new Date(invoice.date).toLocaleDateString()}

Customer:
${invoice.customer.name}
${invoice.customer.email}
${invoice.customer.phone}

Restaurant:
${invoice.restaurant.name}
${invoice.restaurant.address}
${invoice.restaurant.phone}

Items:
${invoice.items.map((item: any) => `${item.name} x${item.quantity} - ${formatCurrency(item.total_price, 'INR')}`).join('\n')}

Subtotal: ${formatCurrency(invoice.subtotal, 'INR')}
Tax: ${formatCurrency(invoice.tax_amount, 'INR')}
Delivery Fee: ${formatCurrency(invoice.delivery_fee, 'INR')}
Tip: ${formatCurrency(invoice.tip_amount, 'INR')}
Discount: ${formatCurrency(invoice.discount_amount, 'INR')}
Total: ${formatCurrency(invoice.total_amount, 'INR')}

Payment Method: ${invoice.payment_method}
${invoice.transaction_id ? `Transaction ID: ${invoice.transaction_id}` : ''}
      `.trim()
      
      const blob = new Blob([invoiceText], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `invoice-${invoice.order_number}.txt`
      a.click()
      URL.revokeObjectURL(url)
    }
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!order) {
    return <div>Order not found</div>
  }

  const isActiveOrder = order.status && !['DELIVERED', 'CANCELLED', 'REFUNDED'].includes(order.status)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Order #{order.order_number}</h1>
          <Badge>{order.status}</Badge>
        </div>
        {isActiveOrder && (
          <Button onClick={() => navigate(`/orders/${id}/track`)}>
            <MapPin className="w-4 h-4 mr-2" />
            Track Order
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <Card className="mb-6">
            <CardContent className="p-6">
              <h2 className="text-xl font-semibold mb-4">Order Items</h2>
              <div className="space-y-4">
                {order.items.map((item) => (
                  <div key={item.id} className="flex justify-between items-start pb-4 border-b last:border-0">
                    <div>
                      <h3 className="font-semibold">{item.name}</h3>
                      <p className="text-sm text-gray-600">Quantity: {item.quantity}</p>
                      {item.selected_modifiers && item.selected_modifiers.length > 0 && (
                        <p className="text-xs text-gray-500 mt-1">
                          {item.selected_modifiers.map((m: any) => m.name).join(', ')}
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">{formatCurrency(item.total_price)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardContent className="p-6">
              <h2 className="text-xl font-semibold mb-4">Order Summary</h2>
              <div className="space-y-2 mb-4">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span>{formatCurrency(order.subtotal, 'INR')}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tax</span>
                  <span>{formatCurrency(order.tax_amount, 'INR')}</span>
                </div>
                <div className="flex justify-between">
                  <span>Delivery Fee</span>
                  <span>{formatCurrency(order.delivery_fee, 'INR')}</span>
                </div>
                {order.tip_amount > 0 && (
                  <div className="flex justify-between">
                    <span>Tip</span>
                    <span>{formatCurrency(order.tip_amount, 'INR')}</span>
                  </div>
                )}
                {order.discount_amount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount</span>
                    <span>-{formatCurrency(order.discount_amount, 'INR')}</span>
                  </div>
                )}
                <div className="border-t pt-2 flex justify-between font-semibold text-lg">
                  <span>Total</span>
                  <span>{formatCurrency(order.total_amount, 'INR')}</span>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                <p>Placed on {formatDate(order.created_at)}</p>
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <Card>
            <CardContent className="p-6 space-y-3">
              <Button
                variant="outline"
                className="w-full"
                onClick={handleDownloadInvoice}
              >
                <Download className="w-4 h-4 mr-2" />
                Download Invoice
              </Button>
              
              <Button
                variant="outline"
                className="w-full"
                onClick={() => repeatOrderMutation.mutate()}
                disabled={repeatOrderMutation.isPending}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                {repeatOrderMutation.isPending ? 'Reordering...' : 'Repeat Order'}
              </Button>

              {order.status && !['DELIVERED', 'CANCELLED', 'REFUNDED'].includes(order.status) && (
                <Button
                  variant="destructive"
                  className="w-full"
                  onClick={() => {
                    const reason = prompt('Please provide a reason for cancellation:')
                    if (reason) {
                      apiClient.post(`/orders/orders/${order.id}/cancel/`, { reason })
                        .then(() => {
                          queryClient.invalidateQueries({ queryKey: ['order', id] })
                          alert('Order cancelled successfully. Refund will be processed if payment was made.')
                        })
                        .catch((err) => {
                          alert(err.response?.data?.error || 'Failed to cancel order')
                        })
                    }
                  }}
                >
                  Cancel Order
                </Button>
              )}

              {order.status === 'DELIVERED' && !review && (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setShowReviewModal(true)}
                >
                  <Star className="w-4 h-4 mr-2" />
                  Write a Review
                </Button>
              )}

              <Dialog open={showTransactionModal} onOpenChange={setShowTransactionModal}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="w-full">
                    <CreditCard className="w-4 h-4 mr-2" />
                    Transaction Details
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Transaction Details</DialogTitle>
                  </DialogHeader>
                  {transaction ? (
                    <div className="space-y-3">
                      <div>
                        <div className="text-sm text-gray-600">Transaction ID</div>
                        <div className="font-medium">{transaction.transaction_id}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Payment Method</div>
                        <div className="font-medium">{transaction.payment_method}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Amount</div>
                        <div className="font-medium">{formatCurrency(transaction.amount, transaction.currency || 'INR')}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-600">Status</div>
                        <Badge>{transaction.status}</Badge>
                      </div>
                      {transaction.processed_at && (
                        <div>
                          <div className="text-sm text-gray-600">Processed At</div>
                          <div className="font-medium">{new Date(transaction.processed_at).toLocaleString()}</div>
                        </div>
                      )}
                      {transaction.refund_amount && (
                        <div className="border-t pt-3">
                          <div className="text-sm text-gray-600">Refund Amount</div>
                          <div className="font-medium text-red-600">{formatCurrency(transaction.refund_amount, transaction.currency || 'INR')}</div>
                          {transaction.refund_transaction_id && (
                            <div className="text-xs text-gray-500 mt-1">Refund ID: {transaction.refund_transaction_id}</div>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div>Loading transaction details...</div>
                  )}
                </DialogContent>
              </Dialog>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Review Modal */}
      {order && (
        <ReviewModal
          orderId={order.id}
          restaurantId={order.restaurant?.id || order.restaurant_id}
          isOpen={showReviewModal}
          onClose={() => setShowReviewModal(false)}
          onSuccess={() => {
            // Refresh order data
          }}
        />
      )}
    </div>
  )
}

