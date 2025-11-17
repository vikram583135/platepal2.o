import { useEffect, useRef, useState } from 'react'
import { RefreshCw } from 'lucide-react'

interface PullToRefreshProps {
  onRefresh: () => Promise<void> | void
  children: React.ReactNode
  threshold?: number
  disabled?: boolean
}

export default function PullToRefresh({ onRefresh, children, threshold = 80, disabled = false }: PullToRefreshProps) {
  const [isPulling, setIsPulling] = useState(false)
  const [pullDistance, setPullDistance] = useState(0)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const startY = useRef<number>(0)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (disabled) return

    const container = containerRef.current
    if (!container) return

    let touchStartY = 0
    let isDragging = false

    const handleTouchStart = (e: TouchEvent) => {
      if (container.scrollTop > 0) return
      touchStartY = e.touches[0].clientY
      startY.current = touchStartY
      isDragging = true
    }

    const handleTouchMove = (e: TouchEvent) => {
      if (!isDragging || container.scrollTop > 0) return

      const currentY = e.touches[0].clientY
      const distance = currentY - touchStartY

      if (distance > 0) {
        e.preventDefault()
        setIsPulling(true)
        setPullDistance(Math.min(distance, threshold * 1.5))
      }
    }

    const handleTouchEnd = async () => {
      if (!isDragging) return

      isDragging = false

      if (pullDistance >= threshold && !isRefreshing) {
        setIsRefreshing(true)
        try {
          await onRefresh()
        } finally {
          setIsRefreshing(false)
          setIsPulling(false)
          setPullDistance(0)
        }
      } else {
        setIsPulling(false)
        setPullDistance(0)
      }
    }

    container.addEventListener('touchstart', handleTouchStart, { passive: false })
    container.addEventListener('touchmove', handleTouchMove, { passive: false })
    container.addEventListener('touchend', handleTouchEnd)

    return () => {
      container.removeEventListener('touchstart', handleTouchStart)
      container.removeEventListener('touchmove', handleTouchMove)
      container.removeEventListener('touchend', handleTouchEnd)
    }
  }, [onRefresh, threshold, disabled, pullDistance, isRefreshing])

  const pullProgress = Math.min(pullDistance / threshold, 1)
  const rotation = pullProgress * 360

  return (
    <div ref={containerRef} className="relative overflow-auto">
      {/* Pull indicator */}
      {isPulling && (
        <div
          className="absolute top-0 left-0 right-0 flex items-center justify-center z-50 transition-transform duration-200"
          style={{
            transform: `translateY(${Math.min(pullDistance, threshold)}px)`,
            height: `${threshold}px`,
          }}
        >
          <div className="flex flex-col items-center gap-2">
            <RefreshCw
              className={`w-6 h-6 text-primary-600 transition-transform duration-200 ${
                isRefreshing ? 'animate-spin' : ''
              }`}
              style={{ transform: `rotate(${rotation}deg)` }}
            />
            <span className="text-sm text-gray-600">
              {pullDistance >= threshold ? 'Release to refresh' : 'Pull to refresh'}
            </span>
          </div>
        </div>
      )}

      {/* Content */}
      <div
        style={{
          transform: isPulling ? `translateY(${Math.min(pullDistance, threshold)}px)` : 'translateY(0)',
          transition: isPulling ? 'none' : 'transform 0.3s ease-out',
        }}
      >
        {children}
      </div>
    </div>
  )
}

