import { useMemo, useState } from 'react'
import { ArrowUpDown, Search as SearchIcon, Inbox } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/Select'
import { PriorityBadge, StatusBadge, CategoryBadge, SentimentBadge, SlaBadge } from '@/components/ui/TicketBadges'
import { ConfidenceBar } from '@/components/ui/ConfidenceBar'
import { EmptyState, TableSkeleton } from '@/components/ui/States'
import { TicketDetailDrawer } from '@/components/tickets/TicketDetailDrawer'
import { useTickets } from '@/context/TicketsContext'
import type { Ticket, TicketStatus, TicketCategory, TicketPriority } from '@/lib/mock-data'

type SortKey = 'updatedAt' | 'priority' | 'slaDeadline'

const priorityRank: Record<TicketPriority, number> = { critical: 0, high: 1, medium: 2, low: 3 }

export function TicketsPage() {
  const { tickets } = useTickets()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<TicketStatus | 'all'>('all')
  const [categoryFilter, setCategoryFilter] = useState<TicketCategory | 'all'>('all')
  const [sortKey, setSortKey] = useState<SortKey>('updatedAt')
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null)
  const [loading] = useState(false) // demo hook point for a real loading state

  const filtered = useMemo(() => {
    let result = tickets.filter(t => {
      const matchesSearch =
        search.trim() === '' ||
        t.subject.toLowerCase().includes(search.toLowerCase()) ||
        t.customer.toLowerCase().includes(search.toLowerCase()) ||
        t.id.toLowerCase().includes(search.toLowerCase()) ||
        t.tags.some(tag => tag.toLowerCase().includes(search.toLowerCase()))
      const matchesStatus = statusFilter === 'all' || t.status === statusFilter
      const matchesCategory = categoryFilter === 'all' || t.category === categoryFilter
      return matchesSearch && matchesStatus && matchesCategory
    })

    result = [...result].sort((a, b) => {
      if (sortKey === 'priority') return priorityRank[a.priority] - priorityRank[b.priority]
      if (sortKey === 'slaDeadline') return new Date(a.slaDeadline).getTime() - new Date(b.slaDeadline).getTime()
      return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    })

    return result
  }, [tickets, search, statusFilter, categoryFilter, sortKey])

  const selectedTicket: Ticket | undefined = tickets.find(t => t.id === selectedTicketId)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-foreground">Tickets Inbox</h1>
          <p className="text-sm text-muted-foreground">{filtered.length} of {tickets.length} tickets</p>
        </div>
      </div>

      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[220px]">
            <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search by subject, customer, ID, or tag..."
              aria-label="Search tickets"
              className="pl-9"
            />
          </div>

          <Select value={statusFilter} onValueChange={v => setStatusFilter(v as TicketStatus | 'all')}>
            <SelectTrigger className="w-40" aria-label="Filter by status">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="open">Open</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
            </SelectContent>
          </Select>

          <Select value={categoryFilter} onValueChange={v => setCategoryFilter(v as TicketCategory | 'all')}>
            <SelectTrigger className="w-40" aria-label="Filter by category">
              <SelectValue placeholder="Category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All categories</SelectItem>
              <SelectItem value="billing">Billing</SelectItem>
              <SelectItem value="technical">Technical</SelectItem>
              <SelectItem value="account">Account</SelectItem>
              <SelectItem value="general">General</SelectItem>
              <SelectItem value="shipping">Shipping</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setSortKey(k => (k === 'updatedAt' ? 'priority' : k === 'priority' ? 'slaDeadline' : 'updatedAt'))}
          >
            <ArrowUpDown className="w-3.5 h-3.5" />
            Sort: {sortKey === 'updatedAt' ? 'Recently updated' : sortKey === 'priority' ? 'Priority' : 'SLA deadline'}
          </Button>
        </div>
      </Card>

      <Card className="overflow-hidden">
        {loading ? (
          <div className="p-4"><TableSkeleton /></div>
        ) : filtered.length === 0 ? (
          <EmptyState
            icon={<Inbox className="w-6 h-6" />}
            title="No tickets match your filters"
            description="Try adjusting your search or filters to see more results."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-muted-foreground">
                  <th className="px-4 py-3 font-medium">Ticket</th>
                  <th className="px-4 py-3 font-medium">Priority</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Category</th>
                  <th className="px-4 py-3 font-medium">Sentiment</th>
                  <th className="px-4 py-3 font-medium">AI Confidence</th>
                  <th className="px-4 py-3 font-medium">SLA</th>
                  <th className="px-4 py-3 font-medium">Assignee</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(ticket => (
                  <tr
                    key={ticket.id}
                    onClick={() => setSelectedTicketId(ticket.id)}
                    className="border-b border-border last:border-0 cursor-pointer hover:bg-muted/50 transition-colors"
                  >
                    <td className="px-4 py-3 max-w-xs">
                      <p className="text-xs font-mono text-muted-foreground">{ticket.id}</p>
                      <p className="text-sm font-medium text-foreground truncate">{ticket.subject}</p>
                      <p className="text-xs text-muted-foreground truncate">{ticket.customer}</p>
                    </td>
                    <td className="px-4 py-3"><PriorityBadge priority={ticket.priority} /></td>
                    <td className="px-4 py-3"><StatusBadge status={ticket.status} /></td>
                    <td className="px-4 py-3"><CategoryBadge category={ticket.category} /></td>
                    <td className="px-4 py-3"><SentimentBadge sentiment={ticket.sentiment} /></td>
                    <td className="px-4 py-3"><ConfidenceBar value={ticket.aiConfidence} /></td>
                    <td className="px-4 py-3"><SlaBadge deadline={ticket.slaDeadline} breached={ticket.slaBreached} /></td>
                    <td className="px-4 py-3">
                      {ticket.assignee ? (
                        <div className="flex items-center gap-2">
                          <Avatar initials={ticket.assignee.split(' ').map(n => n[0]).join('')} size="sm" />
                          <span className="text-xs text-foreground">{ticket.assignee}</span>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">Unassigned</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {selectedTicket && (
        <TicketDetailDrawer
          ticket={selectedTicket}
          open={!!selectedTicketId}
          onOpenChange={open => !open && setSelectedTicketId(null)}
        />
      )}
    </div>
  )
}
