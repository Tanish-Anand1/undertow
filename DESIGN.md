---
name: Undertow
description: Listening darkroom — founder signal develops out of the social noise field.
colors:
  ink: "#070a0c"
  ink-2: "#0d1216"
  ink-on-signal: "#041012"
  foam: "#e7eef2"
  silver: "#c5d0d8"
  mist: "#8a9aa8"
  signal: "#5eead4"
  signal-dim: "rgba(94, 234, 212, 0.14)"
  signal-deep: "#1a3a42"
  tag-pain: "#f5c078"
  tag-question: "#8ec8f5"
  tag-complaint: "#f0a0a8"
  tag-praise: "#8fe0b8"
  solid-fallback: "#10161b"
typography:
  display:
    fontFamily: "Cabinet Grotesk, sans-serif"
    fontSize: "clamp(3.2rem, 9vw, 6rem)"
    fontWeight: 800
    lineHeight: 0.95
    letterSpacing: "-0.035em"
  title:
    fontFamily: "Cabinet Grotesk, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Satoshi, system-ui, sans-serif"
    fontSize: "clamp(1.05rem, 2vw, 1.25rem)"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "0.72rem"
    fontWeight: 400
    letterSpacing: "0.04em"
  brand-nav:
    fontFamily: "Cabinet Grotesk, sans-serif"
    fontSize: "1.2rem"
    fontWeight: 800
    letterSpacing: "-0.03em"
rounded:
  none: "0"
  full: "9999px"
spacing:
  xs: "0.5rem"
  sm: "0.85rem"
  md: "1.25rem"
  lg: "1.35rem"
  xl: "2rem"
  panel-x: "clamp(1.25rem, 5vw, 4rem)"
  panel-y: "clamp(5rem, 12vh, 8rem)"
  content-max: "1120px"
components:
  button-primary:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.ink-on-signal}"
    rounded: "{rounded.none}"
    padding: "0.95rem 1.35rem"
    typography: "Satoshi 700 / 0.95rem"
  button-primary-hover:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.ink-on-signal}"
  button-ghost:
    backgroundColor: "rgba(13, 18, 22, 0.45)"
    textColor: "{colors.foam}"
    rounded: "{rounded.none}"
    padding: "0.95rem 1.25rem"
  button-nav:
    backgroundColor: "{colors.signal-dim}"
    textColor: "{colors.signal}"
    rounded: "{rounded.none}"
    padding: "0.7rem 1.1rem"
  glass-tray:
    backgroundColor: "rgba(13, 18, 22, 0.52)"
    textColor: "{colors.foam}"
    rounded: "{rounded.none}"
    padding: "1.25rem 1.35rem"
    width: "min(520px, 100%)"
  tag-signal:
    backgroundColor: "rgba(94, 234, 212, 0.06)"
    textColor: "{colors.signal}"
    rounded: "{rounded.none}"
    padding: "0.4rem 0.65rem"
    typography: "JetBrains Mono 0.7rem / 0.06em / uppercase"
---

# Design System: Undertow

## Overview

**Creative North Star: "The Listening Darkroom"**

Undertow is a near-black chamber where founder signal develops under a teal safelight. The marketing surface is not a SaaS feature grid: it is a scroll-driven darkroom — full-bleed WebGL particle undertow behind silver developed copy, grain and vignette as atmosphere, and glass only where an instrument readout belongs.

Density is spare and typographic. Each station carries one display line, one short lede, and at most one tray of classified signal. Motion is the camera advancing through Lenis-synced waypoints; UI chrome stays sharp-cornered and quiet so the field can breathe.

Confirmed visual rejections from the shipped build: no eyebrow/kicker strips (`.kicker-ban`), no card grids as marketing layout, no rounded SaaS chrome on CTAs or trays.

