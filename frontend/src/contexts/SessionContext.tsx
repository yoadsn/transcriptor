import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react'
import { setAuthToken } from '../api'
import type { SessionDTO } from '../types'

const TOKEN_KEY = 'auth_token'
const CONSENT_KEY = 'consent_given'
const GUEST_KEY = 'is_guest'

interface SessionContextValue {
  token: string | null
  isGuest: boolean
  isAuthenticated: boolean
  consentGiven: boolean
  currentSession: SessionDTO | null
  setToken: (token: string) => void
  clearToken: () => void
  guestLogin: () => void
  setConsentGiven: (val: boolean) => void
  setCurrentSession: (session: SessionDTO | null) => void
}

const SessionContext = createContext<SessionContextValue | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_KEY)
  )
  const [isGuest, setIsGuestState] = useState<boolean>(() =>
    localStorage.getItem(GUEST_KEY) === 'true'
  )
  const [consentGiven, setConsentGivenState] = useState<boolean>(() =>
    localStorage.getItem(CONSENT_KEY) === 'true'
  )
  const [currentSession, setCurrentSession] = useState<SessionDTO | null>(null)

  useEffect(() => {
    if (token) setAuthToken(token)
  }, [token])

  const setToken = useCallback((newToken: string) => {
    localStorage.setItem(TOKEN_KEY, newToken)
    localStorage.removeItem(GUEST_KEY)
    localStorage.setItem(CONSENT_KEY, 'true')
    setAuthToken(newToken)
    setTokenState(newToken)
    setIsGuestState(false)
    setConsentGivenState(true)
  }, [])

  const clearToken = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(GUEST_KEY)
    localStorage.removeItem(CONSENT_KEY)
    setTokenState(null)
    setIsGuestState(false)
    setConsentGivenState(false)
  }, [])

  // Debug-only guest login: no token, no backend auth.
  // Remove this when real auth is wired up.
  const guestLogin = useCallback(() => {
    localStorage.setItem(GUEST_KEY, 'true')
    localStorage.setItem(CONSENT_KEY, 'true')
    setIsGuestState(true)
    setConsentGivenState(true)
  }, [])

  const setConsentGiven = useCallback((val: boolean) => {
    localStorage.setItem(CONSENT_KEY, val ? 'true' : 'false')
    setConsentGivenState(val)
  }, [])

  const isAuthenticated = !!token || isGuest

  return (
    <SessionContext.Provider
      value={{
        token,
        isGuest,
        isAuthenticated,
        consentGiven,
        currentSession,
        setToken,
        clearToken,
        guestLogin,
        setConsentGiven,
        setCurrentSession,
      }}
    >
      {children}
    </SessionContext.Provider>
  )
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used within SessionProvider')
  return ctx
}
