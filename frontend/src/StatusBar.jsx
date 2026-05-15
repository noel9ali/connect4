export default function StatusBar({ thinking, gameOver, winner, scores, onNewGame }) {
  function turnLabel() {
    if (gameOver) return null
    if (thinking) return <span className="turn-label bot-turn blink">BOT THINKING<AnimDots /></span>
    return <span className="turn-label player-turn">YOUR TURN</span>
  }

  function winText() {
    if (winner === 'player') return 'PLAYER WINS!'
    if (winner === 'bot') return 'BOT WINS!'
    return 'DRAW!'
  }

  return (
    <div className="status-bar">
      <div className="score-row">
        <div className="score-block">
          <div className="score-label">1UP</div>
          <div className="score-value player-color">{String(scores.player).padStart(4, '0')}</div>
        </div>
        <div className="game-title">CONNECT 4</div>
        <div className="score-block">
          <div className="score-label">BOT</div>
          <div className="score-value bot-color">{String(scores.bot).padStart(4, '0')}</div>
        </div>
      </div>

      <div className="turn-row">
        {gameOver ? (
          <div className="game-over-inline">
            <span className="winner-text rainbow">{winText()}</span>
            <button className="new-game-btn" onClick={onNewGame}>NEW GAME</button>
          </div>
        ) : turnLabel()}
      </div>
    </div>
  )
}

function AnimDots() {
  return <span className="anim-dots"><span>.</span><span>.</span><span>.</span></span>
}