**Key Characteristics:**
- Near-black ink field with teal safelight accent and silver body copy
- Cabinet Grotesk display + Satoshi body + JetBrains Mono instrument labels
- Full-bleed WebGL undertow + grain (9% overlay) + vignette as the depth stack
- Sharp corners everywhere except circular station/progress dots
- Glass trays reserved for classification/digest instrument readouts

## Colors

A darkroom palette: chamber blacks, developed foam/silver text, one teal safelight, and four soft classification dyes used only on tags.

### Primary
- **Safelight Teal** (`signal`): The single accent — brand mark, emphasis in display (`em`), primary CTA fill, progress current state, mono tray labels, default tag.
- **Safelight Wash** (`signal-dim`): Nav CTA fill and related dim washes at ~14% teal.

### Secondary
- **Undertow Dim** (`signal-deep`): Particle field dim mix in the WebGL undertow — deep teal-ink for additive points, not UI fills.

### Tertiary
- **Classification dyes** (`tag-pain`, `tag-question`, `tag-complaint`, `tag-praise`): Soft amber, blue, rose, and mint used only on instrument tags with matching low-alpha borders/fills.

### Neutral
- **Chamber Ink** (`ink`): Page/WebGL clear color and fog base.
- **Tray Ink** (`ink-2`): Glass and ghost button translucent bases (`rgba(13, 18, 22, …)`).
- **Ink on Signal** (`ink-on-signal`): Text on filled primary CTA.
- **Foam** (`foam`): Primary display/brand text on ink.
- **Developed Silver** (`silver`): Lede / supporting copy.
- **Mist** (`mist`): Meta, hints, secondary station copy.
- **Solid Fallback** (`solid-fallback`): Opaque substitute when `prefers-reduced-transparency` disables glass blur.

### Named Rules
**The Safelight Rule.** Teal is the only UI accent. It stays rare: mark, emphasis word, CTAs, instrument chrome — never a purple/indigo marketing wash.

**The Classification Dye Rule.** Pain/question/complaint/praise colors appear only on tags inside instrument contexts. They do not recolor headlines, backgrounds, or CTAs.

## Typography

**Display Font:** Cabinet Grotesk (with sans-serif)
**Body Font:** Satoshi (with system-ui, sans-serif)
**Label/Mono Font:** JetBrains Mono (with ui-monospace, monospace)

**Character:** Compressed, high-contrast display for station titles; calm Satoshi for developed body; mono for tray headers, tags, and scroll hints — the instrument voice.

### Hierarchy
- **Display** (800, `clamp(3.2rem, 9vw, 6rem)`, line-height 0.95, tracking `-0.035em`): Hero and station titles; max ~12ch (14ch on closing CTA). Signal emphasis via non-italic `em`.
- **Title** (700, ~1.05–1.1rem, tracking `-0.02em`): Feed-card and station-list headings inside trays/lists.
- **Body / Lede** (400, `clamp(1.05rem, 2vw, 1.25rem)`, line-height 1.55, max ~38ch): Silver supporting sentence under each display.
- **Label** (Mono, 0.68–0.72rem, uppercase, tracking `0.04–0.14em`): Tray headers (`.mono`), tags, scroll hint.
- **Brand nav** (Cabinet 800, 1.2rem, tracking `-0.03em`): Wordmark beside the mark.

### Named Rules
**The Three-Voice Rule.** Display = Cabinet. UI/body = Satoshi. Instrument = JetBrains Mono. Do not swap roles.

**The No-Kicker Rule.** No eyebrow, kicker, or uppercase label above the display. Station identity is the display line itself.

## Layout

Scroll storytelling on a fixed WebGL stage: five full-viewport panels (`min-height: 100dvh`) stacked in a relative scroll root. Content sits in a centered column (`max-width: 1120px`) with horizontal padding `clamp(1.25rem, 5vw, 4rem)` and vertical padding `clamp(5rem, 12vh, 8rem)` (tightened top on ≤768px).

