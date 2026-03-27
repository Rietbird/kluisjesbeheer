import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../api'

const InstellingenContext = createContext({})

export function InstellingenProvider({ children }) {
  const [borgMap, setBorgMap] = useState({})
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    api.get('/api/vestigingen')
      .then(vestigingen => {
        const map = {}
        vestigingen.forEach(v => { map[v.id] = v.borg_actief !== 0 && v.borg_actief !== false })
        setBorgMap(map)
      })
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [])

  const borgActiefVoor = useCallback((vestigingId) => {
    if (!vestigingId) return true
    const val = borgMap[Number(vestigingId)]
    return val === undefined ? true : val
  }, [borgMap])

  async function setBorgActiefVoor(vestigingId, val) {
    const prev = { ...borgMap }
    setBorgMap(m => ({ ...m, [vestigingId]: val }))
    try {
      await api.put(`/api/vestigingen/${vestigingId}/borg`, { borg_actief: val })
    } catch {
      setBorgMap(prev)
    }
  }

  if (!loaded) return null

  return (
    <InstellingenContext.Provider value={{ borgActiefVoor, setBorgActiefVoor, borgMap }}>
      {children}
    </InstellingenContext.Provider>
  )
}

export function useInstellingen() {
  return useContext(InstellingenContext)
}
