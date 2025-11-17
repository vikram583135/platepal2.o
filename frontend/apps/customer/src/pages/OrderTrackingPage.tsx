import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet'
import { Card, CardContent, CardHeader, CardTitle } from '@/packages/ui/components/card'
import { Button } from '@/packages/ui/components/button'
import { Badge } from '@/packages/ui/components/badge'
import { Input } from '@/packages/ui/components/input'
import { Skeleton } from '@/packages/ui/components/skeleton'
import { Phone, MessageCircle, Clock, MapPin, CheckCircle, Truck, Utensils, Package } from 'lucide-react'
import apiClient from '@/packages/api/client'
import { formatCurrency, formatDate } from '@/packages/utils/format'
import ChatWidget from '../components/ChatWidget'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix for default marker icon
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

function MapUpdater({ courierLocation, restaurantLocation, deliveryLocation }: any) {
  const map = useMap()
  
  useEffect(() => {
    if (courierLocation || restaurantLocation || deliveryLocation) {
      const bounds = L.latLngBounds([])
      if (restaurantLocation) bounds.extend([restaurantLocation.lat, restaurantLocation.lng])
      if (deliveryLocation) bounds.extend([deliveryLocation.lat, deliveryLocation.lng])
      if (courierLocation) bounds.extend([courierLocation.lat, courierLocation.lng])
      if (!bounds.isValid()) return
      map.fitBounds(bounds, { padding: [50, 50] })
    }
  }, [courierLocation, restaurantLocation, deliveryLocation, map])
  
  return null
}

