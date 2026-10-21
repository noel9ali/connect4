// Package c4 is an exact Connect 4 solver (negamax + alpha-beta, bitboards,
// threat-based move ordering, forced-move pruning, transposition table and a
// null-window search). It follows Pascal Pons' design (blog.gamesolver.org).
//
// Bitboard layout matches the Python Board: column c occupies bits
// c*7 .. c*7+5, with bit c*7+6 as an always-empty sentinel. `Cur` holds the
// stones of the player to move, `Mask` holds all stones.
package c4

import "math/bits"

const (
	Width  = 7
	Height = 6
	H1     = Height + 1
	Cells  = Width * Height
)

var (
	bottomMask uint64
	boardMask  uint64
	// columns searched centre-first
	colOrder = [Width]int{3, 2, 4, 1, 5, 0, 6}
)

func init() {
	for c := 0; c < Width; c++ {
		bottomMask |= 1 << (uint(c) * H1)
		boardMask |= ((1 << Height) - 1) << (uint(c) * H1)
	}
}

func colMask(c int) uint64  { return ((1 << Height) - 1) << (uint(c) * H1) }
func topMask(c int) uint64  { return 1 << (uint(Height-1) + uint(c)*H1) }
func bottomOf(c int) uint64 { return 1 << (uint(c) * H1) }

// Pos is a Connect 4 position.
type Pos struct {
	Cur, Mask uint64
}

func (p Pos) Moves() int { return bits.OnesCount64(p.Mask) }

func (p Pos) CanPlay(c int) bool { return c >= 0 && c < Width && p.Mask&topMask(c) == 0 }

// Play drops a piece for the player to move and returns the resulting
// position (with the opponent to move). The caller must check CanPlay.
func (p Pos) Play(c int) Pos {
	return Pos{Cur: p.Cur ^ p.Mask, Mask: p.Mask | (p.Mask + bottomOf(c))}
}

// Valid reports whether the position is structurally sound: Cur is a subset
// of Mask, every column is gravity-packed and within the board, and the stone
// counts are consistent with alternating play.
func (p Pos) Valid() bool {
	if p.Mask&^boardMask != 0 || p.Cur&^p.Mask != 0 {
		return false
	}
	for c := 0; c < Width; c++ {
		col := (p.Mask >> (uint(c) * H1)) & ((1 << Height) - 1)
		if col&(col+1) != 0 { // not of the form 0..01..1
			return false
		}
	}
	n := p.Moves()
	// Cur belongs to the player to move: they have placed floor(n/2) stones.
	return bits.OnesCount64(p.Cur) == n/2
}

// IsWin reports whether the given stone set contains four in a row.
func IsWin(pos uint64) bool {
	// horizontal
	m := pos & (pos >> H1)
	if m&(m>>(2*H1)) != 0 {
		return true
	}
	// diagonal \
	m = pos & (pos >> Height)
	if m&(m>>(2*Height)) != 0 {
		return true
	}
	// diagonal /
	m = pos & (pos >> (Height + 2))
	if m&(m>>(2*(Height+2))) != 0 {
		return true
	}
	// vertical
	m = pos & (pos >> 1)
	return m&(m>>2) != 0
}

// winningPosition returns the empty cells that would complete four in a row
// for `position`.
func winningPosition(position, mask uint64) uint64 {
	r := (position << 1) & (position << 2) & (position << 3)

	p := (position << H1) & (position << (2 * H1))
	r |= p & (position << (3 * H1))
	r |= p & (position >> H1)
	p = (position >> H1) & (position >> (2 * H1))
	r |= p & (position << H1)
	r |= p & (position >> (3 * H1))

	p = (position << Height) & (position << (2 * Height))
	r |= p & (position << (3 * Height))
	r |= p & (position >> Height)
	p = (position >> Height) & (position >> (2 * Height))
	r |= p & (position << Height)
	r |= p & (position >> (3 * Height))

	p = (position << (Height + 2)) & (position << (2 * (Height + 2)))
	r |= p & (position << (3 * (Height + 2)))
	r |= p & (position >> (Height + 2))
	p = (position >> (Height + 2)) & (position >> (2 * (Height + 2)))
	r |= p & (position << (Height + 2))
	r |= p & (position >> (3 * (Height + 2)))

	return r & (boardMask ^ mask)
}

func (p Pos) possible() uint64 { return (p.Mask + bottomMask) & boardMask }

func (p Pos) canWinNext() bool {
	return winningPosition(p.Cur, p.Mask)&p.possible() != 0
}

// possibleNonLosingMoves returns the playable cells that do not hand the
// opponent an immediate win; 0 means every move loses.
func (p Pos) possibleNonLosingMoves() uint64 {
	possible := p.possible()
	oppWin := winningPosition(p.Cur^p.Mask, p.Mask)
	forced := possible & oppWin
	if forced != 0 {
		if forced&(forced-1) != 0 {
			return 0 // two threats: cannot block both
		}
		possible = forced
	}
	return possible &^ (oppWin >> 1) // don't play under an opponent threat
}

