import { useEffect, useState, type FormEvent } from 'react'
import { adminApi, type AdminUser } from './api'
import './Dashboard.css'
import './Admin.css'

export default function Admin() {
  const [unlocked, setUnlocked] = useState(Boolean(adminApi.token()))
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [users, setUsers] = useState<AdminUser[]>([])
  const [count, setCount] = useState(0)
  const [visitors, setVisitors] = useState(0)
  const [views, setViews] = useState(0)
  const [clicks, setClicks] = useState(0)

  useEffect(() => {
    document.documentElement.classList.add('hm-root')
    return () => document.documentElement.classList.remove('hm-root')
  }, [])

  useEffect(() => {
    if (!unlocked) return
    let cancelled = false
    adminApi
      .overview()
      .then((data) => {
        if (cancelled) return
        setUsers(data.users)
        setCount(data.user_count)
        setVisitors(data.unique_visitors ?? 0)
        setViews(data.page_views ?? 0)
        setClicks(data.cta_clicks ?? 0)
      })
      .catch((err) => {
        if (cancelled) return
        adminApi.clear()
        setUnlocked(false)
        setError(err instanceof Error ? err.message : 'Locked')
      })
    return () => {
      cancelled = true
    }
  }, [unlocked])

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await adminApi.unlock(password)
      setPassword('')
      setUnlocked(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Wrong password')
    } finally {
      setBusy(false)
    }
  }

  if (!unlocked) {
    return (
      <div className="hm chamber">
        <header className="hm-nav">
          <a className="hm-mark" href="/">
            Sudo
          </a>
          <nav className="hm-links" aria-label="Primary">
            <a href="/">Home</a>
          </nav>
        </header>
        <div className="auth-wrap">
          <form onSubmit={submit} className="auth-form">
            <h1>Ledger.</h1>
            <p>Private roll of who is listening, and to which words.</p>
            <label htmlFor="admin-pass">Password</label>
            <input
              id="admin-pass"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
            {error && <p className="auth-err">{error}</p>}
            <button className="hm-cta" disabled={busy} type="submit">
              {busy ? 'Please wait' : 'Open ledger'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="hm chamber">
      <header className="hm-nav">
        <a className="hm-mark" href="/">
          Sudo
        </a>
        <nav className="hm-links" aria-label="Primary">
          <span>{count} accounts · {visitors} visited</span>
          <button
            type="button"
            className="admin-lock"
            onClick={() => {
              adminApi.clear()
              setUnlocked(false)
            }}
          >
            Lock
          </button>
        </nav>
      </header>
      <main className="admin-main">
        <h1>Who is researching</h1>
        <dl className="admin-stats">
          <div>
            <dt>People who visited</dt>
            <dd>{visitors}</dd>
          </div>
          <div>
            <dt>Page loads</dt>
            <dd>{views}</dd>
          </div>
          <div>
            <dt>Start / log in clicks</dt>
            <dd>{clicks}</dd>
          </div>
          <div>
            <dt>Accounts</dt>
            <dd>{count}</dd>
          </div>
        </dl>
        {users.length === 0 ? (
          <p className="admin-empty">No accounts yet.</p>
        ) : (
          <ul className="admin-list">
            {users.map((user) => (
              <li key={user.id} className="admin-card">
                <header>
                  <strong>{user.email}</strong>
                  <span>
                    {user.google ? 'Google' : 'Email'}
                    {user.last_scan_at ? ` · scanned ${user.last_scan_at.slice(0, 10)}` : ' · no scan yet'}
                  </span>
                </header>
                {user.keywords.length === 0 ? (
                  <p>Nothing watched.</p>
                ) : (
                  <ul className="admin-keys">
                    {user.keywords.map((item) => (
                      <li key={item.keyword}>
                        <em>{item.keyword}</em>
                        <span>{item.platforms.join(', ') || 'all'}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  )
}
