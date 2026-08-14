# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated from explicit brief: single-file static HTML/JS landing with CDN Three.js, GSAP, Lenis, and custom GLSL; separate React+Vite dashboard already exists for the app. Deploy as a static file openable in any modern browser.

## Users

Primary users are early-stage founders and indie makers who need to listen for customer pain, questions, and praise across Reddit, Hacker News, and X without manually refreshing feeds all day.

## Product Purpose

Undertow is a multiplatform founder-research tool. Founders set keyword/niche watchlists; the system continuously ingests matching posts, classifies them (pain / question / complaint / praise), and surfaces them in a live feed plus a daily digest. Success means high-signal posts reach the founder before competitors reply.

## Positioning

Posts are crawled once across the unique keyword set and matched globally via `watchlist_matches`, so listening cost stays sublinear as users grow. The product is a listening/monitoring instrument, not a CRM or social scheduler.

## Operating Context

- Founders scan a dark monitoring dashboard, add keywords, filter by platform/tag, draft replies, and read a daily digest email.
- The marketing surface must sell the listening loop before asking them to register for the app.

## Capabilities and Constraints

- Platforms: Hacker News (live), Reddit and X (credential-gated), classification via Anthropic Haiku with heuristic fallback.
- Auth: email/password JWT. No orgs/teams, LinkedIn, billing, or mobile app in v1.
- Landing constraint (user-pinned): immersive WebGL + Lenis scroll storytelling in one HTML file; dark high-contrast overlay; mouse-reactive camera; scroll-driven zones.

## Brand Commitments

- Name: **Undertow**
- Identity: signal / listening tool — near-black canvas, teal signal accent (~#5EEAD4), not CRM chrome.
- Craft references (user-pinned): podium.space (scroll storytelling, grain, typographic restraint, Lenis+GSAP+WebGL sync) and lenis.dev (silky controllable scroll).
- Technical brief (user-pinned): Three.js scene with custom GLSL (noise, bloom, reactive light), Lenis or GSAP ScrollTrigger path, DOM typography synced to camera waypoints.

## Evidence on Hand

- Working product app at `frontend/` (React dashboard) and `backend/` (FastAPI).
- No customer logos, testimonials, or paid benchmarks. Landing must not invent metrics, customer names, or uptime claims. Synthetic demo feed labels are allowed if marked as sample.

## Product Principles

1. Signal over noise — every surface should feel like a listening instrument.
2. Prove the mechanism — show the listen → classify → surface loop, don't claim generic "AI insights."
3. Sublinear listening — one crawl, many matches; the architecture is part of the story.
4. Restraint with craft — premium through material and motion, not neon clutter.
5. Honesty — no fabricated social proof.

## Accessibility & Inclusion

Prefer `prefers-reduced-motion` fallbacks that keep content readable without vestibular scroll-camera motion. Maintain body text contrast ≥4.5:1 on overlays.
