import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { createWebSocket, getWebSocketUrl } from '@/packages/api/websocket'
import { useAuthStore } from '../stores/authStore'

export function useRestaurantSocket(restaurantId?: number | null) {
  const queryClient = useQueryClient()
  const { accessToken } = useAuthStore()

  useEffect(() => {
    if (!restaurantId || !accessToken) {
      return
    }

    const socket = createWebSocket(getWebSocketUrl('restaurant', restaurantId), accessToken)
    let isMounted = true

    socket.connect().catch((error) => {
      console.error('WebSocket connection failed', error)
    })

    const invalidateOrders = () => {
      queryClient.invalidateQueries({ queryKey: ['orders-queue', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['realtime-feed', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-orders', restaurantId] })
    }

    // Order lifecycle events
    socket.on('order_created', (event: any) => {
      invalidateOrders()
      // Show notification for new order
      if (event.data?.payload) {
        console.log('New order received:', event.data.payload)
      }
    })
    socket.on('order_accepted', invalidateOrders)
    socket.on('order_rejected', invalidateOrders)
    socket.on('order_updated', invalidateOrders)
    socket.on('order_completed', invalidateOrders)
    
    // Menu and inventory events
    socket.on('menu_updated', () => {
      queryClient.invalidateQueries({ queryKey: ['menu', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-menu', restaurantId] })
    })
    socket.on('inventory_low', () => {
      queryClient.invalidateQueries({ queryKey: ['inventory', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-dashboard', restaurantId] })
    })
    socket.on('item_sold_out', () => {
      queryClient.invalidateQueries({ queryKey: ['inventory', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['menu', restaurantId] })
    })
    socket.on('inventory_restocked', () => {
      queryClient.invalidateQueries({ queryKey: ['inventory', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['menu', restaurantId] })
    })
    
    // Delivery events
    socket.on('delivery_assigned', invalidateOrders)
    socket.on('delivery_status_changed', invalidateOrders)
    socket.on('rider_location', () => {
      queryClient.invalidateQueries({ queryKey: ['deliveries', restaurantId] })
    })
    
    // Restaurant alerts and status
    socket.on('restaurant_alert', () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-dashboard', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-alerts', restaurantId] })
    })
    socket.on('restaurant_high_rejection_rate', () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-dashboard', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-alerts', restaurantId] })
    })
    socket.on('restaurant_status', (payload: any) => {
      // Update all related queries when status changes
      queryClient.invalidateQueries({ queryKey: ['dashboard', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-dashboard', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['my-restaurants'] })
      // Update optimistically if payload has is_online
      if (payload?.is_online !== undefined) {
        queryClient.setQueryData(['dashboard', restaurantId], (old: any) => {
          if (!old) return old
          return {
            ...old,
            restaurant: {
              ...old.restaurant,
              is_online: payload.is_online,
            },
          }
        })
      }
    })

    // Payment events
    socket.on('payment_captured', invalidateOrders)
    socket.on('payment_failed', () => {
      queryClient.invalidateQueries({ queryKey: ['orders-queue', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-alerts', restaurantId] })
    })
    socket.on('refund_initiated', invalidateOrders)
    socket.on('refund_completed', invalidateOrders)

    return () => {
      if (isMounted) {
        socket.disconnect()
        isMounted = false
      }
    }
  }, [restaurantId, accessToken, queryClient])
}
