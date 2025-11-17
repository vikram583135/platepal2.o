export interface RestaurantAlert {
  id: number
  alert_type: string
  severity: string
  title: string
  message: string
  created_at: string
  is_read: boolean
}

export interface RestaurantSettings {
  id: number
  is_online: boolean
  default_prep_time_minutes: number
  sla_threshold_minutes?: number
  auto_accept_orders?: boolean
}

export interface MenuItem {
  id: number
  name: string
  description: string
  price: string
  is_available: boolean
  preparation_time_minutes: number
  is_spicy: boolean
  is_vegetarian: boolean
  inventory_count: number | null
  low_stock_threshold: number
  is_featured: boolean
}

export interface MenuCategory {
  id: number
  name: string
  description: string
  display_order: number
  items: MenuItem[]
}

export interface Menu {
  id: number
  name: string
  description: string
  is_active: boolean
  categories: MenuCategory[]
}

export interface ManagerProfile {
  id: number
  first_name: string
  last_name: string
  email: string
  phone: string
  role: string
  is_primary: boolean
}

export interface RestaurantDocument {
  id: number
  document_type: string
  status: string
  rejection_reason: string
  needs_reupload: boolean
  submitted_at: string
}

export interface RestaurantBranch {
  id: number
  name: string
  city: string
  branch_type: string
  is_primary: boolean
  service_radius_km: string
}

export interface RestaurantDetail {
  id: number
  name: string
  status: string
  onboarding_status: string
  description?: string
  address?: string
  city?: string
  restaurant_type: string
  cuisine_types: string[]
  delivery_radius_km: string
  estimated_preparation_time: number
  support_phone?: string
  support_email?: string
  settings?: RestaurantSettings | null
  latest_alerts?: RestaurantAlert[]
  menus?: Menu[]
}

export interface RestaurantOverview {
  restaurant: RestaurantDetail
  branches: RestaurantBranch[]
  managers: ManagerProfile[]
  documents: RestaurantDocument[]
  progress: {
    steps: Record<string, boolean>
    percentage: number
  }
}

