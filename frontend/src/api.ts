const TOKEN_KEY = 'undertow_token'
export const API_BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || ''

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
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = {
    ...(init.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
    ...authHeaders(),
    ...(init.headers || {}),
  }
  const res = await fetch(apiUrl(path), { ...init, headers })
  if (!res.ok) {
    const text = await res.text()
    try {
      const parsed = JSON.parse(text) as { detail?: string }
      throw new Error(parsed.detail || text || res.statusText)
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
  login: async (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password })
    const res = await fetch(apiUrl('/auth/login'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body,
    })
    if (!res.ok) throw new Error(await res.text())
    const data = (await res.json()) as { access_token: string }
    api.setToken(data.access_token)
    return data
  },
  me: () => request<{ id: number; email: string }>('/auth/me'),
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
    for (let i = 0; i < 90 && !terminal.has(current.status); i += 1) {
      await new Promise((r) => setTimeout(r, 2000))
      current = await request(`/ingest/${scan.id}`)
    }
    return current as unknown as Record<string, number>
  },
  draftReply: (id: number) =>
    request<{ post_id: number; draft: string }>(`/posts/${id}/draft-reply`, { method: 'POST' }),
}
