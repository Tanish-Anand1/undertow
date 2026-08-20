const TOKEN_KEY = 'undertow_token'
const DEVICE_KEY = 'sudo_device'

export function deviceId(): string {
  let id = localStorage.getItem(DEVICE_KEY)
  if (!id || id.length < 8) {
    id = crypto.randomUUID().replace(/-/g, '')
    localStorage.setItem(DEVICE_KEY, id)
  }
  return id
}

export function resetDeviceId() {
  localStorage.removeItem(DEVICE_KEY)
}

const PRODUCTION_API = 'https://undertow-api.vercel.app'

function resolveApiBase() {
  if (typeof window !== 'undefined') {
    const host = window.location.hostname
    if (host === 'localhost' || host === '127.0.0.1') {
      return ''
    }
    if (
      host === 'trysudo.in' ||
      host === 'www.trysudo.in' ||
      host === 'undertow-zeta.vercel.app' ||
      host.endsWith('-tanishs-projects-66633ee2.vercel.app')
    ) {
      return PRODUCTION_API
    }
  }
  const fromEnv = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '')
  if (fromEnv) return fromEnv
  return ''
}

export const API_BASE = resolveApiBase()

function apiUrl(path: string) {
  return `${API_BASE}${path}`
}

export type Post = {
  id: number
  platform: string
  source: string
  title: string
  body: string
  url: string
  author: string
  engagement: number
  posted_at: string | null
  ingested_at: string
  tag: string | null
  relevance_score: number | null
  watchlist_id?: number | null
  keyword?: string | null
}

export type Watchlist = {
  id: number
  keyword: string
  platforms: string[]
  active: boolean
  created_at: string
}

export type Digest = {
  hours: number
  total: number
  by_tag: { tag: string; count: number; posts: Post[] }[]
}

export type Stats = {
  posts_scanned: number
  high_relevance_hits: number
  replies_drafted: number
  x_circuit_open?: boolean
}

export type Me = {
  id: number
  email: string
  name: string | null
  email_verified: boolean
  is_guest: boolean
  guest_scans_used: number
}

export const GUEST_SCAN_LIMIT = 2

function authHeaders(): HeadersInit {
  const token = localStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const parts = detail.map((item) => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object' && 'msg' in item) return String((item as { msg: string }).msg)
      return ''
    })
    const joined = parts.filter(Boolean).join('. ')
    if (joined) return joined
  }
  return fallback
}

