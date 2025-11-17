import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/packages/ui/components/dialog'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { Star, Upload, X } from 'lucide-react'
import apiClient from '@/packages/api/client'

interface ReviewModalProps {
  orderId: number
  restaurantId: number
  isOpen: boolean
  onClose: () => void
  onSuccess?: () => void
}

export default function ReviewModal({ orderId, restaurantId, isOpen, onClose, onSuccess }: ReviewModalProps) {
  const [restaurantRating, setRestaurantRating] = useState(0)
  const [foodRating, setFoodRating] = useState(0)
  const [deliveryRating, setDeliveryRating] = useState(0)
  const [comment, setComment] = useState('')
  const [images, setImages] = useState<File[]>([])
  const [itemRatings, setItemRatings] = useState<Record<number, number>>({})
  const queryClient = useQueryClient()

  const createReviewMutation = useMutation({
    mutationFn: async (reviewData: any) => {
      const response = await apiClient.post('/orders/reviews/', reviewData)
      return response.data
    },
    onSuccess: async (review) => {
      // Upload images if any
      if (images.length > 0) {
        const formData = new FormData()
        images.forEach((img) => formData.append('images', img))
        await apiClient.post(`/orders/reviews/${review.id}/upload_images/`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
      }

      queryClient.invalidateQueries({ queryKey: ['reviews', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['order', orderId] })
      onSuccess?.()
      onClose()
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (restaurantRating === 0) {
      alert('Please provide a restaurant rating')
      return
    }

    createReviewMutation.mutate({
      order: orderId,
      restaurant_rating: restaurantRating,
      food_rating: foodRating || null,
      delivery_rating: deliveryRating || null,
      comment: comment,
      item_reviews: Object.entries(itemRatings).map(([orderItemId, rating]) => ({
        order_item: parseInt(orderItemId),
        rating: rating,
      })),
    })
  }

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newImages = Array.from(e.target.files)
      setImages((prev) => [...prev, ...newImages].slice(0, 5)) // Max 5 images
    }
  }

  const removeImage = (index: number) => {
    setImages((prev) => prev.filter((_, i) => i !== index))
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Write a Review</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Restaurant Rating */}
          <div>
            <label className="block text-sm font-medium mb-2">Restaurant Rating *</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((rating) => (
                <button
                  key={rating}
                  type="button"
                  onClick={() => setRestaurantRating(rating)}
                  className="focus:outline-none"
                >
                  <Star
                    className={`w-8 h-8 ${
                      rating <= restaurantRating
                        ? 'fill-yellow-400 text-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                </button>
              ))}
            </div>
          </div>

          {/* Food Rating */}
          <div>
            <label className="block text-sm font-medium mb-2">Food Quality</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((rating) => (
                <button
                  key={rating}
                  type="button"
                  onClick={() => setFoodRating(rating)}
                  className="focus:outline-none"
                >
                  <Star
                    className={`w-8 h-8 ${
                      rating <= foodRating
                        ? 'fill-yellow-400 text-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                </button>
              ))}
            </div>
          </div>

          {/* Delivery Rating */}
          <div>
            <label className="block text-sm font-medium mb-2">Delivery Experience</label>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((rating) => (
                <button
                  key={rating}
                  type="button"
                  onClick={() => setDeliveryRating(rating)}
                  className="focus:outline-none"
                >
                  <Star
                    className={`w-8 h-8 ${
                      rating <= deliveryRating
                        ? 'fill-yellow-400 text-yellow-400'
                        : 'text-gray-300'
                    }`}
                  />
                </button>
              ))}
            </div>
          </div>

          {/* Comment */}
          <div>
            <label className="block text-sm font-medium mb-2">Your Review</label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Share your experience..."
              className="w-full p-3 border rounded-lg"
              rows={4}
            />
          </div>

          {/* Image Upload */}
          <div>
            <label className="block text-sm font-medium mb-2">Add Photos (up to 5)</label>
            <div className="flex flex-wrap gap-2 mb-2">
              {images.map((img, index) => (
                <div key={index} className="relative">
                  <img
                    src={URL.createObjectURL(img)}
                    alt={`Review ${index + 1}`}
                    className="w-20 h-20 object-cover rounded"
                  />
                  <button
                    type="button"
                    onClick={() => removeImage(index)}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
            {images.length < 5 && (
              <label className="inline-flex items-center gap-2 px-4 py-2 border rounded-lg cursor-pointer hover:bg-gray-50">
                <Upload className="w-4 h-4" />
                Upload Photos
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={handleImageSelect}
                  className="hidden"
                />
              </label>
            )}
          </div>

          {/* Submit */}
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button
              type="submit"
              className="flex-1"
              disabled={createReviewMutation.isPending || restaurantRating === 0}
            >
              {createReviewMutation.isPending ? 'Submitting...' : 'Submit Review'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

