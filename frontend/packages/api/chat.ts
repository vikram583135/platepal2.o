/**
 * Chat WebSocket client
 */
import { WebSocketClient, createWebSocket } from './websocket'

export function createChatWebSocket(roomId: number, token: string): WebSocketClient {
  const baseUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
  const url = `${baseUrl}/chat/${roomId}`
  return createWebSocket(url, token)
}

