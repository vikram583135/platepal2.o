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

    socket.on('order_created', invalidateOrders)
    socket.on('order_updated', invalidateOrders)
    socket.on('restaurant_alert', () => {
      queryClient.invalidateQueries({ queryKey: ['restaurant-dashboard', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-alerts', restaurantId] })
    })
    socket.on('inventory_low', () => {
      queryClient.invalidateQueries({ queryKey: ['inventory', restaurantId] })
      queryClient.invalidateQueries({ queryKey: ['restaurant-dashboard', restaurantId] })
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

    return () => {
      if (isMounted) {
        socket.disconnect()
        isMounted = false
      }
    }
  }, [restaurantId, accessToken, queryClient])
}
