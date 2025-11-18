import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Badge } from '@/packages/ui/components/badge'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { CheckCircle, Clock } from 'lucide-react'
import apiClient from '@/packages/api/client'
import { formatCurrency, formatDate } from '@/packages/utils/format'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/packages/ui/components/button'

export default function RefundPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: refund, isLoading } = useQuery({
    queryKey: ['refund', id],
    queryFn: async () => {
      const response = await apiClient.get(`/payments/refunds/${id}/`)
      return response.data
    },
  })

  const { data: timeline } = useQuery({
    queryKey: ['refund-timeline', id],
    queryFn: async () => {
      const response = await apiClient.get(`/payments/refunds/${id}/timeline/`)
      return response.data
    },
    enabled: !!refund,
  })

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!refund) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-4 py-3 rounded">
          Refund not found or you don't have permission to view it.
        </div>
        <Button className="mt-4" onClick={() => navigate('/orders')}>
          Back to Orders
        </Button>
      </div>
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-green-100 text-green-700'
      case 'PROCESSING':
        return 'bg-yellow-100 text-yellow-700'
      case 'FAILED':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <Button variant="outline" onClick={() => navigate(-1)} className="mb-4">
          ← Back
        </Button>
        <h1 className="text-3xl font-bold mb-2">Refund Details</h1>
        <Badge className={getStatusColor(refund.status)}>
          {refund.status}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          {/* Refund Timeline */}
          {timeline && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Refund Timeline</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {timeline.timeline.map((item: any, index: number) => (
                    <div key={index} className="flex items-start gap-4">
                      <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                        item.completed ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
                      }`}>
                        {item.completed ? (
                          <CheckCircle className="w-6 h-6" />
                        ) : (
                          <Clock className="w-6 h-6" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="font-semibold">{item.label}</div>
                        <div className="text-sm text-gray-600">
                          {new Date(item.timestamp).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Refund Details */}
          <Card>
            <CardHeader>
              <CardTitle>Refund Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-sm text-gray-600 mb-1">Refund Amount</div>
                <div className="text-2xl font-bold text-green-600">
                  {formatCurrency(refund.amount, 'INR')}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600 mb-1">Reason</div>
                <div className="text-gray-900">{refund.reason}</div>
              </div>
              {refund.refund_transaction_id && (
                <div>
                  <div className="text-sm text-gray-600 mb-1">Refund Transaction ID</div>
                  <div className="font-mono text-sm">{refund.refund_transaction_id}</div>
                </div>
              )}
              {refund.processed_at && (
                <div>
                  <div className="text-sm text-gray-600 mb-1">Processed At</div>
                  <div>{formatDate(refund.processed_at)}</div>
                </div>
              )}
              {refund.order && (
                <div>
                  <div className="text-sm text-gray-600 mb-1">Related Order</div>
                  <Button
                    variant="link"
                    className="p-0 h-auto"
                    onClick={() => navigate(`/orders/${refund.order}`)}
                  >
                    Order #{refund.order_number || refund.order}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>Payment Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {refund.payment && (
                <>
                  <div>
                    <div className="text-sm text-gray-600">Original Payment</div>
                    <div className="font-medium">{formatCurrency(refund.payment.amount, refund.payment.currency || 'INR')}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-600">Payment Method</div>
                    <div className="font-medium">{refund.payment.method_type}</div>
                  </div>
                  {refund.payment.transaction_id && (
                    <div>
                      <div className="text-sm text-gray-600">Transaction ID</div>
                      <div className="font-mono text-xs">{refund.payment.transaction_id}</div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

