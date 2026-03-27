import { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api'

const InstellingenContext = createContext({ borgActief: true, setBorgActief: () => {} })

export function InstellingenProvider({ children }) {
  const [borgActief, setBorgActiefState] = useState(true)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    api.get('/api/instellingen')
      .then(data => {
        setBorgActiefState(data.borg_actief !== 'false')
      })
      .catch(() => {})
      .finally(() => setLoaded(true))
  }, [])

  async function setBorgActief(val) {
    setBorgActiefState(val)
    await api.put('/api/instellingen', { borg_actief: val ? 'true' : 'false' })
  }

  if (!loaded) return null

  return (
    <InstellingenContext.Provider value={{ borgActief, setBorgActief }}>
      {children}
    </InstellingenContext.Provider>
  )
}

export function useInstellingen() {
  return useContext(InstellingenContext)
}
