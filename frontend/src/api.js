const BASE = ''

export async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
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

export const api = {
  get: (path) => apiFetch(path),
  post: (path, body) => apiFetch(path, { method: 'POST', body: JSON.stringify(body) }),
  put: (path, body) => apiFetch(path, { method: 'PUT', body: JSON.stringify(body) }),
  del: (path) => apiFetch(path, { method: 'DELETE' }),
  upload: (path, formData) => fetch(path, { method: 'POST', body: formData }).then(async r => {
    if (r.status === 401) { window.location.href = '/auth/login'; throw new Error('Niet ingelogd') }
    if (!r.ok) {
      const err = await r.json().catch(() => ({}))
      throw new Error(err.error || `HTTP ${r.status}`)
    }
    return r.json()
  }),
}
