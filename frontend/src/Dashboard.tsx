import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { HIGH_SIGNAL, statusLine, wickHeard, wickTwice, wickWelcomeBack } from './copy'
import { WickMark, type WickMood } from './Wick'
import './Wick.css'
import { api, type Digest, type Post, type Stats, type Watchlist } from './api'
import './Dashboard.css'

const EASE_OUT = [0.23, 1, 0.32, 1] as const

const PLATFORMS = [
  { id: '', label: 'All', soon: false },
  { id: 'hn', label: 'HN', soon: false },
  { id: 'x', label: 'X', soon: false },
  { id: 'github', label: 'GitHub', soon: false },
  { id: 'reddit', label: 'Reddit', soon: true },
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

function OnboardingScreen({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState<'q1' | 'q2' | 'name' | 'login' | 'register'>('q1')
  const [iceCream, setIceCream] = useState('')
  const [fight, setFight] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = ''
    }
  }, [])

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (step === 'q1') {
      if (!iceCream) { setError('Please pick a flavor'); return; }
      setStep('q2')
      setError('')
      return
    }
    if (step === 'q2') {
      if (!fight) { setError('Please pick an opponent'); return; }
      setStep('name')
      setError('')
      return
    }
    if (step === 'name') {
      if (!name.trim()) { setError('Please enter a name'); return; }
      setStep('register')
      setError('')
      return
    }
    setBusy(true)
    setError('')
    try {
      if (step === 'register') {
        await api.upgrade(name, email, password)
      } else {
        await api.login(email, password)
      }
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Auth failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }} 
      animate={{ opacity: 1 }} 
      exit={{ opacity: 0 }} 
      transition={{ duration: 0.25 }}
      className="hm chamber hm-onboarding-overlay" 
      style={{ position: 'fixed', inset: 0, zIndex: 100, background: 'var(--bg)' }}
    >
      <div className="auth-wrap">
        <form onSubmit={submit} className="auth-form">
          <WickMark mood="idle" className="wick-auth" />
          <h1>{step === 'q1' ? 'What\'s your favorite ice cream flavor?' : step === 'q2' ? 'If you had to fight...' : step === 'name' ? 'What should Wick call you?' : (step === 'login' ? 'Enter.' : 'Begin.')}</h1>
          <p>The feed is private. Wick is already listening.</p>
          
          <AnimatePresence mode="wait">
            {step === 'q1' ? (
              <motion.div key="q1" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.25 }} className="auth-options">
                <label>Choose wisely</label>
                <div className="auth-choices">
                  {['Chocolate', 'Vanilla', 'Strawberry', 'Mint', 'Something Weird'].map(opt => (
                    <button key={opt} type="button" className={`auth-choice ${iceCream === opt ? 'selected' : ''}`} onClick={() => setIceCream(opt)}>
                      {opt}
                    </button>
                  ))}
                </div>
              </motion.div>
            ) : step === 'q2' ? (
              <motion.div key="q2" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.25 }} className="auth-options">
                <label>Choose your opponent</label>
                <div className="auth-choices">
                  <button type="button" className={`auth-choice ${fight === 'duck' ? 'selected' : ''}`} onClick={() => setFight('duck')}>
                    A horse-sized duck
                  </button>
                  <button type="button" className={`auth-choice ${fight === 'horses' ? 'selected' : ''}`} onClick={() => setFight('horses')}>
                    100 duck-sized horses
                  </button>
                </div>
              </motion.div>
            ) : step === 'name' ? (
              <motion.div key="name" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.25 }}>
                <label htmlFor="name">Name</label>
                <input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  type="text"
                  required
                  autoFocus
                />
              </motion.div>
            ) : (
              <motion.div key="creds" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.25 }}>
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  type="email"
                  required
                  autoFocus
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
              </motion.div>
            )}
          </AnimatePresence>

          {error && <p className="auth-err">{error}</p>}
          <button className="hm-cta" disabled={busy} type="submit">
            {step === 'q1' || step === 'q2' || step === 'name' ? 'Continue' : busy ? 'Please wait' : step === 'login' ? 'Enter chamber' : 'Create account'}
          </button>
          
          {(step === 'login' || step === 'register') && (
            <button type="button" className="switch" onClick={() => setStep(step === 'login' ? 'register' : 'login')}>
              {step === 'login' ? 'Need an account? Register' : 'Have an account? Enter'}
            </button>
          )}
          <button type="button" className="switch" onClick={onClose} style={{ marginTop: '1rem', opacity: 0.7 }}>
            Cancel
          </button>
        </form>
      </div>
    </motion.div>
  )
}

