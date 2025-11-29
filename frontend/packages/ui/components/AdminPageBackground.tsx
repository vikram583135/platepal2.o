import { ReactNode } from 'react'
import { cn } from '../utils/cn'

interface AdminPageBackgroundProps {
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
  default: 'bg-gradient-to-br from-indigo-50 via-white to-indigo-50/50',
  light: 'bg-gradient-to-br from-indigo-50/30 via-white to-indigo-50/20',
  dark: 'bg-gradient-to-br from-indigo-950/10 via-indigo-900/5 to-indigo-950/10',
  gradient: 'bg-gradient-to-br from-admin-primary/5 via-indigo-50/30 to-admin-secondary/5',
  pattern: 'admin-page-background',
}

export function AdminPageBackground({
  children,
  variant = 'default',
  overlay = true,
  overlayOpacity = 'medium',
  className,
}: AdminPageBackgroundProps) {
  return (
    <div className={cn('admin-page-background min-h-screen', backgroundVariants[variant], className)}>
      {overlay && (
        <div className={cn('admin-page-background-overlay', overlayClasses[overlayOpacity])} />
      )}
      <div className="admin-page-content">{children}</div>
    </div>
  )
}

