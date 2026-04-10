import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api'

const BrandingContext = createContext({
  schoolNaam: 'Kluisjesbeheer',
  schoolSubtitel: '',
  schoolLogo: '/img/logo.png',
  schoolKleur: '#FF8200',
})

export function BrandingProvider({ children }) {
  const [branding, setBranding] = useState(null)

  useEffect(() => {
    function applyColor(hex) {
      const r = parseInt(hex.slice(1, 3), 16)
      const g = parseInt(hex.slice(3, 5), 16)
      const b = parseInt(hex.slice(5, 7), 16)
      // Mix with white for lighter shades, with black for darker
      const mix = (c, target, factor) => Math.round(c + (target - c) * factor)
      const light = (factor) => `${mix(r,255,factor)} ${mix(g,255,factor)} ${mix(b,255,factor)}`
      const dark = (factor) => `${mix(r,0,factor)} ${mix(g,0,factor)} ${mix(b,0,factor)}`
      document.documentElement.style.setProperty('--color-primary', `${r} ${g} ${b}`)
      document.documentElement.style.setProperty('--color-primary-50', light(0.95))
      document.documentElement.style.setProperty('--color-primary-100', light(0.88))
      document.documentElement.style.setProperty('--color-primary-600', dark(0.1))
      document.documentElement.style.setProperty('--color-primary-700', dark(0.25))
    }

    api.get('/api/branding')
      .then(data => {
        setBranding(data)
        if (data.schoolNaam) document.title = `Kluisjesbeheer — ${data.schoolNaam}`
        if (data.schoolKleur) applyColor(data.schoolKleur)
      })
      .catch(() => setBranding({
        schoolNaam: 'Kluisjesbeheer',
        schoolSubtitel: '',
        schoolLogo: '/img/logo.png',
        schoolKleur: '#FF8200',
      }))
  }, [])

  if (!branding) return null

  return (
    <BrandingContext.Provider value={branding}>
      {children}
    </BrandingContext.Provider>
  )
}

export function useBranding() {
  return useContext(BrandingContext)
}
