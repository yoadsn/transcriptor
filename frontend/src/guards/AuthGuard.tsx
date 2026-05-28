import { type ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useSession } from '../contexts/SessionContext'

const DEV_MODE = import.meta.env.VITE_DEV_MODE === 'true'

interface AuthGuardProps {
  children: ReactNode
}

export function AuthGuard({ children }: AuthGuardProps) {
  const { token } = useSession()
  if (!DEV_MODE && !token) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}
