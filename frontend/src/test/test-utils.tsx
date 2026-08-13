import { ReactElement, ReactNode } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { ThemeProvider } from '@/context/ThemeContext'
import { ToastProvider } from '@/context/ToastContext'
import { TicketsProvider } from '@/context/TicketsContext'
import { NotificationsProvider } from '@/context/NotificationsContext'

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

export * from '@testing-library/react'
