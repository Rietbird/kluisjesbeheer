import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../api'

const InstellingenContext = createContext({})

// Standaard kleuren (Tailwind gradient klassen) per index als fallback
export const VESTIGING_STANDAARD_KLEUREN = [
  '#14b8a6', // teal-500
  '#3b82f6', // blue-500
  '#8b5cf6', // violet-500
  '#FF8200', // school primary
]

export function InstellingenProvider({ children }) {
  const [borgMap, setBorgMap] = useState({})
  const [kleurMap, setKleurMap] = useState({})
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    api.get('/api/vestigingen')
      .then(vestigingen => {
        const bMap = {}
        const kMap = {}
        vestigingen.forEach(v => {
          bMap[v.id] = v.borg_actief !== 0 && v.borg_actief !== false
          if (v.kleur) kMap[v.id] = v.kleur
        })
        setBorgMap(bMap)
        setKleurMap(kMap)
      })
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [])

  const borgActiefVoor = useCallback((vestigingId) => {
    if (!vestigingId) return true
    const val = borgMap[Number(vestigingId)]
    return val === undefined ? true : val
  }, [borgMap])

  const kleurVoor = useCallback((vestigingId, index = 0) => {
    return kleurMap[Number(vestigingId)] || VESTIGING_STANDAARD_KLEUREN[index % VESTIGING_STANDAARD_KLEUREN.length]
  }, [kleurMap])

  async function setBorgActiefVoor(vestigingId, val) {
    const prev = { ...borgMap }
    setBorgMap(m => ({ ...m, [vestigingId]: val }))
    try {
      await api.put(`/api/vestigingen/${vestigingId}/borg`, { borg_actief: val })
    } catch {
      setBorgMap(prev)
    }
  }

  async function setKleurVoor(vestigingId, kleur) {
    const prev = { ...kleurMap }
    setKleurMap(m => ({ ...m, [Number(vestigingId)]: kleur }))
    try {
      await api.put(`/api/vestigingen/${vestigingId}/kleur`, { kleur })
    } catch {
      setKleurMap(prev)
    }
  }

  if (!loaded) return null

  return (
    <InstellingenContext.Provider value={{ borgActiefVoor, setBorgActiefVoor, borgMap, kleurVoor, setKleurVoor, kleurMap }}>
      {children}
    </InstellingenContext.Provider>
  )
}

export function useInstellingen() {
  return useContext(InstellingenContext)
}
