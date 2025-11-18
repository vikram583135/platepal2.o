import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useCartStore } from '../stores/cartStore'
import { useAuthStore } from '../stores/authStore'
import { useQuery, useMutation } from '@tanstack/react-query'
import apiClient from '@/packages/api/client'
import { Button } from '@/packages/ui/components/button'
import { Input } from '@/packages/ui/components/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Badge } from '@/packages/ui/components/badge'
import { formatCurrency } from '@/packages/utils/format'
import PaymentMethodSelector from '../components/PaymentMethodSelector'

export default function CheckoutPage() {
  const navigate = useNavigate()
  const { items, restaurantId, getTotal, clearCart, isGuest, setGuestMode } = useCartStore()
  const { isAuthenticated } = useAuthStore()
  const [selectedAddress, setSelectedAddress] = useState<number | null>(null)
  const [tip, setTip] = useState(0)
  const [paymentMethod, setPaymentMethod] = useState<string | null>(null)
  const [selectedCard, setSelectedCard] = useState<any>(null)
  const [contactlessDelivery, setContactlessDelivery] = useState(false)

  // Check if user needs to login
  useEffect(() => {
    if (!isAuthenticated && !isGuest) {
      setGuestMode(true)
    } else if (isAuthenticated && isGuest) {
      setGuestMode(false)
    }
  }, [isAuthenticated, isGuest, setGuestMode])

  const { data: addresses } = useQuery({
    queryKey: ['addresses'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/addresses/')
      return response.data.results || response.data
    },
    enabled: isAuthenticated, // Only fetch if authenticated
  })

  const { data: savedCards } = useQuery({
    queryKey: ['payment-methods'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/payment-methods/')
      return response.data.results || response.data || []
    },
    enabled: isAuthenticated,
  })

  // Calculate subtotal early for use in queries
  const subtotal = getTotal()
  const tax = subtotal * 0.1
  const total = subtotal + tax + tip

  const { data: availableOffers } = useQuery({
    queryKey: ['available-offers', restaurantId, paymentMethod, subtotal],
    queryFn: async () => {
      const response = await apiClient.get(`/restaurants/promotions/available/?restaurant_id=${restaurantId}&order_amount=${subtotal}&payment_method=${paymentMethod || ''}`)
      return response.data.offers || []
    },
    enabled: !!restaurantId && subtotal > 0,
  })

  const createOrderMutation = useMutation({
    mutationFn: async (orderData: any) => {
      const response = await apiClient.post('/orders/orders/', orderData)
      return response.data
    },
    onSuccess: async (orderData) => {
      // If COD, proceed directly
      if (paymentMethod === 'CASH') {
        clearCart()
        navigate(`/orders/${orderData.id}`)
        return
      }

      // For other payment methods, create payment intent
      if (paymentMethod && paymentMethod !== 'CASH') {
        try {
          const paymentResponse = await apiClient.post('/payments/create_payment_intent/', {
            order_id: orderData.id,
            payment_method: paymentMethod,
            amount: total,
          })
          
          // Mock payment confirmation (in production, integrate with gateway)
          await apiClient.post('/payments/confirm_payment/', {
            order_id: orderData.id,
            payment_intent_id: paymentResponse.data.payment_intent_id,
            transaction_id: `TXN_${Date.now()}`,
            payment_method: paymentMethod,
          })
          
          clearCart()
          navigate(`/orders/${orderData.id}`)
        } catch (error: any) {
          const errorMsg = error.response?.data?.detail || error.message || 'Payment processing failed'
          alert(`${errorMsg}. Please try again.`)
        }
      } else {
        clearCart()
        navigate(`/orders/${orderData.id}`)
      }
    },
    onError: (error: any) => {
      // Extract error message from various possible formats
      let errorMessage = 'Order creation failed. Please try again.'
      
      if (error.response?.data) {
        const errorData = error.response.data
        
        // Handle DRF error format
        if (errorData.error) {
          errorMessage = typeof errorData.error === 'string' 
            ? errorData.error 
            : errorData.error.message || errorData.error
        }
        // Handle field errors
        else if (errorData.items?.[0]) {
          errorMessage = errorData.items[0]
        }
        else if (errorData.restaurant_id?.[0]) {
          errorMessage = errorData.restaurant_id[0]
        }
        else if (errorData.delivery_address_id?.[0]) {
          errorMessage = errorData.delivery_address_id[0]
        }
        else if (errorData.non_field_errors?.[0]) {
          errorMessage = errorData.non_field_errors[0]
        }
        // Handle details object
        else if (errorData.details) {
          if (typeof errorData.details === 'string') {
            errorMessage = errorData.details
          } else if (errorData.details.message) {
            errorMessage = errorData.details.message
          } else if (errorData.details.detail) {
            errorMessage = errorData.details.detail
          }
        }
        // Handle string response
        else if (typeof errorData === 'string') {
          errorMessage = errorData
        }
        // Handle detail field
        else if (errorData.detail) {
          errorMessage = errorData.detail
        }
      } else if (error.message) {
        errorMessage = error.message
      }
      
      alert(errorMessage)
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedAddress || !restaurantId) {
      alert('Please select a delivery address')
      return
    }
    if (!paymentMethod) {
      alert('Please select a payment method')
      return
    }

    const orderItems = items.map((item) => ({
      menu_item_id: item.menuItem.id,
      quantity: item.quantity,
      selected_modifiers: item.selectedModifiers.map((m) => ({
        modifier_id: m.id,
        name: m.name,
        price: m.price,
      })),
    }))

    createOrderMutation.mutate({
      restaurant_id: restaurantId,
      delivery_address_id: selectedAddress,
      order_type: 'DELIVERY',
      items: orderItems,
      tip_amount: tip,
      contactless_delivery: contactlessDelivery,
    })
  }

  // Show login prompt for guests
  if (!isAuthenticated) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">Login Required</h2>
            <p className="text-gray-600 mb-6">
              Please login or create an account to complete your order.
            </p>
            <div className="flex gap-4 justify-center">
              <Link to="/login">
                <Button>Login</Button>
              </Link>
              <Link to="/signup">
                <Button variant="outline">Sign Up</Button>
              </Link>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              Your cart will be saved and available after login.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Check if cart is empty
  if (!items || items.length === 0 || !restaurantId) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">Your Cart is Empty</h2>
            <p className="text-gray-600 mb-6">
              Add items to your cart before checking out.
            </p>
            <Link to="/restaurants">
              <Button>Browse Restaurants</Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Checkout</h1>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Delivery Address</CardTitle>
              </CardHeader>
              <CardContent>
                {addresses && addresses.length > 0 ? (
                  addresses.map((address: any) => (
                    <label
                      key={address.id}
                      className="flex items-start gap-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50"
                    >
                      <input
                        type="radio"
                        name="address"
                        value={address.id}
                        checked={selectedAddress === address.id}
                        onChange={() => setSelectedAddress(address.id)}
                        className="mt-1"
                      />
                      <div>
                        <div className="font-semibold">{address.label}</div>
                        <div className="text-sm text-gray-600">
                          {address.street}, {address.city}, {address.state} {address.postal_code}
                        </div>
                      </div>
                    </label>
                  ))
                ) : (
                  <div className="text-center py-4">
                    <p className="text-gray-600 mb-4">No addresses saved</p>
                    <Link to="/profile">
                      <Button variant="outline">Add Address</Button>
                    </Link>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Tip</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2 mb-4">
                  {[0, 5, 10, 15, 20].map((amount) => (
                    <Button
                      key={amount}
                      type="button"
                      variant={tip === amount ? 'default' : 'outline'}
                      onClick={() => setTip(amount)}
                    >
                      ₹{amount}
                    </Button>
                  ))}
                </div>
                <Input
                  type="number"
                  placeholder="Custom tip"
                  value={tip || ''}
                  onChange={(e) => setTip(parseFloat(e.target.value) || 0)}
                  min="0"
                  step="0.01"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Payment Method</CardTitle>
              </CardHeader>
              <CardContent>
                <PaymentMethodSelector
                  selectedMethod={paymentMethod}
                  onSelectMethod={setPaymentMethod}
                  savedCards={savedCards}
                  onCardSelect={setSelectedCard}
                  selectedCard={selectedCard}
                />
              </CardContent>
            </Card>

            {/* Available Offers */}
            {availableOffers && availableOffers.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Available Offers</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {availableOffers.slice(0, 3).map((offer: any) => (
                      <div
                        key={offer.id}
                        className="p-3 border rounded-lg hover:border-primary-300 cursor-pointer"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-medium text-sm">{offer.name}</div>
                            <div className="text-xs text-gray-600">{offer.discount_display}</div>
                            {offer.minimum_order_amount > 0 && (
                              <div className="text-xs text-gray-500">
                                Min: {formatCurrency(offer.minimum_order_amount, 'INR')}
                              </div>
                            )}
                          </div>
                          {offer.code && (
                            <Badge variant="outline" className="text-xs">
                              {offer.code}
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Safety Features */}
            <Card>
              <CardHeader>
                <CardTitle>Safety Options</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">Contactless Delivery</div>
                    <div className="text-sm text-gray-600">
                      Leave order at door, no contact required
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    id="contactless"
                    checked={contactlessDelivery}
                    onChange={(e) => setContactlessDelivery(e.target.checked)}
                    className="w-5 h-5"
                  />
                </div>
                {contactlessDelivery && (
                  <div className="text-sm text-blue-600">
                    ✓ OTP will be required for delivery verification
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div>
            <Card>
              <CardHeader>
                <CardTitle>Order Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between">
                    <span>Subtotal</span>
                    <span>{formatCurrency(subtotal, 'INR')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tax</span>
                    <span>{formatCurrency(tax, 'INR')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tip</span>
                    <span>{formatCurrency(tip, 'INR')}</span>
                  </div>
                  <div className="border-t pt-2 flex justify-between font-semibold text-lg">
                    <span>Total</span>
                    <span>{formatCurrency(total, 'INR')}</span>
                  </div>
                </div>
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={!selectedAddress || createOrderMutation.isPending}
                >
                  {createOrderMutation.isPending ? 'Placing Order...' : 'Place Order'}
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  )
}

