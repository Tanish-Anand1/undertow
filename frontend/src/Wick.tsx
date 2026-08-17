import { useEffect, useRef } from 'react'

export type WickMood = 'idle' | 'typing' | 'scanning' | 'found' | 'resting'

export function WickMark({ mood = 'idle', className }: { mood?: WickMood; className?: string }) {
  const ref = useRef<SVGSVGElement>(null)
  useEffect(() => {
    ref.current?.style.setProperty('--blink', `${5 + Math.random() * 3}s`)
  }, [])
  return (
    <svg
      ref={ref}
      className={`wick-mark wick--${mood}${className ? ` ${className}` : ''}`}
      viewBox="0 0 120 148"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <g className="wick-body">
        <circle cx="60" cy="42" r="26" stroke="#111" strokeWidth="1.4" />
        <path d="M42 42h36" stroke="#111" strokeWidth="1.4" />
        <g className="wick-eyes">
          <circle className="wick-eye" cx="51" cy="42" r="2.2" fill="#111" />
          <circle className="wick-eye" cx="69" cy="42" r="2.2" fill="#111" />
        </g>
        <path d="M48 78c4-12 8-18 12-18s8 6 12 18" stroke="#111" strokeWidth="1.4" strokeLinejoin="round" />
        <path d="M44 128c6-28 10-42 16-42s10 14 16 42" stroke="#111" strokeWidth="1.4" strokeLinejoin="round" />
        <g className="wick-arcs">
          <path d="M88 40c10 2 16 10 16 20" stroke="#111" strokeWidth="1.2" strokeLinecap="round" />
          <path d="M92 36c12 4 20 14 20 26" stroke="#111" strokeWidth="1.2" strokeLinecap="round" opacity="0.45" />
        </g>
      </g>
    </svg>
  )
}
