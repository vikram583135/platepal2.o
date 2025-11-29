import { ReactNode } from 'react'
import { cn } from '../utils/cn'

interface DeliveryPageBackgroundProps {
  children: ReactNode
  variant?: 'default' | 'light' | 'dark' | 'gradient' | 'pattern'
  overlay?: boolean
  overlayOpacity?: 'light' | 'medium' | 'dark'
  className?: string
}

const overlayClasses = {
  light: 'from-black/10 via-black/5 to-black/10',
  medium: 'from-black/15 via-black/5 to-black/15',
  dark: 'from-black/30 via-black/15 to-black/30',
}

const backgroundVariants = {
  default: 'bg-gradient-to-br from-emerald-50 via-white to-emerald-50/50',
  light: 'bg-gradient-to-br from-emerald-50/30 via-white to-emerald-50/20',
  dark: 'bg-gradient-to-br from-emerald-950/10 via-emerald-900/5 to-emerald-950/10',
  gradient: 'bg-gradient-to-br from-delivery-primary/5 via-emerald-50/30 to-delivery-secondary/5',
  pattern: 'delivery-page-background',
}

export function DeliveryPageBackground({
  children,
  variant = 'default',
  overlay = true,
  overlayOpacity = 'medium',
  className,
}: DeliveryPageBackgroundProps) {
  return (
    <div className={cn('delivery-page-background min-h-screen', backgroundVariants[variant], className)}>
      {overlay && (
        <div className={cn('delivery-page-background-overlay', overlayClasses[overlayOpacity])} />
      )}
      <div className="delivery-page-content">{children}</div>
    </div>
  )
}

