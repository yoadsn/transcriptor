import { type ReactNode } from 'react'

interface ConsentGuardProps {
  children: ReactNode
}

// Consent is now collected inline during auth (AuthScreen).
// This guard is kept as a no-op so old imports don't break during cleanup.
export function ConsentGuard({ children }: ConsentGuardProps) {
  return <>{children}</>
}
