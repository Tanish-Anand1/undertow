export const HIGH_SIGNAL = 80

export function statusLine(kind: 'empty' | 'scan' | 'x' | 'twice' | 'signoff') {
  if (kind === 'empty') return "Nothing yet. Wick's listening, just hasn't heard your name mentioned."
  if (kind === 'scan') return "Wick's down there. Give it a second."
  if (kind === 'x') return "Wick's taking a breather on X for a bit — everything else is still coming in fine."
  if (kind === 'twice') return 'Wick actually stopped and read this one twice.'
  return "That's what surfaced this week. — Wick"
}

export function wickHeard(keyword: string) {
  const k = keyword.trim()
  if (!k) return ''
  return `Heard it — watching for '${k}' now.`
}

export function wickTwice(keyword?: string | null) {
  const k = (keyword || '').trim()
  if (!k) return statusLine('twice')
  return `Wick stopped on this one — it's about ${k} again.`
}

export function wickWelcomeBack(n: number) {
  if (n <= 0) return 'Nothing new since you were last here.'
  return `Welcome back. Wick's been listening — ${n} things surfaced since you were last here.`
}
