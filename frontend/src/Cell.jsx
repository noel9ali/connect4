export default function Cell({ value, isNew, row, isWinner }) {
  const dropDuration = value ? `${300 + row * 40}ms` : '0ms'

  let cls = 'cell'
  if (value === 1) cls += ' cell-player'
  if (value === 2) cls += ' cell-bot'
  if (isNew && value) cls += ' cell-drop'
  if (isWinner) cls += ' cell-winner'

  return (
    <div
      className={cls}
      style={isNew && value ? { '--drop-duration': dropDuration } : {}}
    />
  )
}
