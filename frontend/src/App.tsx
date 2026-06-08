import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { SessionProvider } from './contexts/SessionContext'
import { AuthGuard } from './guards/AuthGuard'
import { ErrorBoundary } from './components/ErrorBoundary'
import { LandingScreen } from './screens/LandingScreen'
import { AuthScreen } from './screens/AuthScreen'
import { GuidelinesScreen } from './screens/GuidelinesScreen'
import { WorkScreen } from './screens/WorkScreen'
import { AllCaughtUpScreen } from './screens/AllCaughtUpScreen'
import { ProgressScreen } from './screens/ProgressScreen'

export default function App() {
  return (
    <ErrorBoundary>
      <SessionProvider>
        <BrowserRouter>
          <Routes>
            {/* Public */}
            <Route path="/" element={<LandingScreen />} />
            <Route path="/auth" element={<AuthScreen />} />
            {/* /login kept as alias for old OAuth redirect */}
            <Route path="/login" element={<AuthScreen />} />
            <Route path="/guidelines" element={<GuidelinesScreen />} />

            {/* Protected */}
            <Route path="/work" element={<AuthGuard><WorkScreen /></AuthGuard>} />
            <Route path="/done" element={<AuthGuard><AllCaughtUpScreen /></AuthGuard>} />
            <Route path="/me" element={<AuthGuard><ProgressScreen /></AuthGuard>} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </SessionProvider>
    </ErrorBoundary>
  )
}
