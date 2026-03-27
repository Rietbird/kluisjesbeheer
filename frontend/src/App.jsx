import { useState } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import { InstellingenProvider } from './context/InstellingenContext'
import TopNav from './components/TopNav'
import Uitleenoverzicht from './pages/Uitleenoverzicht'
import Beheer from './pages/Beheer'

export default function App() {
  const [beheerOpen, setBeheerOpen] = useState(false)

  return (
    <BrowserRouter>
      <AuthProvider>
        <InstellingenProvider>
          <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-950 dark:text-white">
            <TopNav onOpenBeheer={() => setBeheerOpen(true)} />
            {beheerOpen
              ? <Beheer onClose={() => setBeheerOpen(false)} />
              : <Uitleenoverzicht />
            }
          </div>
        </InstellingenProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
