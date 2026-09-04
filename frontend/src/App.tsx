import type { ReactNode } from "react"
import { Navigate, Route, Routes } from "react-router-dom"
import { useAuth } from "./lib/auth.tsx"
import Layout from "./components/Layout.tsx"
import Login from "./pages/Login.tsx"
import Dashboard from "./pages/Dashboard.tsx"
import Inbox from "./pages/Inbox.tsx"
import Reply from "./pages/Reply.tsx"
import Progress from "./pages/Progress.tsx"
import Resume from "./pages/Resume.tsx"
import History from "./pages/History.tsx"

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { session, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-base text-white">
        Loading...
      </div>
    )
  }

  if (!session) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="inbox" element={<Inbox />} />
        <Route path="reply" element={<Reply />} />
        <Route path="progress" element={<Progress />} />
        <Route path="resume" element={<Resume />} />
        <Route path="history" element={<History />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
