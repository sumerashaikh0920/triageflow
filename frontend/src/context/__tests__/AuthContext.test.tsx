import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { AuthProvider, useAuth } from '@/context/AuthContext'

describe('AuthContext', () => {
  it('starts logged out', () => {
    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })
    expect(result.current.user).toBeNull()
  })

  it('logs in as the requested demo role', () => {
    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })

    act(() => result.current.login('admin'))

    expect(result.current.user?.role).toBe('admin')
    expect(result.current.user?.name).toBe('Priya Nair')
  })

  it('logs out and clears the user', () => {
    const { result } = renderHook(() => useAuth(), { wrapper: AuthProvider })

    act(() => result.current.login('agent'))
    expect(result.current.user).not.toBeNull()

    act(() => result.current.logout())
    expect(result.current.user).toBeNull()
  })
})
