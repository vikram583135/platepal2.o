import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { useRestaurantStore } from '../stores/restaurantStore'

export default function ReviewsPage() {
  const { selectedRestaurantId } = useRestaurantStore()
  const queryClient = useQueryClient()
  const [replyText, setReplyText] = useState<Record<number, string>>({})

  const reviewsQuery = useQuery({
    queryKey: ['reviews', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get('/orders/reviews/', {
        params: { restaurant_id: selectedRestaurantId },
      })
      // Normalize response to always return array
      const data = response.data
      return Array.isArray(data) ? data : (data?.results || data || [])
    },
    enabled: Boolean(selectedRestaurantId),
  })

  const replyMutation = useMutation({
    mutationFn: async ({ reviewId, reply }: { reviewId: number; reply: string }) => {
      await apiClient.post(`/orders/reviews/${reviewId}/reply/`, { reply })
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['reviews', selectedRestaurantId] })
      setReplyText((prev) => {
        const newState = { ...prev }
        delete newState[variables.reviewId]
        return newState
      })
    },
    onError: (error: any) => {
      console.error('Failed to reply to review:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to reply to review'
      alert(errorMsg)
    },
  })

  const reviews = reviewsQuery.data || []

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to view reviews</p>
        </div>
      </div>
    )
  }

  if (reviewsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-zomato-gray">Loading reviews...</p>
      </div>
    )
  }

  if (reviewsQuery.error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-2">Failed to load reviews</p>
          <p className="text-zomato-gray text-sm">
            {reviewsQuery.error instanceof Error ? reviewsQuery.error.message : 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-slate-900">Reviews & ratings</h1>
        <p className="text-sm text-slate-500">Respond to feedback and highlight signature dishes.</p>
      </header>

      <div className="space-y-4">
        {reviews.length > 0 ? (
          reviews.map((review: any) => (
          <Card key={review.id} className="border-white/70 bg-white/90 shadow-sm">
            <CardHeader>
              <CardTitle className="text-base flex items-center justify-between">
                <span>{review.customer_name || 'Anonymous'}</span>
                <span className="text-sm font-semibold text-primary-600">{review.restaurant_rating} ★</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-slate-700">{review.comment || 'No comment provided.'}</p>
              {review.restaurant_reply && (
                <div className="rounded-xl border border-slate-100 bg-slate-50 px-3 py-2 text-xs text-slate-600">
                  <strong>Reply:</strong> {review.restaurant_reply}
                </div>
              )}
              <div className="flex gap-2">
                <Input
                  placeholder="Write a reply"
                  value={replyText[review.id] ?? ''}
                  onChange={(event) => setReplyText((prev) => ({ ...prev, [review.id]: event.target.value }))}
                />
                <Button 
                  disabled={!replyText[review.id]?.trim() || replyMutation.isPending} 
                  onClick={() => replyMutation.mutate({ reviewId: review.id, reply: replyText[review.id] })}
                >
                  {replyMutation.isPending ? 'Sending...' : 'Reply'}
                </Button>
              </div>
            </CardContent>
          </Card>
          ))
        ) : (
          <div className="text-center py-12">
            <p className="text-sm text-slate-500">No reviews yet.</p>
          </div>
        )}
      </div>
    </div>
  )
}


