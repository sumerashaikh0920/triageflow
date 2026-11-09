import { createContext } from 'react'
import { Ticket, TicketCategory, TicketPriority, FeedbackItem } from '@/lib/mock-data'

export interface TicketsContextValue {
  tickets: Ticket[]
  feedback: FeedbackItem[]
  getTicket: (id: string) => Ticket | undefined
  correctCategory: (ticketId: string, newCategory: TicketCategory, actor: string) => void
  markUrgency: (ticketId: string, priority: TicketPriority, actor: string) => void
  acceptAiPrediction: (ticketId: string, actor: string) => void
  approveFeedback: (feedbackId: string) => void
  rejectFeedback: (feedbackId: string) => void
}

export const TicketsContext = createContext<TicketsContextValue | null>(null)
