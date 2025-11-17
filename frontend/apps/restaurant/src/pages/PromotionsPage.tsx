import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { useRestaurantStore } from '../stores/restaurantStore'
import { Plus, Edit, Trash2, Calendar, Tag, Users, TrendingUp, X, CheckCircle2, Clock } from 'lucide-react'
import { cn } from '@/packages/utils/cn'

export default function PromotionsPage() {
  const { selectedRestaurantId } = useRestaurantStore()
  const queryClient = useQueryClient()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingPromo, setEditingPromo] = useState<any>(null)
  const [form, setForm] = useState({
    name: '',
    description: '',
    discount_type: 'PERCENTAGE',
    discount_value: '',
    minimum_order_amount: '',
    maximum_discount: '',
    valid_from: new Date().toISOString().split('T')[0],
    valid_until: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    max_uses: '',
    max_uses_per_user: '1',
    code: '',
    offer_type: 'RESTAURANT',
  })
  const [formError, setFormError] = useState('')

  const promotionsQuery = useQuery({
    queryKey: ['promotions', selectedRestaurantId],
    queryFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      const response = await apiClient.get('/restaurants/promotions/', {
        params: { restaurant: selectedRestaurantId },
      })
      const data = response.data
      return Array.isArray(data) ? data : (data?.results || [])
    },
    enabled: Boolean(selectedRestaurantId),
  })

  const createPromotion = useMutation({
    mutationFn: async () => {
      if (!selectedRestaurantId) {
        throw new Error('No restaurant selected')
      }
      if (!form.name.trim()) {
        throw new Error('Promotion name is required')
      }
      if (!form.discount_value || Number(form.discount_value) <= 0) {
        throw new Error('Valid discount value is required')
      }
      
      const payload: any = {
        restaurant: selectedRestaurantId,
        name: form.name.trim(),
        description: form.description.trim(),
        discount_type: form.discount_type,
        discount_value: Number(form.discount_value),
        minimum_order_amount: form.minimum_order_amount ? Number(form.minimum_order_amount) : 0,
        offer_type: form.offer_type,
        valid_from: new Date(form.valid_from).toISOString(),
        valid_until: new Date(form.valid_until).toISOString(),
        max_uses_per_user: Number(form.max_uses_per_user) || 1,
      }
      
      if (form.maximum_discount) {
        payload.maximum_discount = Number(form.maximum_discount)
      }
      if (form.max_uses) {
        payload.max_uses = Number(form.max_uses)
      }
      if (form.code) {
        payload.code = form.code.trim().toUpperCase()
      }
      
      return apiClient.post('/restaurants/promotions/', payload)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promotions', selectedRestaurantId] })
      resetForm()
      setShowCreateModal(false)
    },
    onError: (error: any) => {
      setFormError(error.message || error.response?.data?.detail || 'Failed to create promotion')
      console.error('Failed to create promotion:', error)
    },
  })

  const updatePromotion = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: any }) => {
      return apiClient.patch(`/restaurants/promotions/${id}/`, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promotions', selectedRestaurantId] })
      setEditingPromo(null)
      resetForm()
    },
    onError: (error: any) => {
      console.error('Failed to update promotion:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to update promotion'
      setFormError(errorMsg)
    },
  })

  const deletePromotion = useMutation({
    mutationFn: async (id: number) => {
      return apiClient.delete(`/restaurants/promotions/${id}/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promotions', selectedRestaurantId] })
    },
    onError: (error: any) => {
      console.error('Failed to delete promotion:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to delete promotion'
      alert(errorMsg)
    },
  })

  const togglePromotion = useMutation({
    mutationFn: async ({ id, isActive }: { id: number; isActive: boolean }) => {
      return apiClient.patch(`/restaurants/promotions/${id}/`, { is_active: isActive })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promotions', selectedRestaurantId] })
    },
    onError: (error: any) => {
      console.error('Failed to toggle promotion:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to toggle promotion'
      alert(errorMsg)
    },
  })

  const resetForm = () => {
    setForm({
      name: '',
      description: '',
      discount_type: 'PERCENTAGE',
      discount_value: '',
      minimum_order_amount: '',
      maximum_discount: '',
      valid_from: new Date().toISOString().split('T')[0],
      valid_until: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      max_uses: '',
      max_uses_per_user: '1',
      code: '',
      offer_type: 'RESTAURANT',
    })
    setFormError('')
  }

  const handleSubmit = () => {
    setFormError('')
    if (!form.name.trim()) {
      setFormError('Promotion name is required')
      return
    }
    if (!form.discount_value || Number(form.discount_value) <= 0) {
      setFormError('Valid discount value is required')
      return
    }
    if (editingPromo) {
      updatePromotion.mutate({ id: editingPromo.id, data: form })
    } else {
      createPromotion.mutate()
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  }

  const isActive = (promo: any) => {
    if (!promo.is_active) return false
    const now = new Date()
    const validFrom = new Date(promo.valid_from)
    const validUntil = new Date(promo.valid_until)
    return now >= validFrom && now <= validUntil
  }

  const getDiscountDisplay = (promo: any) => {
    if (promo.discount_type === 'PERCENTAGE') {
      return `${promo.discount_value}% off`
    }
    if (promo.discount_type === 'FIXED') {
      return `₹${promo.discount_value} off`
    }
    if (promo.discount_type === 'FREE_DELIVERY') {
      return 'Free Delivery'
    }
    if (promo.discount_type === 'BUY_ONE_GET_ONE') {
      return 'Buy 1 Get 1'
    }
    if (promo.discount_type === 'CASHBACK') {
      return `${promo.cashback_percentage}% cashback`
    }
    return 'Discount'
  }

  if (!selectedRestaurantId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-zomato-gray mb-4">Please select a restaurant to manage promotions</p>
        </div>
      </div>
    )
  }

  if (promotionsQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-zomato-gray">Loading promotions...</p>
      </div>
    )
  }

  if (promotionsQuery.error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 mb-2">Failed to load promotions</p>
          <p className="text-zomato-gray text-sm">
            {promotionsQuery.error instanceof Error ? promotionsQuery.error.message : 'An unexpected error occurred'}
          </p>
        </div>
      </div>
    )
  }

  const promotions = promotionsQuery.data || []

  return (
    <div className="min-h-screen bg-zomato-lightGray p-6">
      <div className="space-y-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-zomato-dark">Promotions & Marketing</h1>
            <p className="text-sm text-zomato-gray mt-1">Run campaigns, BOGO offers, and happy hours</p>
          </div>
          <Button
            onClick={() => {
              resetForm()
              setEditingPromo(null)
              setShowCreateModal(true)
            }}
            className="bg-zomato-red hover:bg-zomato-darkRed text-white"
          >
            <Plus className="h-4 w-4 mr-2" />
            Create Promotion
          </Button>
        </header>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {promotions.length > 0 ? (
            promotions.map((promotion: any) => {
              const active = isActive(promotion)
              return (
                <Card key={promotion.id} className="bg-white shadow-md">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg text-zomato-dark">{promotion.name}</CardTitle>
                        {promotion.code && (
                          <p className="text-xs text-zomato-gray mt-1">Code: <span className="font-mono font-semibold">{promotion.code}</span></p>
                        )}
                      </div>
                      <span
                        className={cn(
                          'px-2 py-1 rounded text-xs font-semibold',
                          active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                        )}
                      >
                        {active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-zomato-gray">{promotion.description || 'No description'}</p>
                    <div className="flex items-center gap-2">
                      <Tag className="h-4 w-4 text-zomato-red" />
                      <p className="font-bold text-lg text-zomato-red">{getDiscountDisplay(promotion)}</p>
                    </div>
                    <div className="space-y-1 text-xs text-zomato-gray">
                      {promotion.minimum_order_amount > 0 && (
                        <p>Min order: ₹{Number(promotion.minimum_order_amount).toFixed(0)}</p>
                      )}
                      {promotion.maximum_discount && (
                        <p>Max discount: ₹{Number(promotion.maximum_discount).toFixed(0)}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2">
                        <div className="flex items-center gap-1">
                          <Users className="h-3 w-3" />
                          <span>{promotion.uses_count || 0} uses</span>
                        </div>
                        {promotion.max_uses && (
                          <span>of {promotion.max_uses}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-1 mt-2">
                        <Calendar className="h-3 w-3" />
                        <span>{formatDate(promotion.valid_from)} - {formatDate(promotion.valid_until)}</span>
                      </div>
                    </div>
                    <div className="flex gap-2 pt-2 border-t">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setEditingPromo(promotion)
                          setForm({
                            name: promotion.name,
                            description: promotion.description || '',
                            discount_type: promotion.discount_type,
                            discount_value: String(promotion.discount_value),
                            minimum_order_amount: String(promotion.minimum_order_amount || ''),
                            maximum_discount: promotion.maximum_discount ? String(promotion.maximum_discount) : '',
                            valid_from: promotion.valid_from.split('T')[0],
                            valid_until: promotion.valid_until.split('T')[0],
                            max_uses: promotion.max_uses ? String(promotion.max_uses) : '',
                            max_uses_per_user: String(promotion.max_uses_per_user || 1),
                            code: promotion.code || '',
                            offer_type: promotion.offer_type,
                          })
                          setShowCreateModal(true)
                        }}
                      >
                        <Edit className="h-3 w-3 mr-1" />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => togglePromotion.mutate({ id: promotion.id, isActive: !promotion.is_active })}
                      >
                        {promotion.is_active ? 'Deactivate' : 'Activate'}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-red-600 hover:text-red-700"
                        onClick={() => {
                          if (confirm('Are you sure you want to delete this promotion?')) {
                            deletePromotion.mutate(promotion.id)
                          }
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })
          ) : (
            <div className="col-span-full text-center py-12">
              <p className="text-zomato-gray">No promotions yet. Create your first promotion!</p>
            </div>
          )}
        </div>
      </div>

      {showCreateModal && (
        <PromotionModal
          form={form}
          setForm={setForm}
          formError={formError}
          onSubmit={handleSubmit}
          onClose={() => {
            setShowCreateModal(false)
            setEditingPromo(null)
            resetForm()
          }}
          isEditing={!!editingPromo}
          isLoading={createPromotion.isPending || updatePromotion.isPending}
        />
      )}
    </div>
  )
}

function PromotionModal({
  form,
  setForm,
  formError,
  onSubmit,
  onClose,
  isEditing,
  isLoading,
}: {
  form: any
  setForm: (form: any) => void
  formError: string
  onSubmit: () => void
  onClose: () => void
  isEditing: boolean
  isLoading: boolean
}) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="bg-white max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-xl">{isEditing ? 'Edit' : 'Create'} Promotion</CardTitle>
            <Button variant="ghost" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Promotion Name</label>
              <Input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="e.g., Weekend Special"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                className="w-full p-2 border rounded"
                rows={2}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Promotion description"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Discount Type</label>
              <select
                className="w-full p-2 border rounded"
                value={form.discount_type}
                onChange={(e) => setForm({ ...form, discount_type: e.target.value })}
              >
                <option value="PERCENTAGE">Percentage</option>
                <option value="FIXED">Fixed Amount</option>
                <option value="FREE_DELIVERY">Free Delivery</option>
                <option value="BUY_ONE_GET_ONE">Buy 1 Get 1</option>
                <option value="CASHBACK">Cashback</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">
                Discount Value {form.discount_type === 'PERCENTAGE' ? '(%)' : '(₹)'}
              </label>
              <Input
                type="number"
                value={form.discount_value}
                onChange={(e) => setForm({ ...form, discount_value: e.target.value })}
                placeholder="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Min Order Amount (₹)</label>
              <Input
                type="number"
                value={form.minimum_order_amount}
                onChange={(e) => setForm({ ...form, minimum_order_amount: e.target.value })}
                placeholder="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Max Discount (₹)</label>
              <Input
                type="number"
                value={form.maximum_discount}
                onChange={(e) => setForm({ ...form, maximum_discount: e.target.value })}
                placeholder="Optional"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Promo Code</label>
              <Input
                value={form.code}
                onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                placeholder="Optional"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Max Uses</label>
              <Input
                type="number"
                value={form.max_uses}
                onChange={(e) => setForm({ ...form, max_uses: e.target.value })}
                placeholder="Unlimited if empty"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Max Uses Per User</label>
              <Input
                type="number"
                value={form.max_uses_per_user}
                onChange={(e) => setForm({ ...form, max_uses_per_user: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Valid From</label>
              <Input
                type="date"
                value={form.valid_from}
                onChange={(e) => setForm({ ...form, valid_from: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Valid Until</label>
              <Input
                type="date"
                value={form.valid_until}
                onChange={(e) => setForm({ ...form, valid_until: e.target.value })}
              />
            </div>
          </div>
          {formError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              {formError}
            </div>
          )}
          <div className="flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={onSubmit}
              disabled={isLoading}
              className="bg-zomato-red hover:bg-zomato-darkRed text-white"
            >
              {isLoading ? 'Saving...' : isEditing ? 'Update' : 'Create'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


