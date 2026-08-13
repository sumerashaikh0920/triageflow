import { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { Card, CardContent } from './Card'

interface StatCardProps {
  label: string
  value: string | number
  delta?: number
  deltaLabel?: string
  icon?: ReactNode
  iconColor?: string
  className?: string
}

export function StatCard({ label, value, delta, deltaLabel, icon, iconColor = 'bg-brand-100 text-brand-600 dark:bg-brand-900/30 dark:text-brand-400', className }: StatCardProps) {
  const isPositive = delta !== undefined && delta >= 0
  const isNegative = delta !== undefined && delta < 0

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardContent className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-muted-foreground truncate">{label}</p>
          <p className="mt-1.5 text-2xl font-bold text-foreground tabular-nums">{value}</p>
          {delta !== undefined && (
            <p className={cn('mt-1 text-xs font-medium', isPositive && 'text-emerald-600 dark:text-emerald-400', isNegative && 'text-red-600 dark:text-red-400')}>
              {isPositive ? '+' : ''}{delta}{deltaLabel || ''}
              <span className="ml-1 text-muted-foreground font-normal">vs yesterday</span>
            </p>
          )}
        </div>
        {icon && (
          <div className={cn('flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center', iconColor)}>
            {icon}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
