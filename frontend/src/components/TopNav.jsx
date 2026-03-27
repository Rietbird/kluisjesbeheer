import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useDarkMode } from '../hooks/useDarkMode'

const links = [
  { to: '/', label: 'Overzicht' },
  { to: '/beheer', label: 'Beheer' },
]

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
    <div className="w-9 h-9 bg-School-700 rounded-full flex items-center justify-center text-sm font-bold text-white border-2 border-white/30">
      {initial}
    </div>
  )
}

export default function TopNav() {
  const user = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const [dark, setDark] = useDarkMode()

  const linkClass = ({ isActive }) =>
    `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-School text-white shadow-sm'
        : 'text-School-700 hover:text-School hover:bg-School-50'
    }`

  const mobileLinkClass = ({ isActive }) =>
    `px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-School text-white'
        : 'text-School-700 hover:bg-School-50'
    }`

  return (
    <header className="bg-gradient-to-r from-white via-School-50 to-School-100 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800 border-b border-School-100 dark:border-slate-700 shadow-sm">
      <div className="flex items-center justify-between px-5 py-2">
        <div className="flex items-center gap-6">
          <NavLink to="/" className="flex items-center gap-3">
            <img src="/img/School-logo.png" alt="School" className="w-10 h-10 rounded-none" />
            <div>
              <div className="font-bold text-lg text-navy dark:text-white leading-tight">Kluisjesbeheer</div>
              <div className="text-[10px] text-School-700 dark:text-School font-medium leading-tight">School</div>
            </div>
          </NavLink>
          <nav className="hidden md:flex gap-1">
            {links.map(l => (
              <NavLink key={l.to} to={l.to} end={l.to === '/'} className={linkClass}>{l.label}</NavLink>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          {/* Dark mode toggle switch */}
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
          <div className="hidden sm:flex items-center gap-2.5 bg-white/60 dark:bg-slate-700/60 backdrop-blur rounded-xl px-3 py-1.5 border border-School-100 dark:border-slate-600">
            <UserPhoto user={user} />
            <div>
              <div className="text-sm font-semibold text-navy dark:text-white leading-tight">{user?.displayName}</div>
              <a href="/auth/logout" className="text-[11px] text-School-700 dark:text-School hover:text-School transition-colors">Uitloggen</a>
            </div>
          </div>
          <a href="/auth/logout" className="sm:hidden text-xs text-School-700 dark:text-School hover:text-School">Uitloggen</a>
          <button className="md:hidden p-2 rounded-lg hover:bg-School-50 dark:hover:bg-slate-700 text-School-700 dark:text-School transition-colors" onClick={() => setMenuOpen(!menuOpen)}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d={menuOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'} />
            </svg>
          </button>
        </div>
      </div>
      {menuOpen && (
        <nav className="md:hidden px-4 pb-3 flex flex-col gap-1 border-t border-School-100 pt-2 bg-white/50">
          {links.map(l => (
            <NavLink key={l.to} to={l.to} end={l.to === '/'} className={mobileLinkClass}
              onClick={() => setMenuOpen(false)}>{l.label}</NavLink>
          ))}
        </nav>
      )}
    </header>
  )
}
