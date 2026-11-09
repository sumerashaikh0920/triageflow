import { ReactElement, ReactNode } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthProvider'
import { ThemeProvider } from '@/context/ThemeProvider'
import { ToastProvider } from '@/context/ToastProvider'
import { TicketsProvider } from '@/context/TicketsProvider'
import { NotificationsProvider } from '@/context/NotificationsProvider'

function makeAllProviders(initialEntries: string[]) {
  return function AllProviders({ children }: { children: ReactNode }) {
    return (
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <NotificationsProvider>
              <TicketsProvider>
                <MemoryRouter initialEntries={initialEntries}>{children}</MemoryRouter>
              </TicketsProvider>
            </NotificationsProvider>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    )
  }
}

export function renderWithProviders(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'> & { initialEntries?: string[] },
) {
  const { initialEntries = ['/'], ...renderOptions } = options ?? {}
  return render(ui, { wrapper: makeAllProviders(initialEntries), ...renderOptions })
}
