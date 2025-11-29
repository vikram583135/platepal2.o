import { useState, useEffect, useCallback } from 'react'
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
  const cartStore = useCartStore()
  const { items, restaurantId: storeRestaurantId, getTotal, clearCart, isGuest, setGuestMode, getItemCount } = cartStore
  const { isAuthenticated } = useAuthStore()
  const [selectedAddress, setSelectedAddress] = useState<number | null>(null)
  const [tip, setTip] = useState(0)
  const [paymentMethod, setPaymentMethod] = useState<string | null>(null)
  const [selectedCard, setSelectedCard] = useState<any>(null)
  const [paymentDetails, setPaymentDetails] = useState<any>(null)
  const [contactlessDelivery, setContactlessDelivery] = useState(false)
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({})
  const [isHydrated, setIsHydrated] = useState(false)

  // Use restaurantId from store
  // If missing, we'll handle it during validation and order creation
  const restaurantId = storeRestaurantId

  // Wait for cart store to hydrate from localStorage
  useEffect(() => {
    let retryCount = 0
    const maxRetries = 5

    const checkHydration = () => {
      // Check localStorage directly as fallback
      try {
        const stored = localStorage.getItem('cart-storage')
        if (stored) {
          const parsed = JSON.parse(stored)
          const hasStoredItems = parsed?.state?.items && Array.isArray(parsed.state.items) && parsed.state.items.length > 0

          if (hasStoredItems) {
            // Items exist in localStorage, wait a bit more for Zustand to hydrate
            setTimeout(() => {
              setIsHydrated(true)
            }, 100)
            return
          }
        }
      } catch (e) {
        // localStorage read failed, continue with normal check
      }

      // Check store state
      const storeState = cartStore
      const hasItems = storeState.items && Array.isArray(storeState.items) && storeState.items.length > 0
      const itemCount = storeState.getItemCount()

      // If items exist or itemCount > 0, we're hydrated
      if (hasItems || itemCount > 0) {
        setIsHydrated(true)
        return
      }

      // Retry mechanism for slow devices
      if (retryCount < maxRetries) {
        retryCount++
        setTimeout(checkHydration, 100 * retryCount)
      } else {
        // Max retries reached, consider hydrated anyway
        setIsHydrated(true)
      }
    }

    // Initial check
    const timer = setTimeout(checkHydration, 50)

    return () => clearTimeout(timer)
  }, [items, cartStore])

  // Check if user needs to login
  useEffect(() => {
    if (!isAuthenticated && !isGuest) {
      setGuestMode(true)
    } else if (isAuthenticated && isGuest) {
      setGuestMode(false)
    }
  }, [isAuthenticated, isGuest, setGuestMode])

  const { data: addresses, isLoading: addressesLoading, error: addressesError } = useQuery({
    queryKey: ['addresses'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/auth/addresses/')
        return response.data.results || response.data || []
      } catch (error: any) {
        console.error('Failed to fetch addresses:', error)
        throw error
      }
    },
    enabled: isAuthenticated, // Only fetch if authenticated
    retry: 1,
  })

  // Auto-select default address or first address
  useEffect(() => {
    if (addresses && addresses.length > 0 && !selectedAddress) {
      // First try to find default address
      const defaultAddress = addresses.find((addr: any) => addr.is_default)
      if (defaultAddress) {
        setSelectedAddress(defaultAddress.id)
      } else {
        // Otherwise select first address
        setSelectedAddress(addresses[0].id)
      }
    }
  }, [addresses, selectedAddress])

  const { data: savedCards, isLoading: cardsLoading } = useQuery({
    queryKey: ['payment-methods'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/auth/payment-methods/')
        return response.data.results || response.data || []
      } catch (error: any) {
        console.error('Failed to fetch payment methods:', error)
        return []
      }
    },
    enabled: isAuthenticated,
    retry: 1,
  })

  // Calculate subtotal early for use in queries
  const subtotal = getTotal()
  const tax = subtotal * 0.1
  const total = subtotal + tax + tip

  const { data: availableOffers } = useQuery({
    queryKey: ['available-offers', restaurantId, paymentMethod, subtotal],
    queryFn: async () => {
      try {
        if (!restaurantId) return []
        const response = await apiClient.get(`/restaurants/promotions/available/?restaurant_id=${restaurantId}&order_amount=${subtotal}&payment_method=${paymentMethod || ''}`)
        return response.data.offers || []
      } catch (error: any) {
        console.error('Failed to fetch offers:', error)
        return []
      }
    },
    enabled: !!restaurantId && subtotal > 0,
    retry: 1,
  })

  const createOrderMutation = useMutation({
    mutationFn: async (orderData: any) => {
      try {
        const response = await apiClient.post('/orders/orders/', orderData)
        return response.data
      } catch (error: any) {
        console.error('Order creation error:', error)
        throw error
      }
    },
    onSuccess: async (orderData) => {
      // If COD, proceed directly
      if (paymentMethod === 'CASH') {
        clearCart()
        navigate(`/orders/${orderData.id}`, { state: { orderPlaced: true } })
        return
      }

      // For other payment methods, create payment intent
      if (paymentMethod && paymentMethod !== 'CASH') {
        try {
          const paymentPayload: any = {
            order_id: orderData.id,
            payment_method: paymentMethod,
            amount: total,
          }

          // Add payment details based on method
          if (paymentMethod === 'CARD' && selectedCard) {
            paymentPayload.card_id = selectedCard.id
          } else if (paymentMethod === 'CARD' && paymentDetails) {
            paymentPayload.card_data = paymentDetails
          } else if (paymentMethod === 'UPI' && paymentDetails?.upiId) {
            paymentPayload.upi_id = paymentDetails.upiId
          } else if (paymentMethod === 'WALLET' && paymentDetails?.walletProvider) {
            paymentPayload.wallet_provider = paymentDetails.walletProvider
          }

          const paymentResponse = await apiClient.post('/payments/create_payment_intent/', paymentPayload)

          const { payment_intent_id } = paymentResponse.data

          // In a real integration, we would use the client_secret with Stripe/Razorpay SDK here
          // For now, we simulate the confirmation call to our backend which verifies with the gateway

          const confirmPayload: any = {
            order_id: orderData.id,
            payment_intent_id: payment_intent_id,
            payment_method: paymentMethod,
          }

          // Add payment details to confirmation
          if (paymentMethod === 'UPI' && paymentDetails?.upiId) {
            confirmPayload.upi_id = paymentDetails.upiId
          } else if (paymentMethod === 'WALLET' && paymentDetails?.walletProvider) {
            confirmPayload.wallet_provider = paymentDetails.walletProvider
          }

          const confirmResponse = await apiClient.post('/payments/confirm_payment/', confirmPayload)

          if (confirmResponse.data.status === 'failed') {
            throw new Error(confirmResponse.data.message || 'Payment failed')
          }

          clearCart()
          navigate(`/orders/${orderData.id}`, { state: { orderPlaced: true } })
        } catch (error: any) {
          console.error('Payment Processing Error:', error)
          const errorMsg = error.response?.data?.message || error.response?.data?.error || error.message || 'Payment processing failed'
          alert(`Payment failed: ${errorMsg}. Your order has been created but payment is pending.`)
          // Navigate to order page with pending payment status
          navigate(`/orders/${orderData.id}`, { state: { paymentPending: true } })
        }
      } else {
        clearCart()
        navigate(`/orders/${orderData.id}`, { state: { orderPlaced: true } })
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

  // Validate form data
  const validateForm = useCallback((): boolean => {
    const errors: Record<string, string> = {}

    if (!selectedAddress) {
      errors.address = 'Please select a delivery address'
    }

    if (!paymentMethod) {
      errors.payment = 'Please select a payment method'
    }

    // Validate payment method details
    if (paymentMethod === 'CARD' && !selectedCard && !paymentDetails) {
      errors.payment = 'Please select a saved card or enter card details'
    } else if (paymentMethod === 'UPI' && (!paymentDetails || !paymentDetails.upiId)) {
      errors.payment = 'Please enter your UPI ID'
    } else if (paymentMethod === 'WALLET' && (!paymentDetails || !paymentDetails.walletProvider)) {
      errors.payment = 'Please select a wallet provider'
    }

    // Validate tip amount
    if (tip < 0) {
      errors.tip = 'Tip amount cannot be negative'
    } else if (tip > 1000) {
      errors.tip = 'Tip amount cannot exceed ₹1000'
    }

    // Validate cart
    if (!items || items.length === 0) {
      errors.cart = 'Your cart is empty'
    }

    if (!restaurantId) {
      // Try to recover restaurantId from localStorage if possible or warn user
      console.error('Restaurant ID missing in checkout')
      errors.restaurant = 'Session expired or invalid. Please return to the restaurant page and add items again.'
    }

    setValidationErrors(errors)
    return Object.keys(errors).length === 0
  }, [selectedAddress, paymentMethod, selectedCard, paymentDetails, tip, items, restaurantId])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setValidationErrors({})

    if (!validateForm()) {
      // Show first error
      const firstError = Object.values(validationErrors)[0]
      if (firstError) {
        alert(firstError)
      }
      return
    }

    // Validate items structure before mapping - handle multiple formats
    if (!items || !Array.isArray(items) || items.length === 0) {
      alert('Cart items are invalid. Please add items to your cart again.')
      return
    }

    const orderItems = items
      .filter((item) => {
        // Validate item structure
        return item && item.menuItem && item.menuItem.id
      })
      .map((item) => {
        const menuItem = item.menuItem
        const modifiers = item.selectedModifiers || []

        return {
          menu_item_id: menuItem.id,
          quantity: item.quantity || 1,
          selected_modifiers: modifiers.map((m: any) => ({
            modifier_id: m.id,
            name: m.name || '',
            price: m.price || 0,
          })),
        }
      })
      .filter((item) => item.menu_item_id) // Final filter to ensure we have valid IDs

    if (orderItems.length === 0) {
      alert('No valid items in cart. Please add items to your cart again.')
      if (import.meta.env.DEV) {
        console.error('Order items validation failed:', items)
      }
      return
    }

    if (import.meta.env.DEV) {
      console.log('Order items prepared:', orderItems)
    }

    if (!restaurantId) {
      alert('Restaurant information is missing. Please add items to your cart again from a restaurant page.')
      if (import.meta.env.DEV) {
        console.error('Cannot create order: restaurantId is missing', { items, restaurantId })
      }
      return
    }

    createOrderMutation.mutate({
      restaurant_id: restaurantId,
      delivery_address_id: selectedAddress,
      order_type: 'DELIVERY',
      items: orderItems,
      tip_amount: Math.max(0, Math.min(tip, 1000)), // Clamp tip between 0 and 1000
      contactless_delivery: contactlessDelivery,
    })
  }

  // Handle payment details from PaymentMethodSelector
  const handlePaymentDetailsChange = useCallback((details: any) => {
    setPaymentDetails(details)
    setValidationErrors((prev) => {
      const newErrors = { ...prev }
      delete newErrors.payment
      return newErrors
    })
  }, [])

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

  // Wait for hydration before checking cart
  if (!isHydrated) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-gray-600">Loading cart...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Check if cart is empty - use multiple checks with fallbacks
  const itemCount = getItemCount()
  const subtotalCheck = getTotal()
  const rawItemsLength = items?.length || 0

  // Multiple checks to determine if we have items:
  // 1. Validated item count > 0
  // 2. Raw items array has items
  // 3. Subtotal > 0
  // Show form if ANY of these are true (be very lenient)
  const hasItemsByCount = itemCount > 0
  const hasItemsByArray = rawItemsLength > 0
  const hasItemsByTotal = subtotalCheck > 0

  // Show form if we have items by any measure
  // Don't require restaurantId to show form - we'll extract it or handle it during order creation
  const shouldShowForm = hasItemsByCount || hasItemsByArray || hasItemsByTotal

  // Debug logging (remove in production)
  if (import.meta.env.DEV) {
    console.log('CheckoutPage - Cart State:', {
      itemCount,
      itemsLength: rawItemsLength,
      restaurantId,
      subtotal: subtotalCheck,
      hasItemsByCount,
      hasItemsByArray,
      hasItemsByTotal,
      shouldShowForm,
      items: items?.map((item: any) => ({
        hasMenuItem: !!(item?.menuItem || item?.menu_item),
        menuItemId: item?.menuItem?.id || item?.menu_item?.id || item?.menu_item,
        quantity: item?.quantity,
        structure: Object.keys(item || {}),
      })),
    })
  }

  // Only show empty message if we're absolutely sure there are no items
  if (!shouldShowForm) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">Your Cart is Empty</h2>
            <p className="text-gray-600 mb-6">
              Add items to your cart before checking out.
            </p>
            <div className="flex gap-4 justify-center">
              <Link to="/cart">
                <Button variant="outline">View Cart</Button>
              </Link>
              <Link to="/restaurants">
                <Button>Browse Restaurants</Button>
              </Link>
            </div>
            {import.meta.env.DEV && (
              <div className="mt-4 p-4 bg-gray-100 rounded text-left text-xs">
                <strong>Debug Info:</strong>
                <pre>{JSON.stringify({ itemCount, rawItemsLength, subtotalCheck, restaurantId }, null, 2)}</pre>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-3xl font-bold mb-8">Checkout</h1>

      {/* Debug info in development */}
      {import.meta.env.DEV && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded text-xs">
          <strong>Debug:</strong> Form is rendering. Items: {rawItemsLength}, Count: {itemCount}, Total: ₹{subtotalCheck.toFixed(2)}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Delivery Address</CardTitle>
              </CardHeader>
              <CardContent>
                {addressesLoading ? (
                  <div className="text-center py-4">
                    <p className="text-gray-600">Loading addresses...</p>
                  </div>
                ) : addressesError ? (
                  <div className="text-center py-4">
                    <p className="text-red-600 mb-4">Failed to load addresses. Please try again.</p>
                    <Button variant="outline" onClick={() => window.location.reload()}>Retry</Button>
                  </div>
                ) : addresses && addresses.length > 0 ? (
                  <>
                    {addresses.map((address: any) => (
                      <label
                        key={address.id}
                        className={`flex items-start gap-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50 ${selectedAddress === address.id ? 'border-primary-600 bg-primary-50' : ''
                          }`}
                      >
                        <input
                          type="radio"
                          name="address"
                          value={address.id}
                          checked={selectedAddress === address.id}
                          onChange={() => {
                            setSelectedAddress(address.id)
                            setValidationErrors((prev) => {
                              const newErrors = { ...prev }
                              delete newErrors.address
                              return newErrors
                            })
                          }}
                          className="mt-1"
                          disabled={createOrderMutation.isPending}
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold">{address.label}</span>
                            {address.is_default && (
                              <Badge variant="outline" className="text-xs">Default</Badge>
                            )}
                          </div>
                          <div className="text-sm text-gray-600">
                            {address.street}, {address.city}, {address.state} {address.postal_code}
                          </div>
                        </div>
                      </label>
                    ))}
                    {validationErrors.address && (
                      <p className="text-red-600 text-sm mt-2">{validationErrors.address}</p>
                    )}
                  </>
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
                <div className="flex gap-2 mb-4 flex-wrap">
                  {[0, 5, 10, 15, 20].map((amount) => (
                    <Button
                      key={amount}
                      type="button"
                      variant={tip === amount ? 'default' : 'outline'}
                      onClick={() => {
                        setTip(amount)
                        setValidationErrors((prev) => {
                          const newErrors = { ...prev }
                          delete newErrors.tip
                          return newErrors
                        })
                      }}
                      disabled={createOrderMutation.isPending}
                    >
                      ₹{amount}
                    </Button>
                  ))}
                </div>
                <Input
                  type="number"
                  placeholder="Custom tip"
                  value={tip || ''}
                  onChange={(e) => {
                    const value = parseFloat(e.target.value) || 0
                    setTip(value)
                    setValidationErrors((prev) => {
                      const newErrors = { ...prev }
                      if (value < 0 || value > 1000) {
                        newErrors.tip = value < 0 ? 'Tip cannot be negative' : 'Tip cannot exceed ₹1000'
                      } else {
                        delete newErrors.tip
                      }
                      return newErrors
                    })
                  }}
                  min="0"
                  max="1000"
                  step="0.01"
                  disabled={createOrderMutation.isPending}
                />
                {validationErrors.tip && (
                  <p className="text-red-600 text-sm mt-2">{validationErrors.tip}</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Payment Method</CardTitle>
              </CardHeader>
              <CardContent>
                {cardsLoading ? (
                  <div className="text-center py-4">
                    <p className="text-gray-600">Loading payment methods...</p>
                  </div>
                ) : (
                  <>
                    <PaymentMethodSelector
                      selectedMethod={paymentMethod}
                      onSelectMethod={(method) => {
                        setPaymentMethod(method)
                        setValidationErrors((prev) => {
                          const newErrors = { ...prev }
                          delete newErrors.payment
                          return newErrors
                        })
                      }}
                      savedCards={savedCards || []}
                      onCardSelect={setSelectedCard}
                      selectedCard={selectedCard}
                      onPaymentDetailsChange={handlePaymentDetailsChange}
                      disabled={createOrderMutation.isPending}
                    />
                    {validationErrors.payment && (
                      <p className="text-red-600 text-sm mt-2">{validationErrors.payment}</p>
                    )}
                  </>
                )}
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
                  disabled={
                    !selectedAddress ||
                    !paymentMethod ||
                    createOrderMutation.isPending ||
                    addressesLoading ||
                    cardsLoading
                  }
                >
                  {createOrderMutation.isPending ? (
                    <span className="flex items-center gap-2">
                      <span className="animate-spin">⏳</span>
                      Placing Order...
                    </span>
                  ) : (
                    'Place Order'
                  )}
                </Button>
                {Object.keys(validationErrors).length > 0 && (
                  <p className="text-red-600 text-sm mt-2 text-center">
                    Please fix the errors above before placing your order.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  )
}