export default function OrderTrackingPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [deliveryOtp, setDeliveryOtp] = useState('')
  const [showOtpInput, setShowOtpInput] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const [chatRoomId, setChatRoomId] = useState<number | null>(null)
  const [chatType, setChatType] = useState<'ORDER' | 'RESTAURANT' | 'COURIER' | 'SUPPORT'>('ORDER')

  const { data: order, isLoading, error: orderError } = useQuery({
    queryKey: ['order', id],
    queryFn: async () => {
      const response = await apiClient.get(`/orders/orders/${id}/`)
      return response.data
    },
    refetchInterval: 5000, // Poll every 5 seconds
    retry: 1,
  })

  const { data: courier } = useQuery({
    queryKey: ['courier', id],
    queryFn: async () => {
      const response = await apiClient.get(`/orders/orders/${id}/courier/`)
      return response.data
    },
    enabled: !!order && order.courier !== null,
    refetchInterval: 10000,
  })

  const { data: eta } = useQuery({
    queryKey: ['eta', id],
    queryFn: async () => {
      const response = await apiClient.get(`/orders/orders/${id}/eta/`)
      return response.data
    },
    enabled: !!order,
    refetchInterval: 30000,
  })

  const { data: timeline } = useQuery({
    queryKey: ['timeline', id],
    queryFn: async () => {
      const response = await apiClient.get(`/orders/orders/${id}/timeline/`)
      return response.data
    },
    enabled: !!order,
  })

  const generateOtpMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post(`/orders/orders/${id}/generate_delivery_otp/`)
      return response.data
    },
    onSuccess: () => {
      setShowOtpInput(true)
      alert('OTP sent to your registered phone number')
    },
  })

  const verifyOtpMutation = useMutation({
    mutationFn: async (otp: string) => {
      const response = await apiClient.post(`/orders/orders/${id}/verify_delivery_otp/`, { otp })
      return response.data
    },
    onSuccess: (data) => {
      if (data.verified) {
        alert('OTP verified successfully!')
        setShowOtpInput(false)
        setDeliveryOtp('')
      }
    },
  })

  // Get or create chat room
  const { data: chatRoom } = useQuery({
    queryKey: ['chat-room', id, chatType],
    queryFn: async () => {
      const response = await apiClient.post('/chat/rooms/create_or_get/', {
        order_id: id,
        room_type: chatType,
      })
      return response.data
    },
    enabled: !!id && showChat,
  })

  useEffect(() => {
    if (chatRoom?.id) {
      setChatRoomId(chatRoom.id)
    }
  }, [chatRoom])

  const handleOpenChat = (type: 'ORDER' | 'RESTAURANT' | 'COURIER' | 'SUPPORT') => {
    setChatType(type)
    setShowChat(true)
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (orderError) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-4">Error Loading Order</h2>
              <p className="text-gray-600 mb-4">
                {orderError instanceof Error 
                  ? orderError.message 
                  : 'Failed to load order details. Please try again.'}
              </p>
              <Button onClick={() => navigate('/orders')}>
                Back to Orders
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-4">Order Not Found</h2>
              <p className="text-gray-600 mb-4">
                The order you're looking for doesn't exist or you don't have permission to view it.
              </p>
              <Button onClick={() => navigate('/orders')}>
                Back to Orders
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Mock locations (in production, get from real-time tracking)
  const restaurantLocation = order.restaurant ? {
    lat: order.restaurant.latitude ? parseFloat(String(order.restaurant.latitude)) : 19.0760,
    lng: order.restaurant.longitude ? parseFloat(String(order.restaurant.longitude)) : 72.8777,
  } : null

  const deliveryLocation = order.delivery_address ? {
    lat: order.delivery_address.latitude ? parseFloat(String(order.delivery_address.latitude)) : 19.0760,
    lng: order.delivery_address.longitude ? parseFloat(String(order.delivery_address.longitude)) : 72.8777,
  } : null

  const courierLocation = courier ? {
    lat: (restaurantLocation?.lat || 0) + 0.01, // Mock courier location
    lng: (restaurantLocation?.lng || 0) + 0.01,
  } : null

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'DELIVERED':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'OUT_FOR_DELIVERY':
      case 'PICKED_UP':
        return <Truck className="w-5 h-5 text-blue-600" />
      case 'PREPARING':
      case 'READY':
        return <Utensils className="w-5 h-5 text-yellow-600" />
      default:
        return <Package className="w-5 h-5 text-gray-600" />
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Track Order #{order.order_number || id}</h1>
        <Badge className="text-lg px-4 py-1">
          {order.status ? order.status.replace(/_/g, ' ') : 'Unknown'}
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Live Map */}
          <Card>
            <CardHeader>
              <CardTitle>Live Tracking</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-96 w-full rounded-lg overflow-hidden">
                <MapContainer
                  center={[19.0760, 72.8777]}
                  zoom={13}
                  style={{ height: '100%', width: '100%' }}
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  <MapUpdater
                    courierLocation={courierLocation}
                    restaurantLocation={restaurantLocation}
                    deliveryLocation={deliveryLocation}
                  />
                  {restaurantLocation && (
                    <Marker position={[restaurantLocation.lat, restaurantLocation.lng]}>
                      <L.Popup>Restaurant</L.Popup>
                    </Marker>
                  )}
                  {deliveryLocation && (
                    <Marker position={[deliveryLocation.lat, deliveryLocation.lng]}>
                      <L.Popup>Delivery Address</L.Popup>
                    </Marker>
                  )}
                  {courierLocation && (
                    <Marker position={[courierLocation.lat, courierLocation.lng]}>
                      <L.Popup>Courier</L.Popup>
                    </Marker>
                  )}
                </MapContainer>
              </div>
            </CardContent>
          </Card>

          {/* Order Timeline */}
          {timeline && (
            <Card>
              <CardHeader>
                <CardTitle>Order Timeline</CardTitle>
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
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* ETA Card */}
          {eta && (
            <Card>
              <CardHeader>
                <CardTitle>Estimated Delivery</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-4xl font-bold text-primary-600 mb-2">
                    {eta.eta_minutes}
                  </div>
                  <div className="text-gray-600">minutes</div>
                  {eta.estimated_time && (
                    <div className="text-sm text-gray-500 mt-2">
                      By {new Date(eta.estimated_time).toLocaleTimeString()}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Courier Details */}
          {courier && (
            <Card>
              <CardHeader>
                <CardTitle>Courier Details</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="font-semibold">{courier.name}</div>
                    <div className="text-sm text-gray-600">Phone: {courier.phone}</div>
                    {courier.rating && (
                      <div className="text-sm text-gray-600">Rating: {courier.rating}/5</div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => window.open(`tel:${courier.phone}`)}
                    >
                      <Phone className="w-4 h-4 mr-2" />
                      Call
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => handleOpenChat('COURIER')}
                    >
                      <MessageCircle className="w-4 h-4 mr-2" />
                      Chat
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Safety Features */}
          {order.contactless_delivery && (
            <Card>
              <CardHeader>
                <CardTitle>Contactless Delivery</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-gray-600 mb-4">
                  Your order will be left at the door. No contact required.
                </div>
                {order.delivery_otp && !order.delivery_otp_verified && (
                  <div className="space-y-2">
                    {!showOtpInput ? (
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={() => generateOtpMutation.mutate()}
                      >
                        Generate Delivery OTP
                      </Button>
                    ) : (
                      <>
                        <Input
                          placeholder="Enter OTP"
                          value={deliveryOtp}
                          onChange={(e) => setDeliveryOtp(e.target.value)}
                          maxLength={6}
                        />
                        <Button
                          className="w-full"
                          onClick={() => verifyOtpMutation.mutate(deliveryOtp)}
                          disabled={deliveryOtp.length !== 6}
                        >
                          Verify OTP
                        </Button>
                      </>
                    )}
                  </div>
                )}
                {order.delivery_otp_verified && (
                  <div className="text-sm text-green-600">OTP Verified ✓</div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Order Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Order Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span>{formatCurrency(order.subtotal, 'INR')}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tax</span>
                  <span>{formatCurrency(order.tax_amount, 'INR')}</span>
                </div>
                <div className="flex justify-between">
                  <span>Delivery</span>
                  <span>{formatCurrency(order.delivery_fee, 'INR')}</span>
                </div>
                {order.tip_amount > 0 && (
                  <div className="flex justify-between">
                    <span>Tip</span>
                    <span>{formatCurrency(order.tip_amount, 'INR')}</span>
                  </div>
                )}
                <div className="border-t pt-2 flex justify-between font-semibold">
                  <span>Total</span>
                  <span>{formatCurrency(order.total_amount, 'INR')}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Restaurant Chat */}
          {order.restaurant && (
            <Card>
              <CardHeader>
                <CardTitle>Restaurant</CardTitle>
              </CardHeader>
              <CardContent>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => handleOpenChat('RESTAURANT')}
                >
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Chat with Restaurant
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Chat Widget */}
      {showChat && chatRoomId && (
        <ChatWidget
          roomId={chatRoomId}
          orderId={order.id}
          onClose={() => setShowChat(false)}
        />
      )}
    </div>
  )
}

