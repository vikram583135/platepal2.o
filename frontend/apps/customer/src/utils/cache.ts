/**
 * Cache utilities for offline support
 */

const CACHE_PREFIX = 'platepal_cache_'
const CACHE_VERSION = '1.0'
const CACHE_EXPIRY = 24 * 60 * 60 * 1000 // 24 hours

interface CacheEntry<T> {
  data: T
  timestamp: number
  version: string
}

export class CacheManager {
  private static getKey(key: string): string {
    return `${CACHE_PREFIX}${key}`
  }

  static set<T>(key: string, data: T): void {
    try {
      const entry: CacheEntry<T> = {
        data,
        timestamp: Date.now(),
        version: CACHE_VERSION,
      }
      localStorage.setItem(this.getKey(key), JSON.stringify(entry))
    } catch (error) {
      console.error('Failed to cache data:', error)
    }
  }

  static get<T>(key: string): T | null {
    try {
      const item = localStorage.getItem(this.getKey(key))
      if (!item) return null

      const entry: CacheEntry<T> = JSON.parse(item)

      // Check version
      if (entry.version !== CACHE_VERSION) {
        this.remove(key)
        return null
      }

      // Check expiry
      if (Date.now() - entry.timestamp > CACHE_EXPIRY) {
        this.remove(key)
        return null
      }

      return entry.data
    } catch (error) {
      console.error('Failed to retrieve cached data:', error)
      return null
    }
  }

  static remove(key: string): void {
    try {
      localStorage.removeItem(this.getKey(key))
    } catch (error) {
      console.error('Failed to remove cached data:', error)
    }
  }

  static clear(): void {
    try {
      const keys = Object.keys(localStorage)
      keys.forEach((key) => {
        if (key.startsWith(CACHE_PREFIX)) {
          localStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.error('Failed to clear cache:', error)
    }
  }

  static has(key: string): boolean {
    return this.get(key) !== null
  }
}

// Menu cache helpers
export const MenuCache = {
  set: (restaurantId: number, menu: any) => {
    CacheManager.set(`menu_${restaurantId}`, menu)
  },
  get: (restaurantId: number) => {
    return CacheManager.get(`menu_${restaurantId}`)
  },
  remove: (restaurantId: number) => {
    CacheManager.remove(`menu_${restaurantId}`)
  },
}

// Restaurant cache helpers
export const RestaurantCache = {
  set: (restaurantId: number, restaurant: any) => {
    CacheManager.set(`restaurant_${restaurantId}`, restaurant)
  },
  get: (restaurantId: number) => {
    return CacheManager.get(`restaurant_${restaurantId}`)
  },
  setList: (restaurants: any[]) => {
    CacheManager.set('restaurants_list', restaurants)
  },
  getList: () => {
    return CacheManager.get<any[]>('restaurants_list')
  },
}

