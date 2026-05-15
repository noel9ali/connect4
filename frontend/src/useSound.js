export function useSound() {
  function ctx() {
    return new (window.AudioContext || window.webkitAudioContext)()
  }

  function tone(ac, type, freqStart, freqEnd, duration, startTime = 0, gain = 0.3) {
    const osc = ac.createOscillator()
    const g = ac.createGain()
    osc.connect(g)
    g.connect(ac.destination)
    osc.type = type
    osc.frequency.setValueAtTime(freqStart, ac.currentTime + startTime)
    osc.frequency.exponentialRampToValueAtTime(freqEnd, ac.currentTime + startTime + duration)
    g.gain.setValueAtTime(gain, ac.currentTime + startTime)
    g.gain.exponentialRampToValueAtTime(0.001, ac.currentTime + startTime + duration)
    osc.start(ac.currentTime + startTime)
    osc.stop(ac.currentTime + startTime + duration)
  }

  function playDrop() {
    const ac = ctx()
    tone(ac, 'square', 440, 220, 0.08)
  }

  function playBotMove() {
    const ac = ctx()
    tone(ac, 'sawtooth', 330, 165, 0.08)
  }

  function playWin() {
    const ac = ctx()
    const notes = [261.63, 329.63, 392.0, 523.25]
    notes.forEach((freq, i) => tone(ac, 'square', freq, freq, 0.1, i * 0.1, 0.25))
  }

  function playDraw() {
    const ac = ctx()
    tone(ac, 'triangle', 300, 150, 0.3)
    tone(ac, 'triangle', 240, 120, 0.3, 0.05, 0.2)
  }

  return { playDrop, playBotMove, playWin, playDraw }
}
