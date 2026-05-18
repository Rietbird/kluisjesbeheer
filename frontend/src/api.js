const BASE = ''

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', ...options.headers },
    ...options,
  })
  if (res.status === 401) {
    window.location.href = '/auth/login'
    throw new Error('Niet ingelogd')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.error || `HTTP ${res.status}`)
  }
  return res.json()
}

// Dedup concurrent GET requests to the same path (e.g. /api/vestigingen loaded by multiple components)
const _inflight = {}
function deduped(path) {
  if (!_inflight[path]) {
    _inflight[path] = apiFetch(path).finally(() => { delete _inflight[path] })
  }
  return _inflight[path].then(data => structuredClone(data))
}

export const api = {
  get: (path) => deduped(path),
  post: (path, body) => apiFetch(path, { method: 'POST', body: JSON.stringify(body) }),
  put: (path, body) => apiFetch(path, { method: 'PUT', body: JSON.stringify(body) }),
  patch: (path, body) => apiFetch(path, { method: 'PATCH', body: JSON.stringify(body) }),
  del: (path) => apiFetch(path, { method: 'DELETE' }),
  upload: (path, formData) => fetch(path, { method: 'POST', body: formData, headers: { 'X-Requested-With': 'XMLHttpRequest' } }).then(async r => {
    if (r.status === 401) { window.location.href = '/auth/login'; throw new Error('Niet ingelogd') }
    if (!r.ok) {
      const err = await r.json().catch(() => ({}))
      throw new Error(err.error || `HTTP ${r.status}`)
    }
    return r.json()
  }),
}
