import { format } from 'date-fns'
import { cn } from '../../utils/cn'

export interface AuditEvent {
  id: string
  action: string
  user?: string
  timestamp: Date | string
  beforeState?: Record<string, any>
  afterState?: Record<string, any>
  reason?: string
  metadata?: Record<string, any>
}

interface AuditTimelineProps {
  events: AuditEvent[]
  className?: string
}

export function AuditTimeline({ events, className }: AuditTimelineProps) {
  return (
    <div className={cn("space-y-4", className)}>
      {events.map((event, index) => (
        <div key={event.id} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div className="w-2 h-2 rounded-full bg-blue-600" />
            {index < events.length - 1 && (
              <div className="w-0.5 h-full bg-gray-200 mt-2" />
            )}
          </div>
          <div className="flex-1 pb-4">
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium text-gray-900">{event.action}</span>
              {event.user && (
                <span className="text-sm text-gray-500">by {event.user}</span>
              )}
            </div>
            <div className="text-sm text-gray-500 mb-2">
              {format(new Date(event.timestamp), 'PPpp')}
            </div>
            {event.reason && (
              <div className="text-sm text-gray-600 mb-2">
                <strong>Reason:</strong> {event.reason}
              </div>
            )}
            {event.beforeState && Object.keys(event.beforeState).length > 0 && (
              <div className="text-sm mb-2">
                <strong className="text-gray-700">Before:</strong>
                <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                  {JSON.stringify(event.beforeState, null, 2)}
                </pre>
              </div>
            )}
            {event.afterState && Object.keys(event.afterState).length > 0 && (
              <div className="text-sm">
                <strong className="text-gray-700">After:</strong>
                <pre className="mt-1 p-2 bg-gray-50 rounded text-xs overflow-x-auto">
                  {JSON.stringify(event.afterState, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

