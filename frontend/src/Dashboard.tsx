import { Link } from 'react-router-dom'
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { X } from 'lucide-react'
import { api, API_BASE, type Digest, type Post, type Stats, type Watchlist } from './api'
import './landing/Landing.css'
import './Dashboard.css'

const PLATFORMS = [
  { id: '', label: 'All' },
  { id: 'hn', label: 'HN' },
  { id: 'x', label: 'X' },
  { id: 'github', label: 'GitHub' },
  { id: 'reddit', label: 'Reddit' },
] as const

const TAGS = [
  { id: '', label: 'All' },
  { id: 'pain', label: 'Pain' },
  { id: 'question', label: 'Question' },
  { id: 'complaint', label: 'Complaint' },
  { id: 'praise', label: 'Praise' },
] as const

function safeHref(url: string | null | undefined) {
  if (!url) return undefined
  try {
    const parsed = new URL(url)
    if (parsed.protocol === 'http:' || parsed.protocol === 'https:') return url
  } catch {
    return undefined
  }
  return undefined
}

function timeAgo(iso: string | null) {
  if (!iso) return 'now'
  const diff = Date.now() - new Date(iso).getTime()
  const m = Math.floor(diff / 60000)
  if (m < 1) return 'now'
  if (m < 60) return `${m}m`
  const h = Math.floor(m / 60)
  if (h < 48) return `${h}h`
  return `${Math.floor(h / 24)}d`
}

