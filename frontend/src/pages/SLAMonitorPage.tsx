import { useMemo } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { StatCard } from '@/components/ui/StatCard'
import { PriorityBadge, SlaBadge } from '@/components/ui/TicketBadges'
import { EmptyState } from '@/components/ui/States'
import { Timer, ShieldAlert, ShieldCheck } from 'lucide-react'
import { useTickets } from '@/context/TicketsContext'
import { slaData } from '@/lib/mock-data'

export function SLAMonitorPage() {
  const { tickets } = useTickets()

  const breached = useMemo(() => tickets.filter(t => t.slaBreached), [tickets])
  const atRisk = useMemo(
    () =>
      tickets.filter(t => {
        if (t.slaBreached || t.status === 'resolved' || t.status === 'closed') return false
        const hoursLeft = (new Date(t.slaDeadline).getTime() - Date.now()) / (1000 * 60 * 60)
        return hoursLeft > 0 && hoursLeft <= 4
      }),
    [tickets],
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-foreground">SLA Monitor</h1>
        <p className="text-sm text-muted-foreground">Track tickets approaching or past their SLA deadline</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Breached" value={breached.length} icon={<ShieldAlert className="w-5 h-5" />} iconColor="bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400" />
        <StatCard label="At Risk (< 4h)" value={atRisk.length} icon={<Timer className="w-5 h-5" />} iconColor="bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400" />
        <StatCard label="Compliance (7d avg)" value="94.2%" icon={<ShieldCheck className="w-5 h-5" />} iconColor="bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>SLA Outcomes (7 days)</CardTitle>
          <CardDescription>Daily count of tickets meeting vs breaching SLA</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={slaData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={32} />
              <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
              <Bar dataKey="met" fill="#10b981" radius={[4, 4, 0, 0]} name="Met" />
              <Bar dataKey="breached" fill="#ef4444" radius={[4, 4, 0, 0]} name="Breached" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Breached &amp; At-Risk Tickets</CardTitle>
          <CardDescription>Tickets needing immediate attention</CardDescription>
        </CardHeader>
        <CardContent>
          {breached.length + atRisk.length === 0 ? (
            <EmptyState title="All tickets are within SLA" description="No breached or at-risk tickets right now." icon={<ShieldCheck className="w-6 h-6" />} />
          ) : (
            <div className="space-y-2">
              {[...breached, ...atRisk].map(t => (
                <div key={t.id} className="flex items-center justify-between p-3 rounded-lg border border-border">
                  <div className="min-w-0">
                    <p className="text-xs font-mono text-muted-foreground">{t.id}</p>
                    <p className="text-sm font-medium text-foreground truncate">{t.subject}</p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <PriorityBadge priority={t.priority} />
                    <SlaBadge deadline={t.slaDeadline} breached={t.slaBreached} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
