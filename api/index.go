// Package handler is the Vercel serverless entry point. /api/:route is
// rewritten to /api?route=:route (see vercel.json).
//
// The bot always plays a perfect game: early positions come from the opening
// book in Supabase (itself generated from exact solves), everything else is
// solved exactly by internal/c4. If the book is unreachable the solver is used
// for every move, so strength never depends on the book being available.
package handler

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	"connect4/internal/c4"
)

const (
	rows       = 6
	cols       = 7
	bookMaxMov = 20 // positions with more stones than this are not in the book
	// column 4 (index 3) is the only winning first move for the first player
	firstMove = 3
)

type boardData struct {
	CurrentPlayer uint64 `json:"current_player"`
	Mask          uint64 `json:"mask"`
	Turn          int    `json:"turn"`
	Heights       []int  `json:"heights"`
}

type state struct {
	Grid       [][]int   `json:"grid"`
	Turn       int       `json:"turn"`
	GameOver   bool      `json:"game_over"`
	Winner     *string   `json:"winner"`
	LastBotCol *int      `json:"last_bot_col"`
	BoardData  boardData `json:"board_data"`
}

func str(s string) *string { return &s }

func heights(mask uint64) []int {
	h := make([]int, cols)
	for c := 0; c < cols; c++ {
		h[c] = c * (rows + 1)
		for r := 0; r < rows && mask&(1<<uint(c*(rows+1)+r)) != 0; r++ {
			h[c]++
		}
	}
	return h
}

func toState(p c4.Pos, over bool, winner *string, botCol *int) state {
	turn := p.Moves()
	grid := make([][]int, rows)
	for r := range grid {
		grid[r] = make([]int, cols)
		for c := 0; c < cols; c++ {
			bit := uint(r + c*(rows+1))
			if p.Mask&(1<<bit) == 0 {
				continue
			}
			isCur := p.Cur&(1<<bit) != 0
			// The bot moves first: on even turns the bot is to move, so Cur is the bot's.
			if (turn%2 == 0) == isCur {
				grid[r][c] = 2
			} else {
				grid[r][c] = 1
			}
		}
	}
	return state{
		Grid: grid, Turn: turn, GameOver: over, Winner: winner, LastBotCol: botCol,
		BoardData: boardData{CurrentPlayer: p.Cur, Mask: p.Mask, Turn: turn, Heights: heights(p.Mask)},
	}
}

// bookMove asks Supabase for the stored move; ok=false on any miss or error.
func bookMove(p c4.Pos) (col int, ok bool) {
	base, key := os.Getenv("SUPABASE_URL"), os.Getenv("SUPABASE_ANON_KEY")
	if base == "" || key == "" || p.Moves() > bookMaxMov {
		return 0, false
	}
	url := fmt.Sprintf("%s/rest/v1/book?select=col&player=eq.%d&mask=eq.%d&limit=1", base, p.Cur, p.Mask)
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return 0, false
	}
	req.Header.Set("apikey", key)
	req.Header.Set("Authorization", "Bearer "+key)
	resp, err := (&http.Client{Timeout: 2 * time.Second}).Do(req)
	if err != nil {
		return 0, false
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, false
	}
	var out []struct {
		Col int `json:"col"`
	}
	if json.NewDecoder(io.LimitReader(resp.Body, 4096)).Decode(&out) != nil || len(out) == 0 {
		return 0, false
	}
	if !p.CanPlay(out[0].Col) {
		return 0, false
	}
	return out[0].Col, true
}

func botMove(p c4.Pos) int {
	if p.Mask == 0 {
		return firstMove
	}
	if col, ok := bookMove(p); ok {
		return col
	}
	return c4.NewSolver(22).BestMove(p)
}

func write(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(code)
	json.NewEncoder(w).Encode(v)
}

func fail(w http.ResponseWriter, code int, msg string) {
	write(w, code, map[string]string{"error": msg})
}

func terminal(p c4.Pos, botCol *int, mover string) (state, bool) {
	// p has the opponent of the last mover to move, so the last mover's stones are Cur^Mask.
	if c4.IsWin(p.Cur ^ p.Mask) {
		return toState(p, true, str(mover), botCol), true
	}
	if p.Moves() == c4.Cells {
		return toState(p, true, str("draw"), botCol), true
	}
	return state{}, false
}

func Handler(w http.ResponseWriter, r *http.Request) {
	switch r.URL.Query().Get("route") {
	case "health":
		write(w, 200, map[string]bool{"ok": true})
	case "new-game":
		if r.Method != http.MethodPost {
			fail(w, 405, "POST required")
			return
		}
		col := botMove(c4.Pos{})
		write(w, 200, toState(c4.Pos{}.Play(col), false, nil, &col))
	case "move":
		if r.Method != http.MethodPost {
			fail(w, 405, "POST required")
			return
		}
		var body struct {
			BoardState struct {
				BoardData boardData `json:"board_data"`
			} `json:"board_state"`
			Col int `json:"col"`
		}
		if json.NewDecoder(io.LimitReader(r.Body, 1<<16)).Decode(&body) != nil {
			fail(w, 400, "Invalid request")
			return
		}
		bd := body.BoardState.BoardData
		p := c4.Pos{Cur: bd.CurrentPlayer, Mask: bd.Mask}
		// Only a human-to-move position (odd stone count) is acceptable.
		if !p.Valid() || p.Moves()%2 != 1 || c4.IsWin(p.Cur^p.Mask) || !p.CanPlay(body.Col) {
			fail(w, 400, "Invalid move")
			return
		}
		p = p.Play(body.Col)
		if st, done := terminal(p, nil, "player"); done {
			write(w, 200, st)
			return
		}
		col := botMove(p)
		p = p.Play(col)
		if st, done := terminal(p, &col, "bot"); done {
			write(w, 200, st)
			return
		}
		write(w, 200, toState(p, false, nil, &col))
	default:
		fail(w, 404, "not found")
	}
}
