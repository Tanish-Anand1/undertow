import Lenis from 'lenis'
import './chrome.css'
import './landing/Landing.css'
import './Wick.css'
import 'lenis/dist/lenis.css'

document.documentElement.classList.add('hm-root')

const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
const finePointer = window.matchMedia('(pointer: fine)').matches

document.querySelectorAll<SVGElement>('.wick-mark').forEach((el) => {
  el.style.setProperty('--blink', `${5 + Math.random() * 3}s`)
})

if (!reduce && finePointer) {
  const lenis = new Lenis({
    duration: 0.72,
    lerp: 0.12,
    smoothWheel: true,
    orientation: 'vertical',
    gestureOrientation: 'vertical',
    touchMultiplier: 1,
  })
  const loop = (time: number) => {
    lenis.raf(time)
    requestAnimationFrame(loop)
  }
  requestAnimationFrame(loop)
}

function apiBase() {
  const host = window.location.hostname
  if (host === 'localhost' || host === '127.0.0.1') return ''
  const fromEnv = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '')
  if (fromEnv) return fromEnv
  return 'https://undertow-api.vercel.app'
}

function visitorId() {
  const key = 'sudo_vid'
  let id = localStorage.getItem(key)
  if (!id || id.length < 8) {
    id = crypto.randomUUID().replace(/-/g, '')
    localStorage.setItem(key, id)
  }
  return id.slice(0, 64)
}

function ping(kind: 'visit' | 'click') {
  const url = `${apiBase()}/presence/ping`
  void fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ visitor_id: visitorId(), kind }),
    keepalive: true,
    mode: 'cors',
  }).catch(() => undefined)
}

ping('visit')
document.querySelectorAll<HTMLAnchorElement>('a[href="/app"]').forEach((link) => {
  link.addEventListener('click', () => ping('click'), { passive: true })
})

