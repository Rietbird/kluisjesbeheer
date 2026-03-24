import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import TopNav from './components/TopNav'
import Dashboard from './pages/Dashboard'
import Uitleenoverzicht from './pages/Uitleenoverzicht'
import Beheer from './pages/Beheer'
import Instellingen from './pages/Instellingen'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-slate-50">
          <TopNav />
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/uitleenoverzicht" element={<Uitleenoverzicht />} />
            <Route path="/beheer" element={<Beheer />} />
            <Route path="/instellingen" element={<Instellingen />} />
          </Routes>
        </div>
      </AuthProvider>
    </BrowserRouter>
  )
}
