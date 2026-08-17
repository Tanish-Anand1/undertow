import { BrowserRouter } from 'react-router-dom'
import { AppRoutes } from './AppRoutes'
import { Analytics } from '@vercel/analytics/react'

export default function App() {
  return (
    <>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
      <Analytics />
    </>
  )
}