function unreachableApiMessage() {
  return API_BASE
    ? `Cannot reach the API at ${API_BASE}. The backend is not live yet.`
    : 'Cannot reach the API. Start the backend on port 8000.'
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = {
    ...(init.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
    ...authHeaders(),
    ...(init.headers || {}),
  }
  let res: Response
  try {
    res = await fetch(apiUrl(path), { ...init, headers })
  } catch {
    throw new Error(unreachableApiMessage())
  }
  if (!res.ok) {
    const text = await res.text()
    try {
      const parsed = JSON.parse(text) as { detail?: unknown }
      throw new Error(formatApiError(parsed.detail, text || res.statusText))
    } catch (err) {
      if (err instanceof SyntaxError) throw new Error(text || res.statusText)
      throw err
    }
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

export const api = {
  token: () => localStorage.getItem(TOKEN_KEY),
  setToken: (t: string | null) => {
    if (t) localStorage.setItem(TOKEN_KEY, t)
    else localStorage.removeItem(TOKEN_KEY)
  },
  register: (email: string, password: string) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify({ email, password }) }),
  guestStart: async () => {
    const data = await request<{ access_token: string }>('/auth/guest/start', { method: 'POST' })
    api.setToken(data.access_token)
    return data
  },
  upgrade: async (name: string, email: string, password: string) => {
    return request<{ id: number; email: string; is_guest: boolean }>('/auth/upgrade', {
      method: 'POST',
      body: JSON.stringify({ name, email, password })
    })
  },
  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password })
    let res: Response
    try {
      res = await fetch(apiUrl('/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      })
    } catch {
      throw new Error(unreachableApiMessage())
    }
    if (!res.ok) {
      const text = await res.text()
      try {
        const parsed = JSON.parse(text) as { detail?: unknown }
        throw new Error(formatApiError(parsed.detail, text || res.statusText))
      } catch (err) {
        if (err instanceof SyntaxError) throw new Error(text || res.statusText)
        throw err
      }
    }
    const data = (await res.json()) as { access_token: string }
    api.setToken(data.access_token)
    return data
  },
  me: () => request<Me>('/auth/me'),
  watchlists: () => request<Watchlist[]>('/watchlists'),
  createWatchlist: (keyword: string, platforms: string[]) =>
    request<Watchlist>('/watchlists', {
      method: 'POST',
      body: JSON.stringify({ keyword, platforms }),
    }),
  deleteWatchlist: (id: number) => request<void>(`/watchlists/${id}`, { method: 'DELETE' }),
  feed: (params: { platform?: string; tag?: string; limit?: number } = {}) => {
    const q = new URLSearchParams()
    if (params.platform) q.set('platform', params.platform)
    if (params.tag) q.set('tag', params.tag)
    if (params.limit) q.set('limit', String(params.limit))
    const qs = q.toString()
    return request<Post[]>(`/feed${qs ? `?${qs}` : ''}`)
  },
  digest: (hours = 24) => request<Digest>(`/digest?hours=${hours}`),
  stats: () => request<Stats>('/stats'),
  ingest: async () => {
    const scan = await request<{
      id: number
      status: string
      total_jobs: number
      finished_jobs: number
      error?: string | null
    }>('/ingest/run', { method: 'POST' })
    const terminal = new Set(['done', 'partial', 'error'])
    let current = scan
    for (let i = 0; i < 40 && !terminal.has(current.status); i += 1) {
      await new Promise((r) => setTimeout(r, 1000))
      current = await request(`/ingest/${scan.id}`)
    }
    return current as unknown as Record<string, number>
  },
  draftReply: (id: number) =>
    request<{ post_id: number; draft: string }>(`/posts/${id}/draft-reply`, { method: 'POST' }),
}

const ADMIN_KEY = 'undertow_admin'

export type AdminUser = {
  id: number
  email: string
  created_at: string
  last_scan_at: string | null
  google: boolean
  keywords: { keyword: string; platforms: string[]; active: boolean }[]
}

export const adminApi = {
  token: () => sessionStorage.getItem(ADMIN_KEY),
  clear: () => sessionStorage.removeItem(ADMIN_KEY),
  unlock: async (password: string) => {
    let res: Response
    try {
      res = await fetch(apiUrl('/admin/unlock'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
    } catch {
      throw new Error(unreachableApiMessage())
    }
    if (!res.ok) {
      const text = await res.text()
      try {
        const parsed = JSON.parse(text) as { detail?: unknown }
        throw new Error(formatApiError(parsed.detail, text || res.statusText))
      } catch (err) {
        if (err instanceof SyntaxError) throw new Error(text || res.statusText)
        throw err
      }
    }
    const data = (await res.json()) as { access_token: string }
    sessionStorage.setItem(ADMIN_KEY, data.access_token)
    return data
  },
  overview: async () => {
    const token = sessionStorage.getItem(ADMIN_KEY)
    if (!token) throw new Error('Locked')
    let res: Response
    try {
      res = await fetch(apiUrl('/admin/overview'), {
        headers: { Authorization: `Bearer ${token}` },
      })
    } catch {
      throw new Error(unreachableApiMessage())
    }
    if (res.status === 401) {
      sessionStorage.removeItem(ADMIN_KEY)
      throw new Error('Session expired')
    }
    if (!res.ok) {
      const text = await res.text()
      throw new Error(text || res.statusText)
    }
    return res.json() as Promise<{
      user_count: number
      unique_visitors: number
      page_views: number
      cta_clicks: number
      users: AdminUser[]
    }>
  },
}
