import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { StatCard } from '@/components/ui/StatCard'
import { Badge } from '@/components/ui/Badge'
import { Target, Gauge, Clock3, Database } from 'lucide-react'
import {
  modelMetrics, aiAccuracyData, f1ScoreData, latencyData, dataFreshnessData,
  modelVersionHistory, confusionMatrix, confusionClasses,
} from '@/lib/mock-data'

const axisProps = { tick: { fontSize: 11, fill: 'hsl(var(--muted-foreground))' }, tickLine: false, axisLine: false }

export function ModelMetricsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-bold text-foreground">Model Metrics</h1>
        <p className="text-sm text-muted-foreground">Classifier performance for model {modelMetrics.modelVersion}</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Accuracy" value={`${(modelMetrics.accuracy * 100).toFixed(1)}%`} icon={<Target className="w-5 h-5" />} />
        <StatCard label="F1 Score" value={`${(modelMetrics.f1 * 100).toFixed(1)}%`} icon={<Gauge className="w-5 h-5" />} iconColor="bg-violet-100 text-violet-600 dark:bg-violet-900/30 dark:text-violet-400" />
        <StatCard label="Avg Latency" value={`${modelMetrics.latencyMs}ms`} icon={<Clock3 className="w-5 h-5" />} iconColor="bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400" />
        <StatCard label="Data Freshness" value={`${modelMetrics.dataFreshnessHours}h`} icon={<Database className="w-5 h-5" />} iconColor="bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Accuracy vs F1 (7 days)</CardTitle>
            <CardDescription>Both metrics trending upward since last retrain</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis dataKey="date" allowDuplicatedCategory={false} {...axisProps} />
                <YAxis domain={[80, 100]} {...axisProps} width={36} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Line data={aiAccuracyData} dataKey="value" name="Accuracy %" stroke="#3366ff" strokeWidth={2} dot={false} />
                <Line data={f1ScoreData} dataKey="value" name="F1 %" stroke="#8b5cf6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Inference Latency (7 days)</CardTitle>
            <CardDescription>p50 inference latency in milliseconds</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis dataKey="date" {...axisProps} />
                <YAxis {...axisProps} width={32} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} formatter={(v: number) => [`${v}ms`, 'Latency']} />
                <Line dataKey="value" name="Latency (ms)" stroke="#f59e0b" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Data Freshness (7 days)</CardTitle>
            <CardDescription>Hours since last feedback ingestion, lower is better</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={dataFreshnessData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                <XAxis dataKey="date" {...axisProps} />
                <YAxis {...axisProps} width={32} />
                <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} formatter={(v: number) => [`${v}h`, 'Freshness']} />
                <Line dataKey="value" name="Hours since ingest" stroke="#10b981" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Confusion Matrix</CardTitle>
            <CardDescription>Actual (rows) vs predicted (columns)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="text-xs w-full">
                <thead>
                  <tr>
                    <th className="p-1"></th>
                    {confusionClasses.map(c => (
                      <th key={c} className="p-1 font-medium text-muted-foreground">{c.slice(0, 4)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {confusionMatrix.map((row, i) => (
                    <tr key={i}>
                      <td className="p-1 font-medium text-muted-foreground text-right pr-2">{confusionClasses[i].slice(0, 4)}</td>
                      {row.map((val, j) => (
                        <td key={j} className="p-1 text-center">
                          <span
                            className="inline-flex items-center justify-center w-9 h-9 rounded-md tabular-nums"
                            style={{
                              backgroundColor: i === j ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.08)',
                              color: i === j ? '#059669' : 'inherit',
                            }}
                          >
                            {val}
                          </span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Model Version History</CardTitle>
          <CardDescription>Model registry entries produced by the retraining pipeline</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="px-3 py-2 font-medium">Version</th>
                  <th className="px-3 py-2 font-medium">Deployed</th>
                  <th className="px-3 py-2 font-medium">Accuracy</th>
                  <th className="px-3 py-2 font-medium">F1</th>
                  <th className="px-3 py-2 font-medium">Training examples</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {modelVersionHistory.map(v => (
                  <tr key={v.version} className="border-b border-border last:border-0">
                    <td className="px-3 py-2 font-mono text-xs text-foreground">{v.version}</td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">{new Date(v.deployedAt).toLocaleDateString()}</td>
                    <td className="px-3 py-2 tabular-nums">{(v.accuracy * 100).toFixed(1)}%</td>
                    <td className="px-3 py-2 tabular-nums">{(v.f1 * 100).toFixed(1)}%</td>
                    <td className="px-3 py-2 tabular-nums">{v.trainingExamples.toLocaleString()}</td>
                    <td className="px-3 py-2">
                      <Badge variant={v.status === 'active' ? 'success' : v.status === 'candidate' ? 'info' : 'neutral'}>
                        {v.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
