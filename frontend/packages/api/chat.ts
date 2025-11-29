/**
 * Chat WebSocket client
 */
import { WebSocketClient, createWebSocket } from './websocket'

export function createChatWebSocket(roomId: number, token: string): WebSocketClient {
  const WS_URL = (import.meta as any).env.VITE_WS_URL || 'ws://localhost:8000/ws'
  const url = `${WS_URL}/chat/${roomId}`
  return createWebSocket(url, token)
}
