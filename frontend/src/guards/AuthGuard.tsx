import { type ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'

interface AuthGuardProps {
  children: ReactNode
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated } = useSession()
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />
  }
  return <>{children}</>
}
