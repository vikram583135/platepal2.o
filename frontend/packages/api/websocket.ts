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
      
      try {
        this.ws = new WebSocket(wsUrl)
      } catch (error) {
        this.isConnecting = false
        // Silently fail - WebSocket is optional
        if (import.meta.env.DEV) {
          console.warn('WebSocket connection failed (ASGI server may not be running):', error)
        }
        resolve() // Resolve instead of reject to prevent unhandled promise rejection
        return
      }

      // Set connection timeout
      const connectionTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
          this.isConnecting = false
          if (this.ws) {
            this.ws.close()
            this.ws = null
          }
          // Silently fail - WebSocket is optional
          if (import.meta.env.DEV) {
            console.warn('WebSocket connection timeout (ASGI server may not be running)')
          }
          resolve() // Resolve instead of reject
        }
      }, 5000) // 5 second timeout

      this.ws.onopen = () => {
        clearTimeout(connectionTimeout)
        this.isConnecting = false
        this.reconnectAttempts = 0
        this.reconnectDelay = 1000
        if (import.meta.env.DEV) {
          console.log('WebSocket connected successfully')
        }
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
          if (import.meta.env.DEV) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }
      }

      this.ws.onerror = (error) => {
        clearTimeout(connectionTimeout)
        this.isConnecting = false
        // Don't log errors in production - WebSocket is optional
        if (import.meta.env.DEV) {
          console.warn('WebSocket error (ASGI server may not be running). This is optional and the app will work without it.')
        }
        // Resolve instead of reject to prevent unhandled promise rejection
        // WebSocket is optional functionality
        resolve()
      }

      this.ws.onclose = (event) => {
        clearTimeout(connectionTimeout)
        this.isConnecting = false
        
        // Only attempt reconnect if it wasn't a normal closure and we haven't exceeded max attempts
        if (this.shouldReconnect && 
            this.reconnectAttempts < this.maxReconnectAttempts && 
            event.code !== 1000) { // 1000 = normal closure
          // Reconnect with last event ID to replay missed events
          this.scheduleReconnect()
        } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          // Max retries reached - silently stop trying
          if (import.meta.env.DEV) {
            console.warn('WebSocket max reconnection attempts reached. Real-time updates disabled.')
          }
        }
      }
    })
  }

  private scheduleReconnect() {
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts), 30000)
    this.reconnectAttempts++

    // Only reconnect if we haven't exceeded max attempts
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      if (import.meta.env.DEV) {
        console.warn('WebSocket max reconnection attempts reached. Real-time updates disabled.')
      }
      return
    }

    setTimeout(() => {
      if (this.shouldReconnect) {
        // Reconnect with last event ID to replay missed events
        this.connect(this.lastEventId || undefined).catch(() => {
          // Silently handle reconnection failures - WebSocket is optional
        })
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
  // Check if WebSocket is disabled via environment variable
  const wsEnabled = (import.meta as any).env.VITE_WS_ENABLED !== 'false'
  if (!wsEnabled) {
    throw new Error('WebSocket is disabled')
  }
  
  const baseUrl = (import.meta as any).env.VITE_WS_URL || 'ws://localhost:8000/ws'

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

