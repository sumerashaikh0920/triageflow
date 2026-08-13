import { createContext, useContext, useState, ReactNode } from 'react'
import {
  mockTickets,
  feedbackItems as initialFeedbackItems,
  Ticket,
  TicketCategory,
  TicketPriority,
  FeedbackItem,
  ActivityEvent,
} from '@/lib/mock-data'

interface TicketsContextValue {
  tickets: Ticket[]
  feedback: FeedbackItem[]
  getTicket: (id: string) => Ticket | undefined
  correctCategory: (ticketId: string, newCategory: TicketCategory, actor: string) => void
  markUrgency: (ticketId: string, priority: TicketPriority, actor: string) => void
  acceptAiPrediction: (ticketId: string, actor: string) => void
  approveFeedback: (feedbackId: string) => void
  rejectFeedback: (feedbackId: string) => void
}

const TicketsContext = createContext<TicketsContextValue | null>(null)

function newActivityEvent(partial: Omit<ActivityEvent, 'id' | 'timestamp'>): ActivityEvent {
  return {
    ...partial,
    id: `a-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    timestamp: new Date().toISOString(),
  }
}

export function TicketsProvider({ children }: { children: ReactNode }) {
  const [tickets, setTickets] = useState<Ticket[]>(mockTickets)
  const [feedback, setFeedback] = useState<FeedbackItem[]>(initialFeedbackItems)

  const getTicket = (id: string) => tickets.find(t => t.id === id)

  const updateTicket = (ticketId: string, updater: (t: Ticket) => Ticket) => {
    setTickets(prev => prev.map(t => (t.id === ticketId ? updater(t) : t)))
  }

  const correctCategory = (ticketId: string, newCategory: TicketCategory, actor: string) => {
    updateTicket(ticketId, t => ({
      ...t,
      category: newCategory,
      updatedAt: new Date().toISOString(),
      activity: [
        ...t.activity,
        newActivityEvent({
          type: 'category_correction',
          actor,
          detail: `Corrected category from "${t.category}" to "${newCategory}"`,
        }),
      ],
    }))

    setFeedback(prev => [
      {
        id: `fb-${Date.now()}`,
        ticketId,
        aiLabel: tickets.find(t => t.id === ticketId)?.aiSuggestedCategory ?? '—',
        agentLabel: newCategory,
        confidence: tickets.find(t => t.id === ticketId)?.aiConfidence ?? 0,
        status: 'pending',
        agent: actor,
        submittedAt: new Date().toISOString(),
      },
      ...prev,
    ])
  }

  const markUrgency = (ticketId: string, priority: TicketPriority, actor: string) => {
    updateTicket(ticketId, t => ({
      ...t,
      priority,
      updatedAt: new Date().toISOString(),
      activity: [
        ...t.activity,
        newActivityEvent({
          type: 'urgency_change',
          actor,
          detail: `Urgency changed to "${priority}"`,
        }),
      ],
    }))
  }

  const acceptAiPrediction = (ticketId: string, actor: string) => {
    updateTicket(ticketId, t => ({
      ...t,
      category: t.aiSuggestedCategory,
      aiPredictionAccepted: true,
      updatedAt: new Date().toISOString(),
      activity: [
        ...t.activity,
        newActivityEvent({
          type: 'ai_accepted',
          actor,
          detail: `Accepted AI prediction: "${t.aiSuggestedCategory}" (${Math.round(t.aiConfidence * 100)}% confidence)`,
        }),
      ],
    }))
  }

  const approveFeedback = (feedbackId: string) => {
    setFeedback(prev => prev.map(f => (f.id === feedbackId ? { ...f, status: 'approved' } : f)))
  }

  const rejectFeedback = (feedbackId: string) => {
    setFeedback(prev => prev.map(f => (f.id === feedbackId ? { ...f, status: 'rejected' } : f)))
  }

  return (
    <TicketsContext.Provider
      value={{ tickets, feedback, getTicket, correctCategory, markUrgency, acceptAiPrediction, approveFeedback, rejectFeedback }}
    >
      {children}
    </TicketsContext.Provider>
  )
}

export function useTickets() {
  const ctx = useContext(TicketsContext)
  if (!ctx) throw new Error('useTickets must be used within TicketsProvider')
  return ctx
}
