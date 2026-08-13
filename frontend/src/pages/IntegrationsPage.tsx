import { Plug, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { integrations } from '@/lib/mock-data'

const statusConfig = {
  connected: { label: 'Connected', variant: 'success' as const, icon: CheckCircle2 },
  disconnected: { label: 'Disconnected', variant: 'neutral' as const, icon: XCircle },
  error: { label: 'Error', variant: 'danger' as const, icon: AlertTriangle },
}

export function IntegrationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-foreground">Integrations</h1>
        <p className="text-sm text-muted-foreground">Ticket ingestion, notification, and CRM connections</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {integrations.map(int => {
          const status = statusConfig[int.status]
          const StatusIcon = status.icon
          return (
            <Card key={int.id}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 flex items-center justify-center">
                    <Plug className="w-4 h-4" />
                  </div>
                  <CardTitle>{int.name}</CardTitle>
                </div>
                <Badge variant={status.variant}>
                  <StatusIcon className="w-3 h-3" />
                  {status.label}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-1">
                <CardDescription>{int.description}</CardDescription>
                <p className="text-xs text-muted-foreground pt-2 border-t border-border">
                  {int.lastSync ? `Last sync: ${new Date(int.lastSync).toLocaleString()}` : 'Never connected'}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
