import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { createWebSocket, getWebSocketUrl } from '@/packages/api/websocket'
import { useAuthStore } from '../stores/authStore'

export function useCustomerSocket(customerId?: number | null) {
  const queryClient = useQueryClient()
  const { accessToken, user } = useAuthStore()

  useEffect(() => {
    const userId = customerId || user?.id
    if (!userId || !accessToken) {
      return
    }

    // Check if WebSocket is enabled
    const wsEnabled = (import.meta as any).env.VITE_WS_ENABLED !== 'false'
    if (!wsEnabled) {
      return // WebSocket is disabled, skip connection
    }

    let socket: ReturnType<typeof createWebSocket> | null = null
    
    try {
      socket = createWebSocket(getWebSocketUrl('customer', userId), accessToken)
    } catch (error) {
      // WebSocket URL construction failed (e.g., disabled)
      if (import.meta.env.DEV) {
        console.warn('WebSocket is disabled or misconfigured')
      }
      return
    }

    let isMounted = true

    // Attempt WebSocket connection - it's optional, so failures are handled gracefully
    socket.connect().catch((error) => {
      // Only log in development - WebSocket is optional functionality
      if (import.meta.env.DEV) {
        console.warn('WebSocket connection failed (ASGI server may not be running). Real-time updates disabled, but the app will work normally.')
      }
    })

    const invalidateOrders = () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['customer-orders', userId] })
      queryClient.invalidateQueries({ queryKey: ['order-detail'] })
    }

    // Order lifecycle events
    socket.on('order_created', (event: any) => {
      invalidateOrders()
      if (event.data?.payload) {
        console.log('Order created:', event.data.payload)
      }
    })
    socket.on('order_accepted', invalidateOrders)
    socket.on('order_rejected', (event: any) => {
      invalidateOrders()
      // Show notification about rejection and refund
      if (event.data?.payload) {
        console.log('Order rejected:', event.data.payload)
      }
    })
    socket.on('order_updated', invalidateOrders)
    socket.on('order_completed', invalidateOrders)
    
    // Delivery events
    socket.on('delivery_assigned', (event: any) => {
      invalidateOrders()
      if (event.data?.payload) {
        console.log('Delivery assigned:', event.data.payload)
      }
    })
    socket.on('delivery_status_changed', invalidateOrders)
    socket.on('rider_location', (event: any) => {
      // Update order tracking with real-time location
      if (event.data?.payload) {
        const { order_id, location, eta_minutes } = event.data.payload
        queryClient.setQueryData(['order-tracking', order_id], (old: any) => {
          if (!old) return old
          return {
            ...old,
            rider_location: location,
            eta_minutes,
            last_updated: new Date().toISOString(),
          }
        })
      }
    })
    
    // Menu and inventory events
    socket.on('menu_updated', () => {
      queryClient.invalidateQueries({ queryKey: ['menu'] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-detail'] })
    })
    socket.on('item_sold_out', () => {
      queryClient.invalidateQueries({ queryKey: ['menu'] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-detail'] })
    })
    
    // Payment events
    socket.on('payment_captured', (event: any) => {
      invalidateOrders()
      if (event.data?.payload) {
        console.log('Payment captured:', event.data.payload)
      }
    })
    socket.on('payment_failed', (event: any) => {
      invalidateOrders()
      // Show error notification
      if (event.data?.payload) {
        console.error('Payment failed:', event.data.payload)
      }
    })
    socket.on('refund_initiated', invalidateOrders)
    socket.on('refund_completed', (event: any) => {
      invalidateOrders()
      queryClient.invalidateQueries({ queryKey: ['wallet'] })
      if (event.data?.payload) {
        console.log('Refund completed:', event.data.payload)
      }
    })
    
    // Promotion events
    socket.on('promo_published', () => {
      queryClient.invalidateQueries({ queryKey: ['promotions'] })
      queryClient.invalidateQueries({ queryKey: ['offers'] })
    })
    
    // Support events
    socket.on('ticket_created', () => {
      queryClient.invalidateQueries({ queryKey: ['support-tickets'] })
    })
    socket.on('ticket_updated', () => {
      queryClient.invalidateQueries({ queryKey: ['support-tickets'] })
      queryClient.invalidateQueries({ queryKey: ['ticket-detail'] })
    })

    return () => {
      if (isMounted && socket) {
        socket.disconnect()
        isMounted = false
      }
    }
  }, [customerId, accessToken, user, queryClient])
}

