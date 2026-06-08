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

interface SessionContextValue {
  token: string | null
  isAuthenticated: boolean
  consentGiven: boolean
  currentSession: SessionDTO | null
  setToken: (token: string) => void
  clearToken: () => void
  setConsentGiven: (val: boolean) => void
  setCurrentSession: (session: SessionDTO | null) => void
}

const SessionContext = createContext<SessionContextValue | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_KEY)
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
    localStorage.setItem(CONSENT_KEY, 'true')
    setAuthToken(newToken)
    setTokenState(newToken)
    setConsentGivenState(true)
  }, [])

  const clearToken = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(CONSENT_KEY)
    setTokenState(null)
    setConsentGivenState(false)
  }, [])

  const setConsentGiven = useCallback((val: boolean) => {
    localStorage.setItem(CONSENT_KEY, val ? 'true' : 'false')
    setConsentGivenState(val)
  }, [])

  const isAuthenticated = !!token

  return (
    <SessionContext.Provider
      value={{
        token,
        isAuthenticated,
        consentGiven,
        currentSession,
        setToken,
        clearToken,
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
