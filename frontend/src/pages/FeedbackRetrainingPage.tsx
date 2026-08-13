import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card'
import { StatCard } from '@/components/ui/StatCard'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { EmptyState } from '@/components/ui/States'
import { useTickets } from '@/context/TicketsContext'
import { useToast } from '@/context/ToastContext'
import { useAuth } from '@/context/AuthContext'
import { modelMetrics } from '@/lib/mock-data'

const statusVariant = { pending: 'neutral', approved: 'success', rejected: 'danger' } as const

export function FeedbackRetrainingPage() {
  const { feedback, approveFeedback, rejectFeedback } = useTickets()
  const { showToast } = useToast()
  const { user } = useAuth()

  const canReview = user?.role === 'team_lead' || user?.role === 'admin'
  const canTriggerRetrain = user?.role === 'admin'

  const pending = feedback.filter(f => f.status === 'pending')
  const approvedCount = feedback.filter(f => f.status === 'approved').length + modelMetrics.approvedCorrections
  const progressPct = Math.min(100, Math.round((approvedCount / modelMetrics.retrainThreshold) * 100))

  const handleApprove = (id: string, ticketId: string) => {
    approveFeedback(id)
    showToast({ title: 'Feedback approved', description: `Correction for ${ticketId} added to the retraining set.`, variant: 'success' })
  }

  const handleReject = (id: string, ticketId: string) => {
    rejectFeedback(id)
    showToast({ title: 'Feedback rejected', description: `Correction for ${ticketId} was discarded.`, variant: 'default' })
  }

  const handleManualRetrain = () => {
    showToast({
      title: 'Retraining triggered (demo)',
      description: 'In production this calls the scheduled/event-driven GitHub Actions retraining workflow.',
      variant: 'success',
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-lg font-bold text-foreground">Feedback &amp; Retraining</h1>
          <p className="text-sm text-muted-foreground">Human corrections feed the retraining pipeline</p>
        </div>
        {canTriggerRetrain && (
          <Button variant="primary" size="sm" onClick={handleManualRetrain}>
            <RefreshCw className="w-3.5 h-3.5" />
            Trigger manual retrain
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Pending Review" value={pending.length} />
        <StatCard label="Approved Corrections" value={approvedCount} />
        <StatCard label="Retrain Threshold" value={modelMetrics.retrainThreshold} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Retraining Progress</CardTitle>
          <CardDescription>
            Approved corrections toward the automatic retraining threshold (fires the event-driven GitHub Actions workflow)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="w-full h-2.5 rounded-full bg-muted overflow-hidden">
            <div className="h-full bg-brand-500 rounded-full transition-all" style={{ width: `${progressPct}%` }} />
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            {approvedCount} / {modelMetrics.retrainThreshold} approved corrections ({progressPct}%)
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Pending Corrections</CardTitle>
          <CardDescription>Agent-submitted category corrections awaiting review</CardDescription>
        </CardHeader>
        <CardContent>
          {pending.length === 0 ? (
            <EmptyState title="No pending feedback" description="All submitted corrections have been reviewed." />
          ) : (
            <div className="space-y-2">
              {pending.map(f => (
                <div key={f.id} className="flex items-center justify-between p-3 rounded-lg border border-border flex-wrap gap-2">
                  <div>
                    <p className="text-xs font-mono text-muted-foreground">{f.ticketId}</p>
                    <p className="text-sm text-foreground">
                      AI said <span className="font-medium">{f.aiLabel}</span> &rarr; {f.agent} corrected to{' '}
                      <span className="font-medium">{f.agentLabel}</span>
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={statusVariant[f.status]}>{f.status}</Badge>
                    {canReview && (
                      <>
                        <Button variant="outline" size="sm" onClick={() => handleApprove(f.id, f.ticketId)}>
                          <CheckCircle2 className="w-3.5 h-3.5" /> Approve
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleReject(f.id, f.ticketId)}>
                          <XCircle className="w-3.5 h-3.5" /> Reject
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recently Reviewed</CardTitle>
        </CardHeader>
        <CardContent>
          {feedback.filter(f => f.status !== 'pending').length === 0 ? (
            <EmptyState title="No reviewed feedback yet" />
          ) : (
            <div className="space-y-2">
              {feedback.filter(f => f.status !== 'pending').map(f => (
                <div key={f.id} className="flex items-center justify-between p-3 rounded-lg border border-border">
                  <p className="text-sm text-foreground">
                    <span className="font-mono text-xs text-muted-foreground mr-2">{f.ticketId}</span>
                    {f.aiLabel} &rarr; {f.agentLabel}
                  </p>
                  <Badge variant={statusVariant[f.status]}>{f.status}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
