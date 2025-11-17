import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import apiClient from '@/packages/api/client'
import { DataTable, Column } from '@/packages/ui/components/DataTable'
import { ModalConfirm } from '@/packages/ui/components/ModalConfirm'
import { Check, X, Flag, AlertTriangle } from 'lucide-react'

interface Review {
  id: number
  restaurant: { name: string }
  customer: { email: string }
  restaurant_rating: number
  food_rating: number
  comment: string
  is_approved: boolean
  is_flagged: boolean
  created_at: string
}

export default function ReviewsModerationPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedReviews, setSelectedReviews] = useState<Review[]>([])
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean
    action: string
    review?: Review
    reviews?: Review[]
  }>({ isOpen: false, action: '' })

  const { data: reviews, isLoading } = useQuery({
    queryKey: ['moderation-reviews'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/moderation/reviews/')
      return response.data.results || response.data
    },
  })

  const approveMutation = useMutation({
    mutationFn: async ({ reviewId, reason }: { reviewId: number; reason?: string }) => {
      return apiClient.post(`/admin/moderation/reviews/${reviewId}/approve/`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['moderation-reviews'] })
      setConfirmModal({ isOpen: false, action: '' })
    },
  })

  const rejectMutation = useMutation({
    mutationFn: async ({ reviewId, reason }: { reviewId: number; reason?: string }) => {
      return apiClient.post(`/admin/moderation/reviews/${reviewId}/reject/`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['moderation-reviews'] })
      setConfirmModal({ isOpen: false, action: '' })
    },
  })

  const flagMutation = useMutation({
    mutationFn: async ({ reviewId, reason }: { reviewId: number; reason?: string }) => {
      return apiClient.post(`/admin/moderation/reviews/${reviewId}/flag/`, { reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['moderation-reviews'] })
      setConfirmModal({ isOpen: false, action: '' })
    },
  })

  const bulkApproveMutation = useMutation({
    mutationFn: async ({ reviewIds, reason }: { reviewIds: number[]; reason?: string }) => {
      return apiClient.post('/admin/moderation/reviews/bulk_approve/', { review_ids: reviewIds, reason })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['moderation-reviews'] })
      setConfirmModal({ isOpen: false, action: '' })
      setSelectedReviews([])
    },
  })

  const handleBulkAction = (action: string) => {
    if (selectedReviews.length === 0) return
    setConfirmModal({ isOpen: true, action, reviews: selectedReviews })
  }

  const handleConfirm = (reason?: string) => {
    const { action, review, reviews } = confirmModal
    const targetReviews = review ? [review] : reviews || []

    if (action === 'approve') {
      if (targetReviews.length === 1) {
        approveMutation.mutate({ reviewId: targetReviews[0].id, reason })
      } else {
        bulkApproveMutation.mutate({ reviewIds: targetReviews.map(r => r.id), reason })
      }
    } else if (action === 'reject') {
      targetReviews.forEach(r => {
        rejectMutation.mutate({ reviewId: r.id, reason })
      })
    } else if (action === 'flag') {
      targetReviews.forEach(r => {
        flagMutation.mutate({ reviewId: r.id, reason })
      })
    }
  }

  const columns: Column<Review>[] = [
    {
      key: 'restaurant',
      header: 'Restaurant',
      accessor: (row) => row.restaurant?.name || 'N/A',
      sortable: true,
    },
    {
      key: 'customer',
      header: 'Customer',
      accessor: (row) => row.customer?.email || 'N/A',
      sortable: true,
    },
    {
      key: 'ratings',
      header: 'Ratings',
      accessor: (row) => (
        <div className="flex gap-2">
          <span>Restaurant: {row.restaurant_rating}/5</span>
          {row.food_rating && <span>Food: {row.food_rating}/5</span>}
        </div>
      ),
    },
    {
      key: 'comment',
      header: 'Comment',
      accessor: (row) => (
        <div className="max-w-md truncate" title={row.comment}>
          {row.comment || 'No comment'}
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      accessor: (row) => (
        <div className="flex gap-2">
          {row.is_flagged && (
            <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800">
              Flagged
            </span>
          )}
          {row.is_approved ? (
            <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
              Approved
            </span>
          ) : (
            <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">
              Pending
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'created_at',
      header: 'Date',
      accessor: (row) => new Date(row.created_at).toLocaleDateString(),
      sortable: true,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reviews Moderation</h1>
          <p className="text-gray-600">Moderate customer reviews and ratings</p>
        </div>
        {selectedReviews.length > 0 && (
          <div className="flex gap-2">
            <button
              onClick={() => handleBulkAction('approve')}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              <Check className="w-4 h-4" />
              Approve Selected
            </button>
            <button
              onClick={() => handleBulkAction('reject')}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              <X className="w-4 h-4" />
              Reject Selected
            </button>
          </div>
        )}
      </div>

      <DataTable
        data={reviews || []}
        columns={columns}
        loading={isLoading}
        onRowClick={(review) => navigate(`/moderation/reviews/${review.id}`)}
        selectedRows={selectedReviews}
        onSelectionChange={setSelectedReviews}
        searchable
        pageSize={20}
      />

      <ModalConfirm
        isOpen={confirmModal.isOpen}
        onClose={() => setConfirmModal({ isOpen: false, action: '' })}
        onConfirm={handleConfirm}
        title={
          confirmModal.action === 'approve' ? 'Approve Review(s)' :
          confirmModal.action === 'reject' ? 'Reject Review(s)' :
          'Flag Review(s)'
        }
        message={
          confirmModal.action === 'approve'
            ? `Are you sure you want to approve ${confirmModal.review ? 'this review' : `${confirmModal.reviews?.length} reviews`}?`
            : confirmModal.action === 'reject'
            ? `Are you sure you want to reject ${confirmModal.review ? 'this review' : `${confirmModal.reviews?.length} reviews`}?`
            : `Are you sure you want to flag ${confirmModal.review ? 'this review' : `${confirmModal.reviews?.length} reviews`}?`
        }
        confirmText={confirmModal.action === 'approve' ? 'Approve' : confirmModal.action === 'reject' ? 'Reject' : 'Flag'}
        requireReason
        variant={confirmModal.action === 'reject' ? 'danger' : 'warning'}
      />
    </div>
  )
}

