import { describe, it, expect } from 'vitest'
import userEvent from '@testing-library/user-event'
import { Routes, Route } from 'react-router-dom'
import { screen } from '@testing-library/react'
import { renderWithProviders } from '@/test/test-utils'
import { LoginPage } from '@/pages/LoginPage'

function DummyOverview() {
  return <div>Overview page content</div>
}

describe('LoginPage workflow', () => {
  it('lets a user pick a demo role and navigates away from login', async () => {
    const user = userEvent.setup()

    renderWithProviders(
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<DummyOverview />} />
      </Routes>,
      { initialEntries: ['/login'] },
    )

    expect(screen.getByText('TriageFlow')).toBeInTheDocument()
    expect(screen.getByText('Demo login — choose a role')).toBeInTheDocument()

    await user.click(screen.getByText('Team Lead'))

    expect(await screen.findByText('Overview page content')).toBeInTheDocument()
  })
})
