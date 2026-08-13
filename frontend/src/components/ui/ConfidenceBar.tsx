import { cn } from '@/lib/utils'

export function ConfidenceBar({ value, className }: { value: number; className?: string }) {
  const pct = Math.round(value * 100)
  const color =
    pct >= 85 ? 'bg-emerald-500' : pct >= 65 ? 'bg-amber-500' : 'bg-red-500'

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="w-16 h-1.5 rounded-full bg-muted overflow-hidden" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className={cn('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs tabular-nums text-muted-foreground">{pct}%</span>
    </div>
  )
}
