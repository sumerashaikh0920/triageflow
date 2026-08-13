import { describe, it, expect } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '@/test/test-utils'
import { TicketDetailDrawer } from '@/components/tickets/TicketDetailDrawer'
import { mockTickets } from '@/lib/mock-data'

describe('TicketDetailDrawer — Accept AI prediction workflow', () => {
  it('accepts the AI prediction and shows a confirmation toast', async () => {
    const user = userEvent.setup()
    const ticket = mockTickets.find(t => t.id === 'TKT-1040')!

    renderWithProviders(
      <TicketDetailDrawer ticket={ticket} open={true} onOpenChange={() => {}} />,
    )

    await user.click(screen.getByRole('tab', { name: /AI & Routing/i }))

    const acceptButton = await screen.findByRole('button', { name: 'Accept AI prediction' })
    await user.click(acceptButton)

    expect(await screen.findByText('AI prediction accepted')).toBeInTheDocument()
    expect(acceptButton).toBeDisabled()
  })

  it('marks urgency and shows a confirmation toast', async () => {
    const user = userEvent.setup()
    const ticket = mockTickets.find(t => t.id === 'TKT-1038')!

    renderWithProviders(
      <TicketDetailDrawer ticket={ticket} open={true} onOpenChange={() => {}} />,
    )

    await user.click(screen.getByRole('button', { name: 'Critical' }))

    expect(await screen.findByText('Urgency updated')).toBeInTheDocument()
  })
})
