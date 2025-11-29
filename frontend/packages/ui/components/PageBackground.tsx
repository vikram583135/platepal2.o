import { ReactNode } from 'react'
import { cn } from '../utils/cn'

interface PageBackgroundProps {
  children: ReactNode
  variant?: 'default' | 'light' | 'dark' | 'gradient' | 'pattern'
  overlay?: boolean
  overlayOpacity?: 'light' | 'medium' | 'dark'
  className?: string
}

const overlayClasses = {
  light: 'from-black/10 via-black/5 to-black/10',
  medium: 'from-black/20 via-black/10 to-black/20',
  dark: 'from-black/40 via-black/20 to-black/40',
}

const backgroundVariants = {
  default: 'bg-gradient-to-br from-red-50 via-white to-red-50/50',
  light: 'bg-gradient-to-br from-red-50/30 via-white to-red-50/20',
  dark: 'bg-gradient-to-br from-red-950/10 via-red-900/5 to-red-950/10',
  gradient: 'bg-gradient-to-br from-zomato-red/5 via-red-50/30 to-zomato-lightRed/5',
  pattern: 'page-background',
}

export function PageBackground({
  children,
  variant = 'default',
  overlay = true,
  overlayOpacity = 'medium',
  className,
}: PageBackgroundProps) {
  return (
    <div className={cn('page-background min-h-screen', backgroundVariants[variant], className)}>
      {overlay && (
        <div className={cn('page-background-overlay', overlayClasses[overlayOpacity])} />
      )}
      <div className="page-content">{children}</div>
    </div>
  )
}

