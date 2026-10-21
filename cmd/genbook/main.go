// genbook builds the complete early-game opening book: for every position the
// bot can face (bot to move, at most maxStones stones, after any sequence of
// human replies) it stores a move that keeps the bot's forced win.
// Only positions the Pons book can certify are stored; the rest are gaps that
// the live solver covers.
//
//	go run ./cmd/genbook [maxStones] > data/early_book.csv   (progress on stderr)
package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"sync"
	"time"

	"connect4/lib/c4"
)

type entry struct {
	pos c4.Pos
	col int
}

func main() {
	maxStones := 12
	if len(os.Args) > 1 {
		maxStones, _ = strconv.Atoi(os.Args[1])
	}
	pons, err := c4.LoadPonsBook("data/7x6.book")
	if err != nil {
		fmt.Fprintln(os.Stderr, "pons book:", err)
		os.Exit(1)
	}
	out := bufio.NewWriter(os.Stdout)
	defer out.Flush()
	fmt.Fprintln(out, "player,mask,col")

	level := map[c4.Pos]struct{}{{}: {}}
	for stones := 0; stones <= maxStones; stones += 2 {
		start := time.Now()
		todo := make(chan c4.Pos)
		results := make(chan entry)
		var wg sync.WaitGroup
		for w := 0; w < 16; w++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				for p := range todo {
					col, ok := pons.WinningMove(p)
					if !ok {
						col = -1 // gap: not certifiable from the Pons book
					}
					results <- entry{p, col}
				}
			}()
		}
		go func() {
			for p := range level {
				todo <- p
			}
			close(todo)
			wg.Wait()
			close(results)
		}()

		next := map[c4.Pos]struct{}{}
		gaps := 0
		for e := range results {
			if e.col < 0 {
				gaps++
				continue
			}
			fmt.Fprintf(out, "%d,%d,%d\n", e.pos.Cur, e.pos.Mask, e.col)
			after := e.pos.Play(e.col)
			if c4.IsWin(after.Cur^after.Mask) || after.Moves() == c4.Cells {
				continue
			}
			for c := 0; c < c4.Width; c++ {
				if !after.CanPlay(c) {
					continue
				}
				reply := after.Play(c)
				if c4.IsWin(reply.Cur^reply.Mask) || reply.Moves() == c4.Cells {
					continue
				}
				next[reply] = struct{}{}
			}
		}
		fmt.Fprintf(os.Stderr, "stones=%d positions=%d took=%v\n", stones, len(level), time.Since(start).Round(time.Second))
		level = next
	}
}