function AuthScreen({ onAuthed }: { onAuthed: () => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const hash = window.location.hash.slice(1)
    const params = new URLSearchParams(hash)
    const token = params.get('google')
    if (params.get('google_error')) {
      setError('Google sign-in was cancelled or failed.')
      window.history.replaceState(null, '', window.location.pathname)
      return
    }
    if (token) {
      api.setToken(token)
      window.history.replaceState(null, '', window.location.pathname)
      onAuthed()
    }
  }, [onAuthed])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (mode === 'register') await api.register(email, password)
      await api.login(email, password)
      onAuthed()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Auth failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="hm chamber">
      <header className="hm-nav">
        <Link className="hm-mark" to="/">
          Undertow
        </Link>
        <nav className="hm-links" aria-label="Primary">
          <Link to="/">Home</Link>
        </nav>
      </header>
      <div className="auth-wrap">
        <form onSubmit={submit} className="auth-form">
          <h1>{mode === 'login' ? 'Enter.' : 'Begin.'}</h1>
          <p>The chamber is private. Same paper, same type. The listening work happens here.</p>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            required
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            minLength={8}
            required
          />
          {error && <p className="auth-err">{error}</p>}
          <button className="hm-cta" disabled={busy} type="submit">
            {busy ? 'Please wait' : mode === 'login' ? 'Enter chamber' : 'Create account'}
          </button>
          <a className="google-auth" href={`${API_BASE}/auth/google/start`}>
            Continue with Google
          </a>
          <button type="button" className="switch" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
            {mode === 'login' ? 'Need an account? Register' : 'Have an account? Enter'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [authed, setAuthed] = useState(!!api.token())
  const [watchlists, setWatchlists] = useState<Watchlist[]>([])
  const [posts, setPosts] = useState<Post[]>([])
  const [digest, setDigest] = useState<Digest | null>(null)
  const [stats, setStats] = useState<Stats | null>(null)
  const [platform, setPlatform] = useState('')
  const [tag, setTag] = useState('')
  const [keyword, setKeyword] = useState('')
  const [scanning, setScanning] = useState(false)
  const [draft, setDraft] = useState<{ id: number; text: string } | null>(null)
  const [error, setError] = useState('')

  const [didPrime, setDidPrime] = useState(false)

  useEffect(() => {
    document.documentElement.classList.add('hm-root')
    return () => document.documentElement.classList.remove('hm-root')
  }, [])

  const livePlatforms = useMemo(() => {
    const set = new Set<string>()
    watchlists.forEach((w) => w.platforms.forEach((p) => set.add(p)))
    return ['hn', 'x', 'github', 'reddit'].map((p) => ({ id: p, on: set.has(p) }))
  }, [watchlists])

  async function refresh() {
    const [w, f, d, s] = await Promise.all([
      api.watchlists(),
      api.feed({ platform: platform || undefined, tag: tag || undefined, limit: 80 }),
      api.digest(24),
      api.stats(),
    ])
    setWatchlists(w)
    setPosts(f)
    setDigest(d)
    setStats(s)
  }

  useEffect(() => {
    if (!authed) return
    refresh()
      .then(() => {
        if (!didPrime) setDidPrime(true)
      })
      .catch((e) => setError(String(e.message || e)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authed, platform, tag])

  useEffect(() => {
    if (!authed || !didPrime || scanning) return
    if (watchlists.length && posts.length === 0) {
      scanNow()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [didPrime, watchlists.length])

  async function addWatchlist(e: FormEvent) {
    e.preventDefault()
    const value = keyword.trim()
    if (!value) return
    if (watchlists.some((w) => w.keyword.toLowerCase() === value.toLowerCase())) {
      setKeyword('')
      return
    }
    setError('')
    setPlatform('')
    try {
      const created = await api.createWatchlist(value, ['hn', 'x', 'github', 'reddit'])
      setWatchlists((prev) => [created, ...prev])
      setKeyword('')
      scanNow()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not add keyword')
    }
  }

  async function removeWatchlist(id: number) {
    setError('')
    const previous = watchlists
    setWatchlists((prev) => prev.filter((w) => w.id !== id))
    try {
      await api.deleteWatchlist(id)
      await refresh()
    } catch (err) {
      setWatchlists(previous)
      setError(err instanceof Error ? err.message : 'Could not remove keyword')
    }
  }

  async function scanNow() {
    setScanning(true)
    setError('')
    try {
      await api.ingest()
      await refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed')
    } finally {
      setScanning(false)
    }
  }

  async function onDraft(id: number) {
    setDraft({ id, text: 'Drafting…' })
    try {
      const res = await api.draftReply(id)
      setDraft({ id, text: res.draft })
    } catch (err) {
      setDraft({ id, text: err instanceof Error ? err.message : 'Draft failed' })
    }
  }

  if (!authed) return <AuthScreen onAuthed={() => setAuthed(true)} />

  return (
    <div className="hm chamber">
      <header className="chamber-nav">
        <Link className="hm-mark" to="/">
          Undertow
        </Link>
        <div className="chamber-live" aria-label="Sources on this watchlist">
          {livePlatforms.map((p) => (
            <span key={p.id}>
              <i className={`chamber-dot${p.on ? ' on' : ''}`} />
              {p.id}
            </span>
          ))}
        </div>
        <div className="chamber-actions">
          <button className="scan" onClick={scanNow} disabled={scanning}>
            {scanning ? 'Scanning' : 'Scan now'}
          </button>
          <Link to="/">Home</Link>
          <button
            type="button"
            onClick={() => {
              api.setToken(null)
              setAuthed(false)
            }}
          >
            Sign out
          </button>
        </div>
      </header>

      {error && <div className="chamber-err">{error}</div>}

      <div className="chamber-grid">
        <aside className="chamber-side">
          <h2>Watch</h2>
          <p className="chamber-meta">
            Add the words you care about. Undertow searches HN, X, and GitHub for those words, not the whole web.
          </p>
          <form onSubmit={addWatchlist} className="chamber-add">
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Add a keyword"
              aria-label="Add a keyword"
              autoComplete="off"
            />
            <button type="submit">Add</button>
          </form>
          <ul className="chamber-list">
            {watchlists.map((w) => (
              <li key={w.id}>
                <span>
                  {w.keyword}
                  <small>{w.platforms.join(' · ')}</small>
                </span>
                <button type="button" onClick={() => removeWatchlist(w.id)} aria-label={`Remove ${w.keyword}`}>
                  Remove
                </button>
              </li>
            ))}
            {!watchlists.length && (
              <li className="chamber-empty-kw">Nothing watched yet. Type a keyword and press Add.</li>
            )}
          </ul>

          <p className="chamber-label">Source</p>
          <div className="chamber-filters">
            {PLATFORMS.map((p) => (
              <button
                key={p.id || 'all'}
                type="button"
                className={platform === p.id ? 'on' : ''}
                onClick={() => setPlatform(p.id)}
              >
                {p.label}
              </button>
            ))}
          </div>
          <p className="chamber-label">Tag</p>
          <div className="chamber-filters">
            {TAGS.map((t) => (
              <button
                key={t.id || 'all'}
                type="button"
                className={tag === t.id ? 'on' : ''}
                onClick={() => setTag(t.id)}
              >
                {t.label}
              </button>
            ))}
          </div>
        </aside>

        <main className="chamber-feed">
          <h2>Feed</h2>
          <p className="chamber-meta">{posts.length} matched posts</p>
          {posts.map((p, i) => (
            <article className="chamber-post" key={`${p.id}-${p.watchlist_id ?? ''}-${p.source}-${i}`}>
              <header>
                <span>{p.source}</span>
                <span>{timeAgo(p.posted_at || p.ingested_at)}</span>
                {p.tag && <span className="tag">{p.tag}</span>}
                <span>rel {Math.round(p.relevance_score ?? 0)}</span>
              </header>
              {safeHref(p.url) ? (
                <a href={safeHref(p.url)} target="_blank" rel="noopener noreferrer">
                  {p.title || p.body.slice(0, 120)}
                </a>
              ) : (
                <span>{p.title || p.body.slice(0, 120)}</span>
              )}
              <p>{p.body}</p>
              <footer>
                <span>
                  {p.engagement}
                  {p.keyword ? ` · ${p.keyword}` : ''}
                </span>
                <button type="button" onClick={() => onDraft(p.id)}>
                  Draft reply
                </button>
              </footer>
              {draft?.id === p.id && (
                <div className="chamber-draft">
                  <button type="button" onClick={() => setDraft(null)} aria-label="Close draft">
                    <X size={14} />
                  </button>
                  {draft.text}
                </div>
              )}
            </article>
          ))}
          {!posts.length && (
            <div className="chamber-empty">No signals yet. Add a keyword and scan.</div>
          )}
        </main>

        <aside className="chamber-rail">
          <h2>Digest</h2>
          <p className="chamber-meta">
            Last {digest?.hours ?? 24}h · score ≥ 60 · {digest?.total ?? 0} posts
          </p>
          <dl>
            {(digest?.by_tag || []).map((g) => (
              <div key={g.tag}>
                <dt>{g.tag}</dt>
                <dd>{g.count}</dd>
              </div>
            ))}
            {!digest?.by_tag?.length && (
              <div>
                <dt>Hits</dt>
                <dd>None yet</dd>
              </div>
            )}
          </dl>
          <h2 style={{ marginTop: '2.2rem' }}>Week</h2>
          <dl>
            <div>
              <dt>Scanned</dt>
              <dd>{stats?.posts_scanned ?? 0}</dd>
            </div>
            <div>
              <dt>High signal</dt>
              <dd>{stats?.high_relevance_hits ?? 0}</dd>
            </div>
            <div>
              <dt>Drafts</dt>
              <dd>{stats?.replies_drafted ?? 0}</dd>
            </div>
          </dl>
        </aside>
      </div>
    </div>
  )
}
