import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { createWebSocket, getWebSocketUrl } from '@/packages/api/websocket'
import { useAuthStore } from '../stores/authStore'

export function useDeliverySocket(riderId?: number | null) {
  const queryClient = useQueryClient()
  const { accessToken, user } = useAuthStore()

  useEffect(() => {
    const userId = riderId || user?.id
    if (!userId || !accessToken) {
      return
    }

    const socket = createWebSocket(getWebSocketUrl('delivery', userId), accessToken)
    let isMounted = true

    socket.connect().catch((error) => {
      console.error('WebSocket connection failed', error)
    })

    const invalidateDeliveries = () => {
      queryClient.invalidateQueries({ queryKey: ['deliveries'] })
      queryClient.invalidateQueries({ queryKey: ['rider-deliveries', userId] })
      queryClient.invalidateQueries({ queryKey: ['active-deliveries'] })
    }

    // Job offer events
    socket.on('job_offer', (event: any) => {
      queryClient.invalidateQueries({ queryKey: ['job-offers', userId] })
      if (event.data?.payload) {
        const { offer_id, delivery_id, estimated_earnings, expires_at } = event.data.payload
        console.log('New job offer received:', {
          offer_id,
          delivery_id,
          estimated_earnings,
          expires_at,
        })
        // Show notification for new offer
      }
    })
    socket.on('offer_accepted', (event: any) => {
      invalidateDeliveries()
      if (event.data?.payload) {
        console.log('Offer accepted:', event.data.payload)
      }
    })
    socket.on('offer_declined', (event: any) => {
      queryClient.invalidateQueries({ queryKey: ['job-offers', userId] })
    })
    
    // Delivery assignment events
    socket.on('delivery_assigned', (event: any) => {
      invalidateDeliveries()
      if (event.data?.payload) {
        console.log('Delivery assigned:', event.data.payload)
      }
    })
    socket.on('delivery_status_changed', (event: any) => {
      invalidateDeliveries()
      if (event.data?.payload) {
        const { status, previous_status } = event.data.payload
        console.log('Delivery status changed:', { status, previous_status })
      }
    })
    
    // Escalation events
    socket.on('delivery_escalation', (event: any) => {
      invalidateDeliveries()
      if (event.data?.payload) {
        console.log('Delivery escalation:', event.data.payload)
      }
    })
    socket.on('delivery_no_rider_available', (event: any) => {
      // Inform rider about no rider available (could be used for incentives)
      if (event.data?.payload) {
        console.log('No rider available:', event.data.payload)
      }
    })
    
    // Payment and earnings events
    socket.on('payment_captured', invalidateDeliveries)
    socket.on('settlement_completed', () => {
      queryClient.invalidateQueries({ queryKey: ['earnings', userId] })
      queryClient.invalidateQueries({ queryKey: ['rider-wallet', userId] })
    })
    socket.on('payout_completed', () => {
      queryClient.invalidateQueries({ queryKey: ['earnings', userId] })
      queryClient.invalidateQueries({ queryKey: ['rider-wallet', userId] })
      queryClient.invalidateQueries({ queryKey: ['payouts', userId] })
    })
    socket.on('payout_failed', () => {
      queryClient.invalidateQueries({ queryKey: ['payouts', userId] })
      // Show error notification
    })
    
    // System alerts
    socket.on('system_alert', (event: any) => {
      if (event.data?.payload) {
        console.log('System alert:', event.data.payload)
      }
    })

    return () => {
      if (isMounted) {
        socket.disconnect()
        isMounted = false
      }
    }
  }, [riderId, accessToken, user, queryClient])
}

