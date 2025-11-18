/**
 * WebSocket client with reconnection logic
 */
import { WebSocketEvent } from '../types'

type EventHandler = (event: WebSocketEvent) => void

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private token: string
  private handlers: Map<string, EventHandler[]> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 10
  private reconnectDelay = 1000
  private isConnecting = false
  private shouldReconnect = true
  private lastEventId: string | null = null

  constructor(url: string, token: string) {
    this.url = url
    this.token = token
  }

  connect(sinceEventId?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
        resolve()
        return
      }

      this.isConnecting = true
      // Use sinceEventId if provided, otherwise use stored lastEventId
      const eventIdParam = sinceEventId || this.lastEventId || undefined
      const params = new URLSearchParams({ token: this.token })
      if (eventIdParam) {
        params.append('since_event_id', eventIdParam)
      }
      const wsUrl = `${this.url}?${params.toString()}`
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        this.isConnecting = false
        this.reconnectAttempts = 0
        this.reconnectDelay = 1000
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const data: WebSocketEvent = JSON.parse(event.data)
          // Store last event ID for reconnection replay
          if (data.event_id) {
            this.lastEventId = data.event_id
          }
          this.handleEvent(data)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        this.isConnecting = false
        reject(error)
      }

      this.ws.onclose = () => {
        this.isConnecting = false
        if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
          // Reconnect with last event ID to replay missed events
          this.scheduleReconnect()
        }
      }
    })
  }

  private scheduleReconnect() {
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts), 30000)
    this.reconnectAttempts++

    setTimeout(() => {
      if (this.shouldReconnect) {
        // Reconnect with last event ID to replay missed events
        this.connect(this.lastEventId || undefined).catch(console.error)
      }
    }, delay)
  }

  getLastEventId(): string | null {
    return this.lastEventId
  }

  private handleEvent(event: WebSocketEvent) {
    const handlers = this.handlers.get(event.type) || []
    handlers.forEach((handler) => handler(event))
  }

  on(eventType: string, handler: EventHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, [])
    }
    this.handlers.get(eventType)!.push(handler)
  }

  off(eventType: string, handler: EventHandler) {
    const handlers = this.handlers.get(eventType)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  disconnect() {
    this.shouldReconnect = false
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('WebSocket is not connected')
    }
  }
}

/**
 * Create WebSocket connection
 */
export function createWebSocket(url: string, token: string): WebSocketClient {
  return new WebSocketClient(url, token)
}

/**
 * Get WebSocket URL for different channels
 */
export function getWebSocketUrl(
  channel: 'customer' | 'restaurant' | 'delivery' | 'admin' | 'chat',
  id?: number
): string {
  const baseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
  
  switch (channel) {
    case 'customer':
      return `${baseUrl}/customer/${id}`
    case 'restaurant':
      return `${baseUrl}/orders/${id}` // Restaurant channel uses restaurant_id
    case 'delivery':
      return `${baseUrl}/delivery/${id}` // Delivery channel uses rider_id
    case 'admin':
      return `${baseUrl}/admin`
    case 'chat':
      return `${baseUrl}/chat/${id}`
    default:
      throw new Error(`Unknown channel: ${channel}`)
  }
}

