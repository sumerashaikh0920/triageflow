import { cn } from '@/lib/utils'
import { HTMLAttributes } from 'react'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'neutral'
}

const variantClasses: Record<NonNullable<BadgeProps['variant']>, string> = {
  default:  'bg-brand-100 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300',
  success:  'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  warning:  'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  danger:   'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  info:     'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400',
  neutral:  'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}

export function Badge({ variant = 'default', className, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
        variantClasses[variant],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  )
}
