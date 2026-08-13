import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { Inbox, Clock, ShieldCheck, Brain, CheckCircle2 } from 'lucide-react'
import { StatCard } from '@/components/ui/StatCard'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import {
  overviewStats, ticketVolumeData, aiAccuracyData, categoryDistribution, slaData,
} from '@/lib/mock-data'

const chartAxisProps = {
  tick: { fontSize: 11, fill: 'hsl(var(--muted-foreground))' },
  tickLine: false,
  axisLine: false,
}

export function OverviewPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-foreground">Overview</h1>
        <p className="text-sm text-muted-foreground">Real-time snapshot of ticket triage performance</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          label="Open Tickets"
          value={overviewStats.openTickets}
          delta={overviewStats.openDelta}
          icon={<Inbox className="w-5 h-5" />}
        />
        <StatCard
          label="Avg Response Time"
          value={overviewStats.avgResponseTime}
          delta={overviewStats.responseDelta}
          deltaLabel="s"
          icon={<Clock className="w-5 h-5" />}
          iconColor="bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400"
        />
        <StatCard
          label="SLA Compliance"
          value={`${overviewStats.slaCompliance}%`}
          delta={overviewStats.slaDelta}
          deltaLabel="%"
          icon={<ShieldCheck className="w-5 h-5" />}
          iconColor="bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400"
        />
        <StatCard
          label="AI Accuracy"
          value={`${overviewStats.aiAccuracy}%`}
          delta={overviewStats.aiDelta}
          deltaLabel="%"
          icon={<Brain className="w-5 h-5" />}
          iconColor="bg-violet-100 text-violet-600 dark:bg-violet-900/30 dark:text-violet-400"
        />
        <StatCard
          label="Resolved Today"
          value={overviewStats.resolvedToday}
          delta={overviewStats.resolvedDelta}
          icon={<CheckCircle2 className="w-5 h-5" />}
          iconColor="bg-sky-100 text-sky-600 dark:bg-sky-900/30 dark:text-sky-400"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Ticket Volume (7 days)</CardTitle>
            <CardDescription>Inbound tickets across all channels</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={ticketVolumeData}>
                <defs>
                  <linearGradient id="volumeFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#3366ff" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#3366ff" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis dataKey="date" {...chartAxisProps} />
                <YAxis {...chartAxisProps} width={32} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Area type="monotone" dataKey="value" stroke="#3366ff" fill="url(#volumeFill)" strokeWidth={2} name="Tickets" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Category Distribution</CardTitle>
            <CardDescription>Current open ticket mix</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={categoryDistribution} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75} paddingAngle={2}>
                  {categoryDistribution.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>AI Classification Accuracy</CardTitle>
            <CardDescription>Trailing 7-day accuracy trend</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={aiAccuracyData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis dataKey="date" {...chartAxisProps} />
                <YAxis {...chartAxisProps} width={36} domain={[80, 100]} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} formatter={(v: number) => [`${v}%`, 'Accuracy']} />
                <Area type="monotone" dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.15} strokeWidth={2} name="Accuracy %" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>SLA Met vs Breached</CardTitle>
            <CardDescription>Daily SLA outcome breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={slaData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis dataKey="date" {...chartAxisProps} />
                <YAxis {...chartAxisProps} width={32} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="met" stackId="a" fill="#10b981" name="Met" radius={[0, 0, 0, 0]} />
                <Bar dataKey="breached" stackId="a" fill="#ef4444" name="Breached" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
