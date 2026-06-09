import { type ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'

interface AuthGuardProps {
  children: ReactNode
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useSession()
  if (isLoading) return null
  if (!isAuthenticated) return <Navigate to="/auth" replace />
  return <>{children}</>
}
