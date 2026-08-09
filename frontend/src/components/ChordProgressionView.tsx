import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import type { GeneratedPiece } from '../types'

const GROUP = 4

type Props = {
  piece: GeneratedPiece
  activeBar: number | null
}

export function ChordProgressionView({ piece, activeBar }: Props) {
  const { t } = useTranslation()
  const groups = useMemo(() => {
    const chords = piece.chords ?? []
    const out: { startBar: number; symbols: { bar: number; symbol: string }[] }[] =
      []
    for (let i = 0; i < chords.length; i += GROUP) {
      const slice = chords.slice(i, i + GROUP)
      out.push({
        startBar: slice[0]?.bar ?? i,
        symbols: slice.map((c) => ({ bar: c.bar, symbol: c.symbol })),
      })
    }
    return out
  }, [piece.chords])

  const activeGroup =
    activeBar == null ? -1 : Math.floor(activeBar / GROUP)

  return (
    <div className="chord-progression" aria-live="polite">
      <h3 className="params-subtitle">{t('atelier.chordProgression')}</h3>
      <p className="params-lead chord-progression-lead">
        {t('atelier.chordProgressionLead')}
      </p>
      <div className="chord-groups">
        {groups.map((g, gi) => (
          <div
            key={g.startBar}
            className={
              gi === activeGroup ? 'chord-group active' : 'chord-group'
            }
          >
            <div className="chord-group-label">
              {t('atelier.barsRange', {
                from: g.startBar + 1,
                to: g.startBar + g.symbols.length,
              })}
            </div>
            <ol className="chord-cells">
              {g.symbols.map((c) => (
                <li
                  key={c.bar}
                  className={
                    activeBar === c.bar ? 'chord-cell current' : 'chord-cell'
                  }
                >
                  <span className="chord-bar">
                    {t('atelier.barN', { n: c.bar + 1 })}
                  </span>
                  <span className="chord-symbol mono">{c.symbol}</span>
                </li>
              ))}
            </ol>
          </div>
        ))}
      </div>
    </div>
  )
}
