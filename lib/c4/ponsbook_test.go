package c4

import (
	"math/rand"
	"testing"
)

// The Pons book's move must keep the same game-theoretic result as the solver.
func TestPonsBookAgreesWithSolver(t *testing.T) {
	b, err := LoadPonsBook("../../data/7x6.book")
	if err != nil {
		t.Skip(err)
	}
	rng := rand.New(rand.NewSource(11))
	s := NewSolver(22)
	checked := 0
	for checked < 40 {
		p, ok := randomPos(rng, 10+rng.Intn(4))
		if !ok {
			continue
		}
		col, ok := b.WinningMove(p)
		if !ok {
			continue
		}
		ch := p.Play(col)
		after := 1
		if !IsWin(ch.Cur ^ ch.Mask) {
			after = -s.SolveWeak(ch)
		}
		if want := s.SolveWeak(p); after != want {
			t.Fatalf("book move %d on %+v gives %d, solver says %d", col, p, after, want)
		}
		checked++
	}
}
