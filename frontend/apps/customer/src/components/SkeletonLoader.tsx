import { Card, CardContent, CardHeader } from '@/packages/ui/components/card'

interface SkeletonLoaderProps {
  variant?: 'card' | 'list' | 'text' | 'image' | 'button'
  count?: number
  className?: string
}

export default function SkeletonLoader({ variant = 'card', count = 1, className = '' }: SkeletonLoaderProps) {
  const renderSkeleton = () => {
    switch (variant) {
      case 'card':
        return (
          <Card className={className}>
            <CardHeader>
              <div className="h-6 bg-gray-200 rounded w-3/4 animate-pulse"></div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded w-full animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded w-5/6 animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded w-4/6 animate-pulse"></div>
              </div>
            </CardContent>
          </Card>
        )
      case 'list':
        return (
          <div className={`space-y-3 ${className}`}>
            {Array.from({ length: count }).map((_, i) => (
              <div key={i} className="flex items-center space-x-4 p-4 border rounded-lg">
                <div className="h-16 w-16 bg-gray-200 rounded animate-pulse"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-3/4 animate-pulse"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse"></div>
                </div>
              </div>
            ))}
          </div>
        )
      case 'text':
        return (
          <div className={`space-y-2 ${className}`}>
            {Array.from({ length: count }).map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded animate-pulse" style={{ width: `${100 - i * 10}%` }}></div>
            ))}
          </div>
        )
      case 'image':
        return (
          <div className={`${className} bg-gray-200 rounded animate-pulse`} style={{ aspectRatio: '16/9' }}></div>
        )
      case 'button':
        return (
          <div className={`h-10 bg-gray-200 rounded w-24 animate-pulse ${className}`}></div>
        )
      default:
        return <div className={`h-4 bg-gray-200 rounded animate-pulse ${className}`}></div>
    }
  }

  if (variant === 'list' || variant === 'text') {
    return renderSkeleton()
  }

  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i}>{renderSkeleton()}</div>
      ))}
    </>
  )
}

