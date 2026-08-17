import { useEffect } from 'react'

export default function NotFound() {
  useEffect(() => {
    document.documentElement.classList.add('hm-root')
    return () => document.documentElement.classList.remove('hm-root')
  }, [])

  return (
    <div className="hm">
      <header className="hm-nav">
        <a className="hm-mark" href="/">
          Sudo
        </a>
        <nav className="hm-links" aria-label="Primary">
          <a href="/">Home</a>
          <a href="/app">Open</a>
        </nav>
      </header>
      <main className="hm-hero">
        <div className="hm-hero-copy">
          <p className="nf-kicker">404</p>
          <h1>This page drifted.</h1>
          <p className="hm-lede">Nothing is listening at this address. The chamber is still one street over.</p>
          <a className="hm-cta" href="/">
            Back to Sudo
          </a>
        </div>
      </main>
    </div>
  )
}
