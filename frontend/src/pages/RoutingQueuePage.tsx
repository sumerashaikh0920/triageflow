import { Route as RouteIcon } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { CategoryBadge } from '@/components/ui/TicketBadges'
import { routingRules } from '@/lib/mock-data'

export function RoutingQueuePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-foreground">Routing Queue</h1>
        <p className="text-sm text-muted-foreground">How AI-classified tickets are routed to teams</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {routingRules.map(rule => (
          <Card key={rule.id}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 flex items-center justify-center">
                  <RouteIcon className="w-4 h-4" />
                </div>
                <CardTitle>{rule.destination}</CardTitle>
              </div>
              <Badge variant={rule.active ? 'success' : 'neutral'}>{rule.active ? 'Active' : 'Inactive'}</Badge>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Category</span>
                <CategoryBadge category={rule.category} />
              </div>
              <CardDescription>Condition: {rule.condition}</CardDescription>
              <p className="text-xs text-muted-foreground pt-2 border-t border-border">
                <span className="font-semibold text-foreground tabular-nums">{rule.ticketsRoutedToday}</span> tickets routed today
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
