import { CheckCircle2, XCircle, Info, X } from 'lucide-react'
import { useToast } from '@/context/ToastContext'
import { cn } from '@/lib/utils'

const iconMap = {
  default: Info,
  success: CheckCircle2,
  error: XCircle,
}

const colorMap = {
  default: 'border-border bg-card text-foreground',
  success: 'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-200',
  error: 'border-red-200 bg-red-50 text-red-900 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-200',
}

export function ToastViewport() {
  const { toasts, dismissToast } = useToast()

  if (toasts.length === 0) return null

  return (
    <div
      role="region"
      aria-label="Notifications"
      className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-full max-w-sm"
    >
      {toasts.map(toast => {
        const Icon = iconMap[toast.variant || 'default']
        return (
          <div
            key={toast.id}
            role="status"
            className={cn(
              'flex items-start gap-3 rounded-lg border p-4 shadow-lg animate-in fade-in slide-in-from-bottom-2',
              colorMap[toast.variant || 'default'],
            )}
          >
            <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold">{toast.title}</p>
              {toast.description && <p className="text-xs mt-0.5 opacity-80">{toast.description}</p>}
            </div>
            <button
              onClick={() => dismissToast(toast.id)}
              aria-label="Dismiss notification"
              className="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