func (p Pos) moveScore(move uint64) int {
	return bits.OnesCount64(winningPosition(p.Cur|move, p.Mask))
}

// Transposition table. Entries pack key<<8 | flag/score. The key (Cur+Mask)
// is unique per position and below 2^49, so the shift never overflows.
const (
	flagLower = 0x80
)

type Solver struct {
	table []uint64
	Nodes uint64
}

// NewSolver allocates a solver with 2^bitsize table entries.
func NewSolver(bitsize uint) *Solver {
	return &Solver{table: make([]uint64, 1<<bitsize)}
}

func (s *Solver) get(key uint64) (val byte, ok bool) {
	e := s.table[key&uint64(len(s.table)-1)]
	if e>>8 == key {
		return byte(e), true
	}
	return 0, false
}

func (s *Solver) put(key uint64, val byte) {
	s.table[key&uint64(len(s.table)-1)] = key<<8 | uint64(val)
}

func (s *Solver) negamax(p Pos, alpha, beta int) int {
	s.Nodes++
	moves := p.Moves()

	possible := p.possibleNonLosingMoves()
	if possible == 0 {
		return -(Cells - moves) / 2
	}
	if moves >= Cells-2 {
		return 0
	}

	min := -(Cells - 2 - moves) / 2
	if alpha < min {
		alpha = min
		if alpha >= beta {
			return alpha
		}
	}
	max := (Cells - 1 - moves) / 2
	if beta > max {
		beta = max
		if alpha >= beta {
			return beta
		}
	}

	key := p.Cur + p.Mask
	if v, ok := s.get(key); ok {
		sc := int(v&0x7f) - 32
		if v&flagLower != 0 {
			if alpha < sc {
				alpha = sc
			}
		} else if beta > sc {
			beta = sc
		}
		if alpha >= beta {
			return sc
		}
	}

	// order moves: highest threat count first, centre-first on ties
	var mv [Width]uint64
	var sc [Width]int
	n := 0
	for i := Width - 1; i >= 0; i-- {
		m := possible & colMask(colOrder[i])
		if m == 0 {
			continue
		}
		score := p.moveScore(m)
		j := n
		for j > 0 && sc[j-1] > score {
			mv[j], sc[j] = mv[j-1], sc[j-1]
			j--
		}
		mv[j], sc[j] = m, score
		n++
		_ = i
	}

	for i := n - 1; i >= 0; i-- {
		child := Pos{Cur: p.Cur ^ p.Mask, Mask: p.Mask | mv[i]}
		score := -s.negamax(child, -beta, -alpha)
		if score >= beta {
			s.put(key, byte(score+32)|flagLower)
			return score
		}
		if score > alpha {
			alpha = score
		}
	}
	s.put(key, byte(alpha+32))
	return alpha
}

// Solve returns the exact game-theoretic score for the player to move:
// >0 win (larger = faster), 0 draw, <0 loss. Score magnitude is the number of
// the player's remaining stones when the game ends, per Pons' convention.
func (s *Solver) Solve(p Pos) int {
	if p.canWinNext() {
		return (Cells + 1 - p.Moves()) / 2
	}
	min := -(Cells - p.Moves()) / 2
	max := (Cells + 1 - p.Moves()) / 2
	for min < max {
		med := min + (max-min)/2
		if med <= 0 && min/2 < med {
			med = min / 2
		} else if med >= 0 && max/2 > med {
			med = max / 2
		}
		r := s.negamax(p, med, med+1)
		if r <= med {
			max = r
		} else {
			min = r
		}
	}
	return min
}

// BestMove returns a column that is optimal for the player to move, i.e. one
// that preserves the best achievable game-theoretic result and, among those,
// wins fastest (or loses slowest). Returns -1 if the board is full.
func (s *Solver) BestMove(p Pos) int {
	best, bestCol := -1<<30, -1
	for _, c := range colOrder {
		if !p.CanPlay(c) {
			continue
		}
		child := p.Play(c)
		var score int
		if IsWin(child.Cur ^ child.Mask) { // mover just completed four
			score = Cells // beats any non-immediate result
		} else {
			score = -s.Solve(child)
		}
		if score > best {
			best, bestCol = score, c
		}
	}
	return bestCol
}

// SolveWeak returns only the sign of the result for the player to move:
// 1 win, 0 draw, -1 loss. It is much faster than Solve.
func (s *Solver) SolveWeak(p Pos) int {
	if p.canWinNext() {
		return 1
	}
	r := s.negamax(p, -1, 1)
	switch {
	case r > 0:
		return 1
	case r < 0:
		return -1
	}
	return 0
}

// BestMoveWeak returns a move that keeps a forced win if one exists (not
// necessarily the fastest), otherwise falls back to the exact BestMove.
func (s *Solver) BestMoveWeak(p Pos) int {
	for _, c := range colOrder {
		if !p.CanPlay(c) {
			continue
		}
		child := p.Play(c)
		if IsWin(child.Cur^child.Mask) || -s.SolveWeak(child) > 0 {
			return c
		}
	}
	return s.BestMove(p)
}
