import { useState } from 'react'
import { Brain, Route, Check, User, Mail, Building2 } from 'lucide-react'
import { Drawer, DrawerContent } from '@/components/ui/Drawer'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs'
import { Card, CardContent } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/Select'
import { PriorityBadge, StatusBadge, CategoryBadge, SentimentBadge, SlaBadge } from '@/components/ui/TicketBadges'
import { ConfidenceBar } from '@/components/ui/ConfidenceBar'
import { useTickets } from '@/context/TicketsContext'
import { useAuth } from '@/context/AuthContext'
import { useToast } from '@/context/ToastContext'
import type { Ticket, TicketCategory, TicketPriority } from '@/lib/mock-data'

const categoryOptions: TicketCategory[] = ['billing', 'technical', 'account', 'general', 'shipping']
const priorityOptions: TicketPriority[] = ['critical', 'high', 'medium', 'low']

export function TicketDetailDrawer({
  ticket,
  open,
  onOpenChange,
}: {
  ticket: Ticket
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const { correctCategory, markUrgency, acceptAiPrediction } = useTickets()
  const { user } = useAuth()
  const { showToast } = useToast()
  const [pendingCategory, setPendingCategory] = useState<TicketCategory>(ticket.category)

  const actor = user?.name ?? 'You'

  const handleCorrectCategory = () => {
    if (pendingCategory === ticket.category) return
    correctCategory(ticket.id, pendingCategory, actor)
    showToast({
      title: 'Category corrected',
      description: `${ticket.id} recategorized as "${pendingCategory}". Submitted for feedback review.`,
      variant: 'success',
    })
  }

  const handleMarkUrgency = (priority: TicketPriority) => {
    markUrgency(ticket.id, priority, actor)
    showToast({
      title: 'Urgency updated',
      description: `${ticket.id} marked as "${priority}" priority.`,
      variant: 'success',
    })
  }

  const handleAcceptPrediction = () => {
    acceptAiPrediction(ticket.id, actor)
    setPendingCategory(ticket.aiSuggestedCategory)
    showToast({
      title: 'AI prediction accepted',
      description: `${ticket.id} confirmed as "${ticket.aiSuggestedCategory}" (${Math.round(ticket.aiConfidence * 100)}% confidence).`,
      variant: 'success',
    })
  }

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent title={`${ticket.id} \u2014 ${ticket.subject}`}>
        <div className="flex flex-wrap items-center gap-2 mb-5">
          <PriorityBadge priority={ticket.priority} />
          <StatusBadge status={ticket.status} />
          <CategoryBadge category={ticket.category} />
          <SentimentBadge sentiment={ticket.sentiment} />
          <SlaBadge deadline={ticket.slaDeadline} breached={ticket.slaBreached} />
        </div>

        <Tabs defaultValue="details">
          <TabsList>
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="messages">Messages</TabsTrigger>
            <TabsTrigger value="activity">Activity</TabsTrigger>
            <TabsTrigger value="ai">AI &amp; Routing</TabsTrigger>
          </TabsList>

          <TabsContent value="details">
            <Card>
              <CardContent className="space-y-3">
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Customer</p>
                <div className="flex items-center gap-3">
                  <Avatar initials={ticket.customer.split(' ').map(n => n[0]).join('')} />
                  <div>
                    <p className="text-sm font-medium text-foreground flex items-center gap-1.5"><User className="w-3.5 h-3.5 text-muted-foreground" />{ticket.customer}</p>
                    <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5"><Mail className="w-3.5 h-3.5" />{ticket.customerEmail}</p>
                    <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-0.5"><Building2 className="w-3.5 h-3.5" />{ticket.customerCompany}</p>
                  </div>
                </div>

                <div className="pt-3 border-t border-border grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <p className="text-muted-foreground">Created</p>
                    <p className="text-foreground font-medium">{new Date(ticket.createdAt).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Last updated</p>
                    <p className="text-foreground font-medium">{new Date(ticket.updatedAt).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">SLA deadline</p>
                    <p className="text-foreground font-medium">{new Date(ticket.slaDeadline).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Tags</p>
                    <p className="text-foreground font-medium">{ticket.tags.join(', ') || '—'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="mt-4 space-y-3">
              <Card>
                <CardContent className="space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Correct category</p>
                  <div className="flex items-center gap-2">
                    <Select value={pendingCategory} onValueChange={v => setPendingCategory(v as TicketCategory)}>
                      <SelectTrigger className="flex-1" aria-label="Select correct category">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {categoryOptions.map(c => (
                          <SelectItem key={c} value={c}>{c[0].toUpperCase() + c.slice(1)}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleCorrectCategory}
                      disabled={pendingCategory === ticket.category}
                    >
                      Save correction
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="space-y-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Mark urgency</p>
                  <div className="flex flex-wrap gap-2">
                    {priorityOptions.map(p => (
                      <Button
                        key={p}
                        variant={ticket.priority === p ? 'primary' : 'outline'}
                        size="sm"
                        onClick={() => handleMarkUrgency(p)}
                      >
                        {p[0].toUpperCase() + p.slice(1)}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="messages">
            <div className="space-y-3">
              {ticket.messages.map(m => (
                <Card key={m.id}>
                  <CardContent className="py-3">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-xs font-semibold text-foreground">{m.author}</p>
                      <p className="text-[11px] text-muted-foreground">{new Date(m.timestamp).toLocaleString()}</p>
                    </div>
                    <p className="text-sm text-foreground">{m.body}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="activity">
            <ol className="relative border-l border-border ml-2 space-y-5">
              {ticket.activity.map(event => (
                <li key={event.id} className="ml-4">
                  <span className="absolute -left-[5px] w-2.5 h-2.5 rounded-full bg-brand-500 mt-1.5" />
                  <p className="text-xs text-muted-foreground">{new Date(event.timestamp).toLocaleString()}</p>
                  <p className="text-sm text-foreground font-medium">{event.actor}</p>
                  <p className="text-xs text-muted-foreground">{event.detail}</p>
                </li>
              ))}
            </ol>
          </TabsContent>

          <TabsContent value="ai">
            <Card>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-2">
                  <Brain className="w-4 h-4 text-brand-600 dark:text-brand-400" />
                  <p className="text-sm font-semibold text-foreground">AI Prediction</p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <p className="text-muted-foreground">Suggested category</p>
                    <div className="mt-1"><CategoryBadge category={ticket.aiSuggestedCategory} /></div>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Confidence</p>
                    <div className="mt-1"><ConfidenceBar value={ticket.aiConfidence} /></div>
                  </div>
                </div>

                <div className="pt-3 border-t border-border">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide flex items-center gap-1.5 mb-2">
                    <Route className="w-3.5 h-3.5" /> Routing recommendation
                  </p>
                  <p className="text-sm text-foreground">{ticket.aiSuggestedRouting}</p>
                </div>

                <div className="pt-3 border-t border-border flex items-center justify-between">
                  {ticket.aiPredictionAccepted ? (
                    <p className="text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5" /> Prediction accepted
                    </p>
                  ) : (
                    <p className="text-xs text-muted-foreground">Not yet reviewed by an agent</p>
                  )}
                  <Button variant="primary" size="sm" onClick={handleAcceptPrediction} disabled={!!ticket.aiPredictionAccepted}>
                    Accept AI prediction
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </DrawerContent>
    </Drawer>
  )
}
