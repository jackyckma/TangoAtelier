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
    const out: {
      startBar: number
      key?: string
      symbols: { bar: number; symbol: string; key?: string }[]
    }[] = []
    for (let i = 0; i < chords.length; i += GROUP) {
      const slice = chords.slice(i, i + GROUP)
      out.push({
        startBar: slice[0]?.bar ?? i,
        key: slice[0]?.key,
        symbols: slice.map((c) => ({
          bar: c.bar,
          symbol: c.symbol,
          key: c.key,
        })),
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

      {piece.harmony_plan && piece.harmony_plan.length > 0 && (
        <ul className="harmony-plan">
          {piece.harmony_plan.map((h) => (
            <li key={`${h.section}-${h.key}-${h.progression_id}`}>
              <span className="harmony-section">{h.section}</span>
              <span className="mono">
                {h.key}
                {h.modulation
                  ? ` · ${t(`atelier.modulation.${h.modulation}`, {
                      defaultValue: h.modulation,
                    })}`
                  : ''}
              </span>
              <span className="mono harmony-prog">
                {h.progression.join(' → ')}
              </span>
            </li>
          ))}
        </ul>
      )}

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
              {g.key ? ` · ${g.key}` : ''}
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
