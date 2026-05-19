import { useState } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './hooks/useAuth'
import { InstellingenProvider } from './context/InstellingenContext'
import { BrandingProvider } from './context/BrandingContext'
import TopNav from './components/TopNav'
import Uitleenoverzicht from './pages/Uitleenoverzicht'
import Beheer from './pages/Beheer'
import Handleiding from './pages/Handleiding'

export default function App() {
  const [beheerOpen, setBeheerOpen] = useState(false)
  const [handleidingOpen, setHandleidingOpen] = useState(false)

  return (
    <BrowserRouter>
      <BrandingProvider>
      <AuthProvider>
        <InstellingenProvider>
          <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-950 dark:text-white">
            <TopNav
              onOpenBeheer={() => { setHandleidingOpen(false); setBeheerOpen(true) }}
              onOpenHandleiding={() => { setBeheerOpen(false); setHandleidingOpen(true) }}
            />
            {handleidingOpen
              ? <Handleiding onClose={() => setHandleidingOpen(false)} />
              : beheerOpen
                ? <Beheer onClose={() => setBeheerOpen(false)} />
                : <Uitleenoverzicht />
            }
          </div>
        </InstellingenProvider>
      </AuthProvider>
      </BrandingProvider>
    </BrowserRouter>
  )
}
