import { type ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'

const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true'

interface ConsentGuardProps {
  children: ReactNode
}

export function ConsentGuard({ children }: ConsentGuardProps) {
  const { consentGiven } = useSession()
  if (!DEV_MODE && !consentGiven) {
    return <Navigate to="/consent" replace />
  }
  return <>{children}</>
}
