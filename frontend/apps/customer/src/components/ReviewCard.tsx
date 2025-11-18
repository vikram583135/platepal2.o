import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/packages/ui/components/avatar'
import { Star, Flag, Reply } from 'lucide-react'
import { formatDate } from '@/packages/utils/format'
import apiClient from '@/packages/api/client'

interface ReviewCardProps {
  review: any
  canReply?: boolean
  onFlag?: () => void
}

export default function ReviewCard({ review, canReply = false, onFlag }: ReviewCardProps) {
  const [showReplyForm, setShowReplyForm] = useState(false)
  const [replyText, setReplyText] = useState('')
  const queryClient = useQueryClient()

  const replyMutation = useMutation({
    mutationFn: async (text: string) => {
      const response = await apiClient.post(`/orders/reviews/${review.id}/reply/`, { reply: text })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviews'] })
      setShowReplyForm(false)
      setReplyText('')
    },
  })

  const flagMutation = useMutation({
    mutationFn: async (reason: string) => {
      const response = await apiClient.post(`/orders/reviews/${review.id}/flag/`, { reason })
      return response.data
    },
    onSuccess: () => {
      alert('Review flagged for moderation')
      onFlag?.()
    },
  })

  const handleFlag = () => {
    const reason = prompt('Why are you flagging this review?')
    if (reason) {
      flagMutation.mutate(reason)
    }
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <Avatar>
            <AvatarImage src={review.customer_photo} />
            <AvatarFallback>{review.customer_name?.[0] || 'U'}</AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <div className="flex items-start justify-between mb-2">
              <div>
                <div className="font-semibold">{review.customer_name || review.customer_email}</div>
                <div className="text-sm text-gray-600">{formatDate(review.created_at)}</div>
              </div>
              <div className="flex items-center gap-1">
                <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                <span className="font-medium">{review.restaurant_rating}</span>
              </div>
            </div>

            {/* Ratings */}
            <div className="flex gap-4 mb-2 text-sm text-gray-600">
              {review.food_rating && (
                <div>Food: {parseFloat(review.food_rating).toFixed(1)}</div>
              )}
              {review.delivery_rating && (
                <div>Delivery: {parseFloat(review.delivery_rating).toFixed(1)}</div>
              )}
            </div>

            {/* Comment */}
            {review.comment && (
              <p className="text-gray-700 mb-3">{review.comment}</p>
            )}

            {/* Images */}
            {review.image_urls && review.image_urls.length > 0 && (
              <div className="flex gap-2 mb-3">
                {review.image_urls.map((img: string, index: number) => (
                  <img
                    key={index}
                    src={img}
                    alt={`Review ${index + 1}`}
                    className="w-20 h-20 object-cover rounded cursor-pointer"
                    onClick={() => window.open(img, '_blank')}
                  />
                ))}
              </div>
            )}

            {/* Restaurant Reply */}
            {review.restaurant_reply && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                <div className="flex items-center gap-2 mb-1">
                  <Reply className="w-4 h-4 text-blue-600" />
                  <span className="font-semibold text-blue-900">Restaurant Response</span>
                </div>
                <p className="text-blue-800 text-sm">{review.restaurant_reply}</p>
                {review.restaurant_replied_at && (
                  <div className="text-xs text-blue-600 mt-1">
                    {formatDate(review.restaurant_replied_at)}
                  </div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 mt-3">
              {canReply && !review.restaurant_reply && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowReplyForm(true)}
                >
                  <Reply className="w-4 h-4 mr-1" />
                  Reply
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={handleFlag}
              >
                <Flag className="w-4 h-4 mr-1" />
                Flag
              </Button>
            </div>

            {/* Reply Form */}
            {showReplyForm && (
              <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                <textarea
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  placeholder="Write a reply..."
                  className="w-full p-2 border rounded mb-2"
                  rows={3}
                />
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => replyMutation.mutate(replyText)}
                    disabled={!replyText.trim() || replyMutation.isPending}
                  >
                    Submit Reply
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      setShowReplyForm(false)
                      setReplyText('')
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