function NameOnboarding({ onNext }: { onNext: (name: string) => void }) {
  const [name, setName] = useState('')

  return (
    <AuthChrome>
      <motion.form
        className="auth-form"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -12 }}
        transition={{ duration: 0.32, ease: EASE_OUT }}
        onSubmit={(e) => {
          e.preventDefault()
          const trimmed = name.trim()
          if (trimmed) onNext(trimmed)
        }}
      >
        <WickMark mood="found" className="wick-auth" />
        <h1>Nice work.</h1>
        <p>That was your two free scans. Before you keep going, who is Wick listening for?</p>
        <label htmlFor="onboard-name">Your name</label>
        <input
          id="onboard-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="What should Wick call you?"
          maxLength={120}
          autoFocus
          required
        />
        <button className="hm-cta" type="submit" disabled={!name.trim()}>
          Continue
        </button>
      </motion.form>
    </AuthChrome>
  )
}

function AuthScreen({
  guest = false,
  guestName = '',
  onAuthed,
}: {
  guest?: boolean
  guestName?: string
  onAuthed: (me: Me) => void
}) {
  const [mode, setMode] = useState<'login' | 'register'>(guest ? 'register' : 'login')
  const [name, setName] = useState(guestName)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const claiming = guest && mode === 'register'

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (claiming) {
        onAuthed(await api.claim(name.trim(), email, password))
      } else {
        if (mode === 'register') {
          await api.register(email, password, name.trim() || undefined)
        }
        await api.login(email, password)
        onAuthed(await api.me())
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Auth failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthChrome>
      <motion.form
        onSubmit={submit}
        className="auth-form"
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -12 }}
        transition={{ duration: 0.32, ease: EASE_OUT }}
      >
        <WickMark mood="idle" className="wick-auth" />
        <h1>{claiming ? 'Lock it in.' : mode === 'login' ? 'Enter.' : 'Begin.'}</h1>
        <p>
          {claiming
            ? `Save the feed so Wick keeps listening for ${name || 'you'} after you close this tab.`
            : 'The feed is private. Wick is already listening.'}
        </p>
        {mode === 'register' && (
          <>
            <label htmlFor="name">Name</label>
            <input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={120}
              required={guest}
            />
          </>
        )}
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
          {busy ? 'Please wait' : claiming ? 'Save my feed' : mode === 'login' ? 'Enter chamber' : 'Create account'}
        </button>
        <a className="google-auth" href={`${API_BASE}/auth/google/start`}>
          Continue with Google
        </a>
        <button type="button" className="switch" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
          {mode === 'login'
            ? guest
              ? 'Back to saving your feed'
              : 'Need an account? Register'
            : 'Already have an account? Log in'}
        </button>
      </motion.form>
    </AuthChrome>
  )
}

