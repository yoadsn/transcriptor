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
  consentGiven: boolean
  currentSession: SessionDTO | null
  setToken: (token: string) => void
  clearToken: () => void
  setConsentGiven: (val: boolean) => void
  setCurrentSession: (session: SessionDTO | null) => void
}

const SessionContext = createContext<SessionContextValue | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_KEY)
  })
  const [consentGiven, setConsentGivenState] = useState<boolean>(() => {
    return localStorage.getItem(CONSENT_KEY) === 'true'
  })
  const [currentSession, setCurrentSession] = useState<SessionDTO | null>(null)

  useEffect(() => {
    if (token) {
      setAuthToken(token)
    }
  }, [token])

  const setToken = useCallback((newToken: string) => {
    localStorage.setItem(TOKEN_KEY, newToken)
    setAuthToken(newToken)
    setTokenState(newToken)
  }, [])

  const clearToken = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    setTokenState(null)
  }, [])

  const setConsentGiven = useCallback((val: boolean) => {
    localStorage.setItem(CONSENT_KEY, val ? 'true' : 'false')
    setConsentGivenState(val)
  }, [])

  return (
    <SessionContext.Provider
      value={{
        token,
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
