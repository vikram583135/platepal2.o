/**
 * Shared TypeScript types
 */

export type UserRole = 'CUSTOMER' | 'RESTAURANT' | 'DELIVERY' | 'ADMIN'

export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  phone?: string
  role: UserRole
  is_email_verified: boolean
  is_phone_verified: boolean
  date_joined: string
}

export interface Address {
  id: number
  label: string
  street: string
  city: string
  state: string
  postal_code: string
  country: string
  latitude?: number
  longitude?: number
  is_default: boolean
  created_at: string
}

export interface Restaurant {
  id: number
  name: string
  description?: string
  cuisine_type: string
  rating: number
  total_ratings: number
  delivery_time_minutes: number
  delivery_fee: number
  minimum_order_amount: number
  latitude: number
  longitude: number
  city: string
  logo?: string
  cover_image?: string
  logo_image_url?: string
  hero_image_url?: string
}

export interface MenuItem {
  id: number
  name: string
  description?: string
  price: number
  image?: string
  is_available: boolean
  inventory_count?: number
  preparation_time_minutes: number
  is_vegetarian: boolean
  is_vegan: boolean
  is_spicy: boolean
  calories?: number
  rating: number
  total_ratings: number
  modifiers?: ItemModifier[]
}

export interface ItemModifier {
  id: number
  name: string
  type: 'ADDON' | 'VARIANT' | 'CUSTOMIZATION'
  price: number
  is_required: boolean
  is_available: boolean
}

export interface Order {
  id: number
  order_number: string
  customer: User
  restaurant: Restaurant
  status: OrderStatus
  order_type: 'DELIVERY' | 'PICKUP'
  subtotal: number
  tax_amount: number
  delivery_fee: number
  tip_amount: number
  discount_amount: number
  total_amount: number
  items: OrderItem[]
  created_at: string
  estimated_delivery_time?: string
  delivered_at?: string
}

export type OrderStatus =
  | 'PENDING'
  | 'ACCEPTED'
  | 'PREPARING'
  | 'READY'
  | 'ASSIGNED'
  | 'PICKED_UP'
  | 'OUT_FOR_DELIVERY'
  | 'DELIVERED'
  | 'CANCELLED'
  | 'REFUNDED'

export interface OrderItem {
  id: number
  menu_item?: MenuItem
  name: string
  quantity: number
  unit_price: number
  total_price: number
  selected_modifiers: Array<{
    modifier_id: number
    name: string
    price: number
  }>
}

export interface Delivery {
  id: number
  order: Order
  rider?: User
  status: DeliveryStatus
  estimated_delivery_time?: string
  actual_delivery_time?: string
  total_earnings: number
}

export type DeliveryStatus =
  | 'PENDING'
  | 'ASSIGNED'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'PICKED_UP'
  | 'IN_TRANSIT'
  | 'DELIVERED'
  | 'FAILED'
  | 'CANCELLED'

export interface WebSocketEvent {
  type: string
  data: any
  event_id: string
  timestamp: string
  version: string
}

