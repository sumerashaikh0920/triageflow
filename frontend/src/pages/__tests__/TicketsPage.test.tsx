import { describe, it, expect } from 'vitest'
import userEvent from '@testing-library/user-event'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '@/test/test-utils'
import { TicketsPage } from '@/pages/TicketsPage'

describe('TicketsPage', () => {
  it('renders the full ticket list by default', () => {
    renderWithProviders(<TicketsPage />)
    expect(screen.getByText('Tickets Inbox')).toBeInTheDocument()
    expect(screen.getByText(/Cannot access my account after password reset/)).toBeInTheDocument()
    expect(screen.getByText(/Double charged on last invoice/)).toBeInTheDocument()
  })

  it('filters tickets by search query', async () => {
    const user = userEvent.setup()
    renderWithProviders(<TicketsPage />)

    const searchInput = screen.getByLabelText('Search tickets')
    await user.type(searchInput, 'Salesforce')

    expect(screen.getByText(/Integration with Salesforce not syncing/)).toBeInTheDocument()
    expect(screen.queryByText(/Double charged on last invoice/)).not.toBeInTheDocument()
  })

  it('shows an empty state when no ticket matches the search', async () => {
    const user = userEvent.setup()
    renderWithProviders(<TicketsPage />)

    const searchInput = screen.getByLabelText('Search tickets')
    await user.type(searchInput, 'this-will-not-match-anything-zzz')

    expect(screen.getByText('No tickets match your filters')).toBeInTheDocument()
  })
})
