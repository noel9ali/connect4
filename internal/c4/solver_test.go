package c4

import (
	"math/rand"
	"testing"
)

// naive reference: plain memoised minimax returning +1 / 0 / -1 for the
// player to move. Shares only the bit layout with the real solver.
func naive(p Pos, memo map[Pos]int) int {
	if v, ok := memo[p]; ok {
		return v
	}
	best, any := -2, false
	for c := 0; c < Width; c++ {
		if !p.CanPlay(c) {
			continue
		}
		any = true
		ch := p.Play(c)
		var v int
		if IsWin(ch.Cur ^ ch.Mask) {
			v = 1
		} else {
			v = -naive(ch, memo)
		}
		if v > best {
			best = v
		}
		if best == 1 {
			break
		}
	}
	if !any {
		best = 0
	}
	memo[p] = best
	return best
}

func randomPos(rng *rand.Rand, stones int) (Pos, bool) {
	p := Pos{}
	for i := 0; i < stones; i++ {
		var legal []int
		for c := 0; c < Width; c++ {
			if p.CanPlay(c) {
				legal = append(legal, c)
			}
		}
		if len(legal) == 0 {
			return p, false
		}
		p = p.Play(legal[rng.Intn(len(legal))])
		if IsWin(p.Cur ^ p.Mask) {
			return p, false
		}
	}
	return p, true
}

func TestAgainstNaive(t *testing.T) {
	rng := rand.New(rand.NewSource(1))
	s := NewSolver(20)
	checked := 0
	for checked < 60 {
		p, ok := randomPos(rng, 22+rng.Intn(8))
		if !ok || !p.Valid() {
			continue
		}
		want := naive(p, map[Pos]int{})
		got := s.Solve(p)
		sign := 0
		if got > 0 {
			sign = 1
		} else if got < 0 {
			sign = -1
		}
		if sign != want {
			t.Fatalf("pos %+v: solver %d, naive %d", p, got, want)
		}
		// the chosen move must preserve the game-theoretic result
		c := s.BestMove(p)
		ch := p.Play(c)
		var after int
		if IsWin(ch.Cur ^ ch.Mask) {
			after = 1
		} else {
			after = -naive(ch, map[Pos]int{})
		}
		if after != want {
			t.Fatalf("pos %+v: best move %d gives %d, expected %d", p, c, after, want)
		}
		checked++
	}
}

func TestKnownOpening(t *testing.T) {
	// 1. d1 2. d2 3. d3 ... a 14-stone position: solver must agree with itself
	// across table sizes (guards against table corruption).
	rng := rand.New(rand.NewSource(7))
	for i := 0; i < 5; {
		p, ok := randomPos(rng, 18)
		if !ok {
			continue
		}
		a := NewSolver(10).Solve(p)
		b := NewSolver(22).Solve(p)
		if a != b {
			t.Fatalf("table-size dependent result %d vs %d for %+v", a, b, p)
		}
		i++
	}
}
