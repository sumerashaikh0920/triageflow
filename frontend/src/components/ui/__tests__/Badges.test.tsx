import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from '@/components/ui/Badge'
import { PriorityBadge, StatusBadge, SlaBadge } from '@/components/ui/TicketBadges'

describe('Badge', () => {
  it('renders children text', () => {
    render(<Badge variant="success">Approved</Badge>)
    expect(screen.getByText('Approved')).toBeInTheDocument()
  })
})

describe('PriorityBadge', () => {
  it('renders the Critical label for critical priority', () => {
    render(<PriorityBadge priority="critical" />)
    expect(screen.getByText('Critical')).toBeInTheDocument()
  })

  it('renders the Low label for low priority', () => {
    render(<PriorityBadge priority="low" />)
    expect(screen.getByText('Low')).toBeInTheDocument()
  })
})

describe('StatusBadge', () => {
  it('renders human-readable status labels', () => {
    render(<StatusBadge status="in_progress" />)
    expect(screen.getByText('In Progress')).toBeInTheDocument()
  })
})

describe('SlaBadge', () => {
  it('shows "Breached" when the ticket has breached SLA', () => {
    render(<SlaBadge deadline="2020-01-01T00:00:00Z" breached={true} />)
    expect(screen.getByText('Breached')).toBeInTheDocument()
  })

  it('shows time remaining when not breached', () => {
    const future = new Date(Date.now() + 10 * 60 * 60 * 1000).toISOString()
    render(<SlaBadge deadline={future} breached={false} />)
    expect(screen.getByText(/left/)).toBeInTheDocument()
  })
})
