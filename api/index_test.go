package handler

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
)

func call(t *testing.T, route string, body any) map[string]any {
	var buf bytes.Buffer
	json.NewEncoder(&buf).Encode(body)
	req := httptest.NewRequest("POST", "/api?route="+route, &buf)
	rec := httptest.NewRecorder()
	Handler(rec, req)
	var out map[string]any
	json.Unmarshal(rec.Body.Bytes(), &out)
	if rec.Code != http.StatusOK {
		t.Logf("%s -> %d %v", route, rec.Code, out)
	}
	return out
}

// A human who always plays column 0..6 in turn must never beat the bot.
func TestBotNeverLoses(t *testing.T) {
	if os.Getenv("SUPABASE_URL") == "" {
		t.Skip("needs the Supabase opening book: without it the first moves take minutes to solve")
	}
	for first := 0; first < cols; first++ {
		st := call(t, "new-game", nil)
		for i := 0; ; i++ {
			if over, _ := st["game_over"].(bool); over {
				if st["winner"] == "player" {
					t.Fatalf("human beat the bot (start %d)", first)
				}
				break
			}
			col := (first + i*3) % cols
			next := call(t, "move", map[string]any{"board_state": st, "col": col})
			if next["error"] != nil { // full column: try the next one
				for c := 0; c < cols && next["error"] != nil; c++ {
					next = call(t, "move", map[string]any{"board_state": st, "col": c})
				}
			}
			st = next
		}
	}
}
