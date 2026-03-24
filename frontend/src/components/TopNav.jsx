import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/uitleenoverzicht', label: 'Uitleenoverzicht' },
  { to: '/beheer', label: 'Beheer' },
  { to: '/instellingen', label: 'Instellingen' },
]

export default function TopNav() {
  const user = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)

  const linkClass = ({ isActive }) =>
    `px-3 py-1 rounded text-sm ${isActive ? 'bg-white/15' : 'opacity-70 hover:opacity-100'}`

  return (
    <header className="bg-navy text-white">
      <div className="flex items-center justify-between px-4 py-2">
        <div className="flex items-center gap-4">
          <span className="text-blue-400 font-bold text-lg">Kluisjes</span>
          {/* Desktop nav */}
          <nav className="hidden md:flex gap-1">
            {links.map(l => (
              <NavLink key={l.to} to={l.to} end={l.to === '/'} className={linkClass}>{l.label}</NavLink>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs opacity-70 hidden sm:inline">{user?.displayName}</span>
          <a href="/auth/logout" className="text-xs opacity-50 hover:opacity-100">Uitloggen</a>
          {/* Hamburger */}
          <button className="md:hidden p-1" onClick={() => setMenuOpen(!menuOpen)}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d={menuOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'} />
            </svg>
          </button>
        </div>
      </div>
      {/* Mobile menu */}
      {menuOpen && (
        <nav className="md:hidden px-4 pb-3 flex flex-col gap-1">
          {links.map(l => (
            <NavLink key={l.to} to={l.to} end={l.to === '/'} className={linkClass}
              onClick={() => setMenuOpen(false)}>{l.label}</NavLink>
          ))}
        </nav>
      )}
    </header>
  )
}
