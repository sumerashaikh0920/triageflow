import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ReactNode } from 'react'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import { ThemeProvider } from '@/context/ThemeContext'
import { ToastProvider } from '@/context/ToastContext'
import { TicketsProvider } from '@/context/TicketsContext'
import { NotificationsProvider } from '@/context/NotificationsContext'
import { Layout } from '@/components/layout/Layout'
import { LoginPage } from '@/pages/LoginPage'
import { OverviewPage } from '@/pages/OverviewPage'
import { TicketsPage } from '@/pages/TicketsPage'
import { RoutingQueuePage } from '@/pages/RoutingQueuePage'
import { SLAMonitorPage } from '@/pages/SLAMonitorPage'
import { FeedbackRetrainingPage } from '@/pages/FeedbackRetrainingPage'
import { ModelMetricsPage } from '@/pages/ModelMetricsPage'
import { IntegrationsPage } from '@/pages/IntegrationsPage'
import { TeamRolesPage } from '@/pages/TeamRolesPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

function RequireAuth({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function RequireRole({ roles, children }: { roles: Array<'agent' | 'team_lead' | 'admin'>; children: ReactNode }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (!roles.includes(user.role)) return <Navigate to="/" replace />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<OverviewPage />} />
        <Route path="/tickets" element={<TicketsPage />} />
        <Route path="/routing" element={<RoutingQueuePage />} />
        <Route path="/sla" element={<SLAMonitorPage />} />
        <Route path="/feedback" element={<FeedbackRetrainingPage />} />
        <Route path="/models" element={<ModelMetricsPage />} />
        <Route
          path="/integrations"
          element={
            <RequireRole roles={['team_lead', 'admin']}>
              <IntegrationsPage />
            </RequireRole>
          }
        />
        <Route
          path="/team"
          element={
            <RequireRole roles={['team_lead', 'admin']}>
              <TeamRolesPage />
            </RequireRole>
          }
        />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <NotificationsProvider>
            <TicketsProvider>
              <BrowserRouter>
                <AppRoutes />
              </BrowserRouter>
            </TicketsProvider>
          </NotificationsProvider>
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}
