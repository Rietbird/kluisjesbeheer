import { useState, useEffect, useCallback } from 'react'
import { api } from '../api'

export function useKluisjes() {
  const [vestigingen, setVestigingen] = useState([])
  const [clusters, setClusters] = useState([])
  const [kluisjes, setKluisjes] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    vestiging_id: null, cluster_id: null, status: '', q: '', klas: '', view: 'grid',
  })

  useEffect(() => {
    api.get('/api/vestigingen').then(setVestigingen)
  }, [])

  useEffect(() => {
    if (filters.vestiging_id) {
      api.get(`/api/vestigingen/${filters.vestiging_id}/clusters`).then(setClusters)
    } else {
      setClusters([])
    }
  }, [filters.vestiging_id])

  const loadKluisjes = useCallback(() => {
    if (!filters.vestiging_id) { setKluisjes([]); setLoading(false); return }
    setLoading(true)
    const params = new URLSearchParams()
    params.set('vestiging_id', filters.vestiging_id)
    if (filters.status) params.set('status', filters.status)
    if (filters.q) params.set('q', filters.q)
    if (filters.klas) params.set('klas', filters.klas)
    api.get(`/api/kluisjes?${params}`).then(setKluisjes).finally(() => setLoading(false))
  }, [filters.vestiging_id, filters.status, filters.q, filters.klas])

  useEffect(() => { loadKluisjes() }, [loadKluisjes])

  return { vestigingen, clusters, kluisjes, loading, filters, setFilters, reload: loadKluisjes }
}
