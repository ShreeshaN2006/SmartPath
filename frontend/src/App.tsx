import { Routes, Route } from 'react-router-dom'
import { ToastProvider } from './components/ui/Toast'
import { LandingPage } from './pages/LandingPage'
import { PlannerPage } from './pages/PlannerPage'

function App() {
  return (
    <ToastProvider>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/planner" element={<PlannerPage />} />
      </Routes>
    </ToastProvider>
  )
}

export default App