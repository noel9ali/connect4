import { useState } from 'react'
import Cell from './Cell'

const ROWS = 6
const COLS = 7

export default function Board({ grid, onColClick, thinking, gameOver, winnerCells, lastNew }) {
  const [hoveredCol, setHoveredCol] = useState(null)

  function handleColClick(col) {
    if (thinking || gameOver) return
    onColClick(col)
  }

  // lastNew: { playerCell: {row,col}, botCell: {row,col} }
  function isNew(row, col) {
    if (!lastNew) return false
    const p = lastNew.playerCell
    const b = lastNew.botCell
    return (p && p.row === row && p.col === col) || (b && b.row === row && b.col === col)
  }

  function isWinner(row, col) {
    if (!winnerCells) return false
    return winnerCells.some(c => c.row === row && c.col === col)
  }

  return (
    <div className={`board-frame ${thinking ? 'board-thinking' : ''}`}>
      {/* arrow indicators */}
      <div className="col-arrows">
        {Array.from({ length: COLS }, (_, col) => (
          <div key={col} className="arrow-slot">
            {hoveredCol === col && !thinking && !gameOver && (
              <span className="col-arrow">▼</span>
            )}
          </div>
        ))}
      </div>

      <div className="board-inner">
        {Array.from({ length: COLS }, (_, col) => (
          <div
            key={col}
            className={`board-col ${hoveredCol === col && !thinking && !gameOver ? 'col-hovered' : ''}`}
            onClick={() => handleColClick(col)}
            onMouseEnter={() => setHoveredCol(col)}
            onMouseLeave={() => setHoveredCol(null)}
          >
            {Array.from({ length: ROWS }, (_, r) => {
              const row = ROWS - 1 - r  // top row first visually
              const value = grid[row]?.[col] ?? 0
              return (
                <Cell
                  key={row}
                  value={value}
                  isNew={isNew(row, col)}
                  row={row}
                  isWinner={isWinner(row, col)}
                />
              )
            })}
          </div>
        ))}
      </div>
    </div>
  )
}
