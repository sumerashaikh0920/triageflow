import { AlertTriangle, Circle, Clock, CheckCircle2, XCircle } from 'lucide-react'
import { Badge } from './Badge'
import type { TicketPriority, TicketStatus, TicketCategory, TicketSentiment } from '@/lib/mock-data'

export function PriorityBadge({ priority }: { priority: TicketPriority }) {
  const config: Record<TicketPriority, { label: string; variant: 'danger' | 'warning' | 'info' | 'neutral' }> = {
    critical: { label: 'Critical', variant: 'danger' },
    high: { label: 'High', variant: 'warning' },
    medium: { label: 'Medium', variant: 'info' },
    low: { label: 'Low', variant: 'neutral' },
  }
  const { label, variant } = config[priority]
  return (
    <Badge variant={variant}>
      {priority === 'critical' && <AlertTriangle className="w-3 h-3" />}
      {label}
    </Badge>
  )
}

export function StatusBadge({ status }: { status: TicketStatus }) {
  const config: Record<TicketStatus, { label: string; variant: 'info' | 'warning' | 'success' | 'neutral' }> = {
    open: { label: 'Open', variant: 'info' },
    in_progress: { label: 'In Progress', variant: 'warning' },
    pending: { label: 'Pending', variant: 'neutral' },
    resolved: { label: 'Resolved', variant: 'success' },
    closed: { label: 'Closed', variant: 'neutral' },
  }
  const { label, variant } = config[status]
  return <Badge variant={variant}>{label}</Badge>
}

export function CategoryBadge({ category }: { category: TicketCategory }) {
  const labels: Record<TicketCategory, string> = {
    billing: 'Billing',
    technical: 'Technical',
    account: 'Account',
    general: 'General',
    shipping: 'Shipping',
  }
  return <Badge variant="default">{labels[category]}</Badge>
}

export function SentimentBadge({ sentiment }: { sentiment: TicketSentiment }) {
  const config: Record<TicketSentiment, { label: string; variant: 'success' | 'neutral' | 'warning' | 'danger' }> = {
    positive: { label: 'Positive', variant: 'success' },
    neutral: { label: 'Neutral', variant: 'neutral' },
    negative: { label: 'Negative', variant: 'warning' },
    frustrated: { label: 'Frustrated', variant: 'danger' },
  }
  const { label, variant } = config[sentiment]
  return <Badge variant={variant}>{label}</Badge>
}

export function SlaBadge({ deadline, breached }: { deadline: string; breached: boolean }) {
  if (breached) {
    return (
      <Badge variant="danger">
        <XCircle className="w-3 h-3" />
        Breached
      </Badge>
    )
  }

  const msLeft = new Date(deadline).getTime() - Date.now()
  const hoursLeft = msLeft / (1000 * 60 * 60)

  if (hoursLeft <= 2) {
    return (
      <Badge variant="warning">
        <Clock className="w-3 h-3" />
        {Math.max(0, Math.round(hoursLeft * 60))}m left
      </Badge>
    )
  }

  return (
    <Badge variant="success">
      <CheckCircle2 className="w-3 h-3" />
      {Math.round(hoursLeft)}h left
    </Badge>
  )
}

export function StatusDot({ status }: { status: 'online' | 'away' | 'offline' }) {
  const colors = { online: 'text-emerald-500', away: 'text-amber-500', offline: 'text-gray-400' }
  return <Circle className={`w-2 h-2 fill-current ${colors[status]}`} />
}
