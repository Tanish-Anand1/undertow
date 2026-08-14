import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import Lenis from 'lenis'
import './Landing.css'

export default function Landing() {
  useEffect(() => {
    document.documentElement.classList.add('hm-root')
    return () => document.documentElement.classList.remove('hm-root')
  }, [])

  useEffect(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce) return

    const lenis = new Lenis({
      duration: 1.05,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    })

    let raf = 0
    const loop = (time: number) => {
      lenis.raf(time)
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)

    return () => {
      cancelAnimationFrame(raf)
      lenis.destroy()
    }
  }, [])

  return (
    <div className="hm">
      <header className="hm-nav">
        <a className="hm-mark" href="#top">
          Undertow
        </a>
        <nav className="hm-links" aria-label="Primary">
          <a href="#method">Method</a>
          <a href="#feed">The feed</a>
          <Link to="/app">Open</Link>
        </nav>
      </header>

      <main id="top">
        <section className="hm-hero">
          <h1>
            Hear what founders miss.
          </h1>
          <div className="hm-hero-bar">
            <p>
              Hacker News, GitHub, and X. Watched, classified, and laid out as one feed. Reddit is next, once API access is approved.
            </p>
            <Link className="hm-cta" to="/app">
              Start listening
            </Link>
          </div>
        </section>

        <section className="hm-names" aria-label="Sources">
          <span>Hacker News</span>
          <span>GitHub</span>
          <span>X</span>
          <span>Reddit soon</span>
        </section>

        <section className="hm-split" id="feed">
          <div className="hm-split-copy">
            <h2>A chamber, not a dashboard.</h2>
            <p>
              Set a keyword. Undertow crawls each unique term once, matches it to every watchlist that shares it, and tags the post: pain, question, complaint, or praise.
            </p>
          </div>
          <figure className="hm-plate">
            <blockquote>
              “Anyone else drowning in auth support tickets after the OAuth change?”
            </blockquote>
            <figcaption>
              <em>pain</em>
              <span>r/SaaS · matched “auth friction”</span>
            </figcaption>
          </figure>
        </section>

        <section className="hm-method" id="method">
          <h2>How it works</h2>
          <ol>
            <li>
              <strong>Watch a niche</strong>
              Add keywords like “auth friction” or your category. Live sources: HN, GitHub, X. Reddit coming soon.
            </li>
            <li>
              <strong>Crawl once</strong>
              Posts are fetched per unique keyword, not per user, then linked to every watchlist sharing it.
            </li>
            <li>
              <strong>Read the signal</strong>
              Irrelevant stays out. What remains is a live feed, a daily digest, and a draft reply when a thread is worth answering.
            </li>
          </ol>
        </section>

        <section className="hm-close">
          <h2>Add one keyword. Hit scan.</h2>
          <Link className="hm-cta" to="/app">
            Open Undertow
          </Link>
        </section>
      </main>
    </div>
  )
}
