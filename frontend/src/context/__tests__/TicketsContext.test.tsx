import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { TicketsProvider, useTickets } from '@/context/TicketsContext'

describe('TicketsContext', () => {
  it('corrects a ticket category and records activity + pending feedback', () => {
    const { result } = renderHook(() => useTickets(), { wrapper: TicketsProvider })
    const ticket = result.current.tickets[0]

    act(() => result.current.correctCategory(ticket.id, 'shipping', 'Test Agent'))

    const updated = result.current.getTicket(ticket.id)
    expect(updated?.category).toBe('shipping')
    expect(updated?.activity.some(a => a.type === 'category_correction')).toBe(true)

    const feedbackEntry = result.current.feedback.find(f => f.ticketId === ticket.id && f.agentLabel === 'shipping')
    expect(feedbackEntry?.status).toBe('pending')
  })

  it('accepts an AI prediction and applies the suggested category', () => {
    const { result } = renderHook(() => useTickets(), { wrapper: TicketsProvider })
    const ticket = result.current.tickets.find(t => t.aiPredictionAccepted === null)!

    act(() => result.current.acceptAiPrediction(ticket.id, 'Test Agent'))

    const updated = result.current.getTicket(ticket.id)
    expect(updated?.aiPredictionAccepted).toBe(true)
    expect(updated?.category).toBe(ticket.aiSuggestedCategory)
  })

  it('approves pending feedback', () => {
    const { result } = renderHook(() => useTickets(), { wrapper: TicketsProvider })
    const pending = result.current.feedback.find(f => f.status === 'pending')!

    act(() => result.current.approveFeedback(pending.id))

    expect(result.current.feedback.find(f => f.id === pending.id)?.status).toBe('approved')
  })
})
