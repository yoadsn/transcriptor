import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { SessionProvider } from './contexts/SessionContext'
import { AuthGuard } from './guards/AuthGuard'
import { ConsentGuard } from './guards/ConsentGuard'
import { ErrorBoundary } from './components/ErrorBoundary'
import { LoginScreen } from './screens/LoginScreen'
import { ConsentScreen } from './screens/ConsentScreen'
import { WorkScreen } from './screens/WorkScreen'
import { DoneScreen } from './screens/DoneScreen'
import { MeScreen } from './screens/MeScreen'

export default function App() {
  return (
    <ErrorBoundary>
      <SessionProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginScreen />} />

            <Route
              path="/consent"
              element={
                <AuthGuard>
                  <ConsentScreen />
                </AuthGuard>
              }
            />

            <Route
              path="/work"
              element={
                <AuthGuard>
                  <ConsentGuard>
                    <WorkScreen />
                  </ConsentGuard>
                </AuthGuard>
              }
            />

            <Route
              path="/done"
              element={
                <AuthGuard>
                  <ConsentGuard>
                    <DoneScreen />
                  </ConsentGuard>
                </AuthGuard>
              }
            />

            <Route
              path="/me"
              element={
                <AuthGuard>
                  <ConsentGuard>
                    <MeScreen />
                  </ConsentGuard>
                </AuthGuard>
              }
            />

            <Route path="*" element={<Navigate to="/work" replace />} />
          </Routes>
        </BrowserRouter>
      </SessionProvider>
    </ErrorBoundary>
  )
}