export default function Dashboard() {
  const [authed, setAuthed] = useState(!!api.token())
  const [showOnboarding, setShowOnboarding] = useState(false)
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
  const [keywordFocus, setKeywordFocus] = useState(false)
  const [heard, setHeard] = useState('')
  const [foundPulse, setFoundPulse] = useState(false)
  const [greeting, setGreeting] = useState('')
  const prevHigh = useRef(0)

  useEffect(() => {
    document.documentElement.classList.add('hm-root')
    return () => document.documentElement.classList.remove('hm-root')
  }, [])

  useEffect(() => {
    async function boot() {
      const hash = window.location.hash.slice(1)
      const params = new URLSearchParams(hash)
      const googleToken = params.get('google')
      const googleError = params.get('google_error')
      if (googleToken || googleError) {
        window.history.replaceState(null, '', window.location.pathname)
      }
      if (googleToken) {
        api.setToken(googleToken)
      } else if (googleError) {
        setError('Google sign-in was cancelled or failed.')
      }

      if (api.token()) {
        try {
          setMe(await api.me())
          return
        } catch {
          api.setToken(null)
        }
      }
      try {
        setMe(await api.startGuest())
      } catch (err) {
        setBootError(err instanceof Error ? err.message : 'Could not start a session')
      }
    }
    boot()
  }, [])

  const needsOnboarding = !!me && me.is_guest && me.guest_scans_used >= GUEST_SCAN_LIMIT

  const livePlatforms = useMemo(() => {
    const set = new Set<string>()
    watchlists.forEach((w) => w.platforms.forEach((p) => set.add(p)))
    return ['hn', 'x', 'github'].map((p) => ({ id: p, on: set.has(p) }))
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
    if (!sessionStorage.getItem('sudo_greeted')) {
      sessionStorage.setItem('sudo_greeted', '1')
      const prev = localStorage.getItem('sudo_seen_at')
      const n = prev
        ? f.filter((p) => new Date(p.ingested_at).getTime() > new Date(prev).getTime()).length
        : 0
      if (prev) setGreeting(wickWelcomeBack(n))
      localStorage.setItem('sudo_seen_at', new Date().toISOString())
    }
  }

  useEffect(() => {
    if (!me || needsOnboarding) return
    refresh()
      .then(() => {
        if (!didPrime) setDidPrime(true)
      })
      .catch((e) => setError(String(e.message || e)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me?.id, needsOnboarding, platform, tag])

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
      const created = await api.createWatchlist(value, ['hn', 'x', 'github'])
      setWatchlists((prev) => [created, ...prev])
      setHeard(wickHeard(value))
      setKeyword('')
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
      if (me?.is_guest) setMe(await api.me())
    } catch (err) {
      if (err instanceof Error && err.message.toLowerCase().includes('limit reached')) {
        setShowOnboarding(true)
      } else {
        setError(err instanceof Error ? err.message : 'Scan failed')
      }
    } finally {
      setScanning(false)
    }
  }

  useEffect(() => {
    if (!keywordFocus) return
    const t = window.setTimeout(() => {
      setHeard(keyword.trim() ? wickHeard(keyword) : '')
    }, 550)
    return () => window.clearTimeout(t)
  }, [keyword, keywordFocus])

  useEffect(() => {
    const n = posts.filter((p) => (p.relevance_score ?? 0) >= HIGH_SIGNAL).length
    if (!didPrime) {
      prevHigh.current = n
      return
    }
    if (n > prevHigh.current) {
      setFoundPulse(true)
      const t = window.setTimeout(() => setFoundPulse(false), 900)
      prevHigh.current = n
      return () => window.clearTimeout(t)
    }
    prevHigh.current = n
  }, [posts, didPrime])

  const wickMood: WickMood = scanning
    ? 'scanning'
    : stats?.x_circuit_open
      ? 'resting'
      : foundPulse
        ? 'found'
        : keywordFocus
          ? 'typing'
          : 'idle'

  const wickSaid = scanning
    ? statusLine('scan')
    : stats?.x_circuit_open
      ? statusLine('x')
      : heard || greeting || (!watchlists.length ? statusLine('empty') : '')

  async function onDraft(id: number) {
    setDraft({ id, text: 'Drafting…' })
    try {
      const res = await api.draftReply(id)
      setDraft({ id, text: res.draft })
    } catch (err) {
      setDraft({ id, text: err instanceof Error ? err.message : 'Draft failed' })
    }
  }

  useEffect(() => {
    if (!authed) {
      api.guestStart().then(() => setAuthed(true)).catch(console.error)
    }
  }, [authed])

  if (!authed) return null

  return (
    <div className="hm chamber">
      <AnimatePresence>
        {showOnboarding && <OnboardingScreen onClose={() => setShowOnboarding(false)} />}
      </AnimatePresence>
      <header className="chamber-nav">
        <a className="hm-mark" href="/">
          Sudo
        </a>
        <div className="chamber-live" aria-label="Sources on this watchlist">
          {livePlatforms.map((p) => (
            <span key={p.id}>
              <i className={`chamber-dot${p.on ? ' on' : ''}`} />
              {p.id}
            </span>
          ))}
        </div>
        <div className="chamber-actions">
          {guestScansLeft !== null && (
            <span className="chamber-guest-note">
              {guestScansLeft} free scan{guestScansLeft === 1 ? '' : 's'} left
            </span>
          )}
          <button
            className="scan"
            onClick={scanNow}
            disabled={scanning || !watchlists.length}
            aria-busy={scanning}
          >
            {scanning ? 'Scanning' : 'Scan now'}
          </button>
          <a href="/">Home</a>
          <button type="button" onClick={startOver}>
            {me.is_guest ? 'Restart' : 'Sign out'}
          </button>
        </div>
      </header>

      {error && <div className="chamber-err">{error}</div>}
      {stats?.x_circuit_open && <div className="chamber-wick-banner">{statusLine('x')}</div>}

      <div className="chamber-grid">
        <section className="chamber-side">
          <div className="wick-dock">
            <WickMark mood={wickMood} />
            <p className="wick-line">{wickSaid}</p>
          </div>
          <h2>Watch</h2>
          <p className="chamber-meta">
            Add as many keywords as you want, then hit Scan when you are ready. Sudo searches HN, X, and GitHub for those words.
          </p>
          <form onSubmit={addWatchlist} className="chamber-add">
            <input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onFocus={() => setKeywordFocus(true)}
              onBlur={() => setKeywordFocus(false)}
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
            {!watchlists.length && <li className="chamber-empty-kw">{statusLine('empty')}</li>}
          </ul>
          <button
            type="button"
            className="chamber-scan-inline"
            onClick={scanNow}
            disabled={scanning || !watchlists.length}
          >
            {scanning ? 'Scanning' : watchlists.length ? 'Scan these keywords' : 'Add a keyword first'}
          </button>

          <p className="chamber-label">Source</p>
          <div className="chamber-filters">
            {PLATFORMS.map((p) => (
              <button
                key={p.id || 'all'}
                type="button"
                className={platform === p.id ? 'on' : ''}
                disabled={p.soon}
                title={p.soon ? 'Reddit coming soon' : undefined}
                onClick={() => {
                  if (p.soon) return
                  setPlatform(p.id)
                }}
              >
                {p.label}
                {p.soon ? <i>soon</i> : null}
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
        </section>

        <main className="chamber-feed">
          <h2>Feed</h2>
          <p className="chamber-meta" aria-live="polite">
            {scanning ? statusLine('scan') : `${posts.length} matched posts`}
          </p>
          {posts.map((p, i) => {
            const twice = (p.relevance_score ?? 0) >= HIGH_SIGNAL
            return (
            <motion.article
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              viewport={{ once: true, margin: '-20px' }}
              className={`chamber-post${twice ? ' chamber-post--twice' : ''}`}
              key={`${p.id}-${p.watchlist_id ?? ''}-${p.source}-${i}`}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '0px 0px -10% 0px' }}
              transition={{ duration: 0.3, ease: EASE_OUT }}
            >
              <header>
                <span>{p.source}</span>
                <span>{timeAgo(p.posted_at || p.ingested_at)}</span>
                {p.tag && <span className="tag">{p.tag}</span>}
                <span>rel {Math.round(p.relevance_score ?? 0)}</span>
                {twice && <span className="wick-twice">{wickTwice(p.keyword)}</span>}
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
                    ×
                  </button>
                  {draft.text}
                </div>
              )}
            </motion.article>
            )
          })}
          {!posts.length && (
            <div className="chamber-empty">
              {scanning ? statusLine('scan') : watchlists.length ? 'Nothing on the wire yet. Hit Scan when you are ready.' : statusLine('empty')}
            </div>
          )}
        </main>

        <section className="chamber-rail">
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
          {stats?.x_circuit_open && <p className="chamber-wick-note">{statusLine('x')}</p>}
        </section>
      </div>
    </motion.div>
  )
}
