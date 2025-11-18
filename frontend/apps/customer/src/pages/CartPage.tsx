import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useCartStore } from '../stores/cartStore'
import { useMutation } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { Card, CardContent } from '@/packages/ui/components/card'
import { Plus, Minus, Trash2, Tag, Clock, X } from 'lucide-react'
import { formatCurrency } from '@/packages/utils/format'

export default function CartPage() {
  const { items, restaurantId, updateQuantity, removeItem, getTotal } = useCartStore()
  const [couponCode, setCouponCode] = useState('')
  const [appliedCoupon, setAppliedCoupon] = useState<any>(null)
  const [couponError, setCouponError] = useState('')

  const subtotal = getTotal()
  const gstRate = 0.18 // 18% GST
  const packagingFee = 5 // Fixed packaging fee
  const platformFee = subtotal > 0 ? Math.max(5, subtotal * 0.02) : 0 // 2% or min ₹5
  const discount = appliedCoupon ? calculateDiscount(subtotal, appliedCoupon) : 0
  const finalSubtotal = subtotal - discount
  const finalGst = finalSubtotal * gstRate
  const finalTotal = finalSubtotal + finalGst + packagingFee + platformFee

  // Calculate ETA (mock - in production, get from restaurant)
  const estimatedDeliveryTime = items.length > 0 ? 30 : 0 // minutes

  function calculateDiscount(amount: number, coupon: any) {
    if (coupon.discount_type === 'PERCENTAGE') {
      const discount = amount * (parseFloat(coupon.discount_value) / 100)
      if (coupon.maximum_discount) {
        return Math.min(discount, parseFloat(coupon.maximum_discount))
      }
      return discount
    } else if (coupon.discount_type === 'FIXED') {
      return Math.min(parseFloat(coupon.discount_value), amount)
    }
    return 0
  }

  const validateCouponMutation = useMutation({
    mutationFn: async (code: string) => {
      const response = await apiClient.post('/restaurants/promotions/validate/', {
        code,
        restaurant_id: restaurantId,
        order_amount: subtotal,
      })
      return response.data
    },
    onSuccess: (data) => {
      if (data.valid) {
        setAppliedCoupon(data.promotion)
        setCouponError('')
      } else {
        setCouponError(data.message || 'Invalid coupon code')
        setAppliedCoupon(null)
      }
    },
    onError: (error: any) => {
      setCouponError(error.response?.data?.message || 'Failed to validate coupon')
      setAppliedCoupon(null)
    },
  })

  const handleApplyCoupon = () => {
    if (!couponCode.trim()) {
      setCouponError('Please enter a coupon code')
      return
    }
    if (!restaurantId) {
      setCouponError('Unable to apply coupon. Please try again.')
      return
    }
    setCouponError('')
    validateCouponMutation.mutate(couponCode.trim().toUpperCase())
  }

  const handleRemoveCoupon = () => {
    setAppliedCoupon(null)
    setCouponCode('')
    setCouponError('')
  }

  if (items.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <h2 className="text-2xl font-semibold mb-4">Your cart is empty</h2>
          <Link to="/restaurants">
            <Button>Browse Restaurants</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Shopping Cart</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-4">
          {items.map((item) => {
            const itemTotal = (item.menuItem.price + item.selectedModifiers.reduce((sum, m) => sum + m.price, 0)) * item.quantity
            return (
              <Card key={item.menuItem.id}>
                <CardContent className="p-4">
                  <div className="flex gap-4">
                    {(item.menuItem.image || item.menuItem.image_url) && (
                      <img
                        src={item.menuItem.image || item.menuItem.image_url}
                        alt={item.menuItem.name}
                        className="w-20 h-20 object-cover rounded"
                      />
                    )}
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1">{item.menuItem.name}</h3>
                      <p className="text-sm text-gray-600 mb-2">
                        {formatCurrency(item.menuItem.price, 'INR')} each
                      </p>
                      {item.selectedModifiers.length > 0 && (
                        <div className="text-xs text-gray-500 mb-2">
                          {item.selectedModifiers.map((m) => m.name).join(', ')}
                        </div>
                      )}
                      <div className="flex items-center justify-between mt-4">
                        <div className="flex items-center gap-2">
                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => updateQuantity(item.menuItem.id, item.quantity - 1)}
                          >
                            <Minus className="w-4 h-4" />
                          </Button>
                          <span className="w-8 text-center">{item.quantity}</span>
                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => updateQuantity(item.menuItem.id, item.quantity + 1)}
                          >
                            <Plus className="w-4 h-4" />
                          </Button>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="font-semibold">{formatCurrency(itemTotal, 'INR')}</span>
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => removeItem(item.menuItem.id)}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>

        <div className="lg:col-span-1 space-y-4">
          {/* Coupon Section */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <Tag className="w-5 h-5 text-primary-600" />
                <h3 className="font-semibold">Apply Coupon</h3>
              </div>
              {appliedCoupon ? (
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-2 bg-green-50 border border-green-200 rounded">
                    <div>
                      <div className="font-medium text-green-800">{appliedCoupon.name}</div>
                      <div className="text-xs text-green-600">{appliedCoupon.code}</div>
                    </div>
                    <button onClick={handleRemoveCoupon}>
                      <X className="w-4 h-4 text-green-600" />
                    </button>
                  </div>
                  <div className="text-sm text-green-600">
                    You saved {formatCurrency(discount, 'INR')}!
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Enter coupon code"
                      value={couponCode}
                      onChange={(e) => {
                        setCouponCode(e.target.value)
                        setCouponError('')
                      }}
                      onKeyPress={(e) => e.key === 'Enter' && handleApplyCoupon()}
                    />
                    <Button
                      onClick={handleApplyCoupon}
                      disabled={validateCouponMutation.isPending}
                    >
                      Apply
                    </Button>
                  </div>
                  {couponError && (
                    <div className="text-sm text-red-600">{couponError}</div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Order Summary */}
          <Card>
            <CardContent className="p-6">
              <h2 className="text-xl font-semibold mb-4">Order Summary</h2>
              
              {/* ETA */}
              {estimatedDeliveryTime > 0 && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex items-center gap-2 text-blue-800">
                    <Clock className="w-4 h-4" />
                    <span className="text-sm font-medium">Estimated Delivery: {estimatedDeliveryTime} min</span>
                  </div>
                </div>
              )}

              {/* Bill Breakdown */}
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span>Item Total</span>
                  <span>{formatCurrency(subtotal, 'INR')}</span>
                </div>
                
                {appliedCoupon && (
                  <div className="flex justify-between text-sm text-green-600">
                    <span>Discount ({appliedCoupon.code})</span>
                    <span>-{formatCurrency(discount, 'INR')}</span>
                  </div>
                )}

                <div className="flex justify-between text-sm">
                  <span>Subtotal</span>
                  <span>{formatCurrency(finalSubtotal, 'INR')}</span>
                </div>

                <div className="flex justify-between text-sm">
                  <span>GST (18%)</span>
                  <span>{formatCurrency(finalGst, 'INR')}</span>
                </div>

                <div className="flex justify-between text-sm">
                  <span>Packaging Charges</span>
                  <span>{formatCurrency(packagingFee, 'INR')}</span>
                </div>

                <div className="flex justify-between text-sm">
                  <span>Platform Fee</span>
                  <span>{formatCurrency(platformFee, 'INR')}</span>
                </div>

                <div className="border-t pt-2 mt-2 flex justify-between font-semibold text-lg">
                  <span>Total</span>
                  <span>{formatCurrency(finalTotal, 'INR')}</span>
                </div>
              </div>

              <Link to="/checkout" className="block">
                <Button className="w-full" size="lg">
                  Proceed to Checkout
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