Rhythm is one composition per station: display → lede → optional CTA row / station list / tag row + glass tray. Gap scale clusters around `0.5rem` (tags), `0.85rem` (lists/CTAs/meta), `1.25–1.35rem` (glass/nav padding), `2rem` (CTA row offset). Fixed nav, right-edge progress rail (hidden ≤768px), and bottom scroll hint sit above the grain layer.

Inactive panels keep inner content dimmed, slightly translated, and soft-blurred until the viewport center activates them; reduced-motion shows all panels fully readable.

## Elevation & Depth

Depth is atmospheric, not card-shadow UI. The stack is: WebGL field (z0) → vignette → grain → scroll content → nav/progress. Glass trays use a single deep ambient shadow and blur; primary CTAs do not lift with drop shadows.

### Shadow Vocabulary
- **Tray ambient** (`box-shadow: 0 18px 50px rgba(0, 0, 0, 0.35)`): Glass instrument trays only.
- **Signal pulse** (animated `box-shadow` ring on station dots): Presence indicator, not elevation.

### Named Rules
**The Atmosphere-Not-Chrome Rule.** Depth comes from vignette, grain, fog, and bloom — not stacked card elevations or neon glows on buttons.

**The Glass Tray Rule.** Backdrop-blur glass is reserved for instrument readouts (classification/digest). Do not glass-wrap marketing copy blocks or hero text.

## Shapes

Form language is square and instrument-like: buttons, tags, glass trays, and nav CTA use `border-radius: 0`. The only round geometry is the 8–10px station/progress dots (`border-radius: 50%` / full). Borders are 1px hairlines at low foam or teal alpha — not thick frames.

## Components

### Buttons
- **Shape:** Sharp rectangle (`0` radius)
- **Primary:** Signal fill, ink-on-signal text, Satoshi 700, padding `0.95rem 1.35rem`; hover brightens (~8%); active scales to `0.97`
- **Ghost:** Tray-ink translucent fill, foam text, foam hairline border; hover shifts border toward signal
- **Nav CTA:** Signal-dim fill, signal text/border; denser padding `0.7rem 1.1rem`

### Chips / Tags
- **Style:** Mono uppercase, sharp corners, 1px dyed border + ~6–8% fill
- **Variants:** Default signal; `pain` / `question` / `complaint` / `praise` dyes
- **Use:** Classification labels inside trays or tag rows — not navigation pills

### Cards / Containers
- **Glass tray:** Sharp, `rgba(13,18,22,0.52)`, teal hairline, blur `18px` + saturate `140%`, tray ambient shadow, padding `1.25rem 1.35rem`, width `min(520px, 100%)`
- **Feed rows:** Separated by foam hairline tops — not nested card stacks
- **Solid fallback:** `#10161b` when reduced transparency is preferred

### Navigation
- **Top bar:** Fixed, foam brand + Cabinet wordmark, gradient fade into ink, blur `14px`; right-aligned nav CTA
- **Progress rail:** Vertical 8px dots on the right; current fills signal and scales `1.35`
- **Scroll hint:** Fixed bottom mono mist label; fades after first advance

### Signature: Station panel
Full-viewport storytelling unit synced to Lenis/GSAP camera waypoints. Active inner content clears to full opacity; inactive stays underdeveloped (low opacity, blur, slight Y offset) unless reduced motion is on.

## Do's and Don'ts

### Do:
- **Do** keep the first viewport as brand-scale display + one silver lede + one primary CTA over the full-bleed undertow.
- **Do** use glass trays only for instrument sample readouts with mono headers.
- **Do** honor `prefers-reduced-motion` (readable panels, no scroll-camera dependency) and `prefers-reduced-transparency` (solid `#10161b` trays/nav).
- **Do** mark sample feed content as sample — never invent live metrics or customer claims.

### Don't:
- **Don't** add kickers/eyebrows above display lines.
- **Don't** round CTA or tray corners into SaaS pill/card chrome.
- **Don't** spread classification dyes or teal washes across full backgrounds.
- **Don't** replace the WebGL undertow + grain stack with flat solid marketing sections or feature-card grids.
