import { useState, useEffect, useCallback } from 'react'
import Board from './Board'
import StatusBar from './StatusBar'
import { useSound } from './useSound'
import './index.css'

const ROWS = 6
const COLS = 7

function emptyGrid() {
  return Array.from({ length: ROWS }, () => Array(COLS).fill(0))
}

function findWinnerCells(grid) {
  const dirs = [[0,1],[1,0],[1,1],[1,-1]]
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const v = grid[r][c]
      if (!v) continue
      for (const [dr, dc] of dirs) {
        const cells = [[r, c]]
        for (let k = 1; k < 4; k++) {
          const nr = r + dr * k, nc = c + dc * k
          if (nr < 0 || nr >= ROWS || nc < 0 || nc >= COLS || grid[nr][nc] !== v) break
          cells.push([nr, nc])
        }
        if (cells.length === 4) return cells.map(([row, col]) => ({ row, col }))
      }
    }
  }
  return null
}

function findLowestEmpty(grid, col) {
  for (let row = 0; row < ROWS; row++) {
    if (!grid[row][col]) return row
  }
  return null
}

export default function App() {
  const [boardState, setBoardState] = useState(null)
  const [displayGrid, setDisplayGrid] = useState(emptyGrid())
  const [thinking, setThinking] = useState(false)
  const [gameOver, setGameOver] = useState(false)
  const [winner, setWinner] = useState(null)
  const [winnerCells, setWinnerCells] = useState(null)
  const [scores, setScores] = useState({ player: 0, bot: 0 })
  const [lastNew, setLastNew] = useState(null)
  const [flashCols, setFlashCols] = useState([])
  const sound = useSound()

  const startNewGame = useCallback(async () => {
    setGameOver(false)
    setWinner(null)
    setWinnerCells(null)
    setLastNew(null)
    setThinking(true)
    setDisplayGrid(emptyGrid())
    const res = await fetch('/api/new-game', { method: 'POST' })
    const data = await res.json()
    setBoardState(data)
    setDisplayGrid(data.grid)
    if (data.last_bot_col !== null) {
      const botRow = findLowestEmpty(emptyGrid(), data.last_bot_col)
      setLastNew({ playerCell: null, botCell: { row: botRow, col: data.last_bot_col } })
      sound.playBotMove()
    }
    setThinking(false)
  }, [])

  useEffect(() => { startNewGame() }, [])

  async function handleColClick(col) {
    if (thinking || gameOver || !boardState) return

    const prevGrid = displayGrid.map(r => [...r])
    const playerRow = findLowestEmpty(prevGrid, col)

    if (playerRow === null) {
      setFlashCols(f => [...f, col])
      setTimeout(() => setFlashCols(f => f.filter(c => c !== col)), 500)
      return
    }

    // optimistic update — player piece
    const optimisticGrid = prevGrid.map(r => [...r])
    optimisticGrid[playerRow][col] = 1
    setDisplayGrid(optimisticGrid)
    setLastNew({ playerCell: { row: playerRow, col }, botCell: null })
    sound.playDrop()
    setThinking(true)

    try {
      const res = await fetch('/api/move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ board_state: boardState, col })
      })
      const data = await res.json()

      if (data.error) {
        setDisplayGrid(prevGrid)
        setThinking(false)
        return
      }

      setBoardState(data)

      if (data.game_over && data.winner === 'player') {
        setDisplayGrid(data.grid)
        const wc = findWinnerCells(data.grid)
        setWinnerCells(wc)
        setWinner('player')
        setGameOver(true)
        setScores(s => ({ ...s, player: s.player + 1 }))
        sound.playWin()
        setThinking(false)
        return
      }

      if (data.game_over && data.winner === 'draw' && data.last_bot_col === null) {
        setDisplayGrid(data.grid)
        setWinner('draw')
        setGameOver(true)
        sound.playDraw()
        setThinking(false)
        return
      }

      // Animate bot piece
      const botCol = data.last_bot_col
      const botRow = botCol !== null ? findLowestEmpty(optimisticGrid, botCol) : null

      // small delay to let player animation finish before bot appears
      setTimeout(() => {
        setDisplayGrid(data.grid)
        if (botRow !== null && botCol !== null) {
          setLastNew({ playerCell: { row: playerRow, col }, botCell: { row: botRow, col: botCol } })
          sound.playBotMove()
        }
        setThinking(false)

        if (data.game_over) {
          const wc = findWinnerCells(data.grid)
          setWinnerCells(wc)
          setWinner(data.winner)
          setGameOver(true)
          if (data.winner === 'bot') {
            setScores(s => ({ ...s, bot: s.bot + 1 }))
            sound.playDraw()
          } else {
            sound.playDraw()
          }
        }
      }, 350)
    } catch {
      setDisplayGrid(prevGrid)
      setThinking(false)
    }
  }

  return (
    <div className="app">
      <StatusBar
        thinking={thinking}
        gameOver={gameOver}
        winner={winner}
        scores={scores}
        onNewGame={startNewGame}
      />
      <Board
        grid={displayGrid}
        onColClick={handleColClick}
        thinking={thinking}
        gameOver={gameOver}
        winnerCells={winnerCells}
        lastNew={lastNew}
        flashCols={flashCols}
      />
    </div>
  )
}
