import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useDarkMode } from '../hooks/useDarkMode'
import { useBranding } from '../context/BrandingContext'

function UserPhoto({ user }) {
  const [hasPhoto, setHasPhoto] = useState(true)
  const initial = (user?.displayName || '?')[0].toUpperCase()

  if (hasPhoto) {
    return (
      <img
        src="/auth/photo"
        alt=""
        className="w-9 h-9 rounded-full object-cover border-2 border-white/30"
        onError={() => setHasPhoto(false)}
      />
    )
  }
  return (
    <div className="w-9 h-9 bg-primary-700 rounded-full flex items-center justify-center text-sm font-bold text-white border-2 border-white/30">
      {initial}
    </div>
  )
}

export default function TopNav({ onOpenBeheer, onOpenHandleiding, onGoHome }) {
  const user = useAuth()
  const [dark, setDark] = useDarkMode()
  const { schoolNaam, schoolSubtitel, schoolLogo } = useBranding()

  return (
    <header className="bg-gradient-to-r from-white via-primary-50 to-primary-100 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800 border-b border-primary-100 dark:border-slate-700 shadow-sm">
      <div className="flex items-center justify-between px-5 py-2">
        <button onClick={onGoHome}
          className="flex items-center gap-3 group cursor-pointer text-left"
          title="Naar overzicht">
          <img src={schoolLogo} alt={schoolNaam} className="h-9 w-auto rounded-none"
            onError={e => { e.target.onerror = null; e.target.src = '/img/logo-placeholder.svg' }} />
          <div>
            <div className="font-bold text-lg text-navy dark:text-white leading-tight group-hover:text-primary transition-colors">Kluisjesbeheer</div>
            {(schoolSubtitel || schoolNaam) && <div className="text-[10px] text-primary-700 dark:text-primary font-medium leading-tight">{schoolSubtitel || schoolNaam}</div>}
          </div>
        </button>
        <div className="flex items-center gap-3">
          {/* Dark mode toggle */}
          <button onClick={() => setDark(!dark)}
            className="flex items-center gap-1.5 bg-amber-200 dark:bg-indigo-900 rounded-full p-0.5 w-14 h-7 relative transition-colors"
            title={dark ? 'Lichte modus' : 'Donkere modus'}>
            <span className={`absolute w-6 h-6 rounded-full bg-white dark:bg-slate-800 shadow-md flex items-center justify-center transition-all duration-200 ${dark ? 'translate-x-7' : 'translate-x-0'}`}>
              {dark ? (
                <svg className="w-3.5 h-3.5 text-blue-300" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                </svg>
              ) : (
                <svg className="w-3.5 h-3.5 text-amber-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                </svg>
              )}
            </span>
          </button>

          {/* Handleiding — discrete ? knop, naast instellingen */}
          <button onClick={onOpenHandleiding}
            className="w-7 h-7 flex items-center justify-center rounded-full border border-slate-300 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:text-primary hover:border-primary dark:hover:text-primary transition-colors text-sm font-semibold"
            title="Handleiding">
            ?
          </button>

          {/* Beheer tandwiel — alleen voor beheerders */}
          {user?.is_beheerder && (
            <button onClick={onOpenBeheer}
              className="p-2 rounded-lg hover:bg-primary-50 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 hover:text-primary dark:hover:text-primary transition-colors"
              title="Beheer">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          )}

          {/* User info */}
          <div className="hidden sm:flex items-center gap-2.5 bg-white/60 dark:bg-slate-700/60 backdrop-blur rounded-xl px-3 py-1.5 border border-primary-100 dark:border-slate-600">
            <UserPhoto user={user} />
            <div>
              <div className="text-sm font-semibold text-navy dark:text-white leading-tight">{user?.displayName}</div>
              <a href="/auth/logout" className="text-[11px] text-primary-700 dark:text-primary hover:text-primary transition-colors">Uitloggen</a>
            </div>
          </div>
          <a href="/auth/logout" className="sm:hidden text-xs text-primary-700 dark:text-primary hover:text-primary">Uitloggen</a>
        </div>
      </div>
    </header>
  )
}
