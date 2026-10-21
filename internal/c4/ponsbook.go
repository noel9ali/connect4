package c4

import (
	"fmt"
	"os"
)

// PonsBook reads Pascal Pons' precomputed opening book (7x6.book), which
// stores the exact score of every position with at most Depth stones.
type PonsBook struct {
	Depth    int
	size     uint64
	keyBytes int
	keys     []byte
	values   []byte
}

func isPrime(n uint64) bool {
	if n < 2 {
		return false
	}
	for i := uint64(2); i*i <= n; i++ {
		if n%i == 0 {
			return false
		}
	}
	return true
}

func LoadPonsBook(path string) (*PonsBook, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	if len(raw) < 6 || raw[0] != Width || raw[1] != Height || raw[3] != 1 || raw[4] != 1 {
		return nil, fmt.Errorf("unsupported book header")
	}
	size := uint64(1) << raw[5]
	for !isPrime(size) {
		size++
	}
	if uint64(len(raw)) != 6+2*size {
		return nil, fmt.Errorf("book size mismatch")
	}
	return &PonsBook{Depth: int(raw[2]), size: size, keyBytes: 1, keys: raw[6 : 6+size], values: raw[6+size:]}, nil
}

func encodeKey3(p Pos, rev bool) uint64 {
	var key uint64
	for i := 0; i < Width; i++ {
		c := i
		if rev {
			c = Width - 1 - i
		}
		pos := bottomOf(c)
		for pos&p.Mask != 0 {
			key *= 3
			if pos&p.Cur != 0 {
				key++
			} else {
				key += 2
			}
			pos <<= 1
		}
		key *= 3
	}
	return key
}

// key3 is Pons' mirror-invariant base-3 position key.
func key3(p Pos) uint64 {
	a, b := encodeKey3(p, false), encodeKey3(p, true)
	if b < a {
		a = b
	}
	return a / 3
}

func (b *PonsBook) lookup(p Pos) int {
	k := key3(p)
	i := k % b.size
	if uint64(b.keys[i]) == k&0xff {
		return int(b.values[i])
	}
	return 0
}

// scoreOffset: a stored value is the exact score plus this constant
// (verified against the solver), so values below it are losses for the player
// to move in that child position.
const scoreOffset = 19

// WinningMove returns a column that provably wins for the player to move,
// using only what the book stores: an immediate win, or a child position the
// book records as lost for the opponent. ok=false means the book cannot
// certify a win (a gap), not that none exists.
func (b *PonsBook) WinningMove(p Pos) (col int, ok bool) {
	if p.Moves()+1 > b.Depth {
		return 0, false
	}
	best, bestCol := scoreOffset, -1
	for _, c := range colOrder {
		if !p.CanPlay(c) {
			continue
		}
		child := p.Play(c)
		if IsWin(child.Cur ^ child.Mask) {
			return c, true
		}
		if raw := b.lookup(child); raw != 0 && raw < best {
			best, bestCol = raw, c
		}
	}
	return bestCol, bestCol >= 0
}
