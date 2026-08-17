import { lazy, Suspense, useEffect } from 'react'
import { Route, Routes } from 'react-router-dom'

const Dashboard = lazy(() => import('./Dashboard'))
const Admin = lazy(() => import('./Admin'))
const NotFound = lazy(() => import('./NotFound'))

function RedirectHome() {
  useEffect(() => {
    window.location.replace('/')
  }, [])
  return null
}

export function AppRoutes() {
  return (
    <Suspense fallback={null}>
      <Routes>
        <Route path="/" element={<RedirectHome />} />
        <Route path="/app" element={<Dashboard />} />
        <Route path="/ledger" element={<Admin />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}
