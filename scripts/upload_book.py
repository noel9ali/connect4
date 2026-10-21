"""Upload the early-game part of data/opening_book.db to Supabase.

Usage (PowerShell):
    py -m pip install "psycopg[binary]"
    $env:SUPABASE_DB_URL = "postgresql://postgres:<password>@db.iqyqwsqtpvkrbuoaaqch.supabase.co:5432/postgres"
    py scripts/upload_book.py [max_stones | path/to/book.csv]   (CSV from: go run ./cmd/genbook)

Only positions with at most `max_stones` stones (default 20) are uploaded; the
Go solver in internal/c4 solves everything deeper exactly in milliseconds.
The script is idempotent: existing rows are skipped.
"""
import os
import sqlite3
import sys

import psycopg

ENV = os.path.join(os.path.dirname(__file__), "..", ".env")
if "SUPABASE_DB_URL" not in os.environ and os.path.exists(ENV):
    for line in open(ENV):
        k, sep, v = line.strip().partition("=")
        if sep and not k.startswith("#"):
            os.environ.setdefault(k, v)

ARG = sys.argv[1] if len(sys.argv) > 1 else "20"
CSV = ARG if ARG.endswith(".csv") else None
MAX_STONES = 20 if CSV else int(ARG)
SRC = os.path.join(os.path.dirname(__file__), "..", "data", "opening_book.db")

src = sqlite3.connect(f"file:{SRC}?mode=ro", uri=True)
pg = psycopg.connect(os.environ["SUPABASE_DB_URL"])

if CSV:
    import csv
    reader = csv.reader(open(CSV))
    next(reader)
    rows = ((int(p), int(m), int(c)) for p, m, c in reader)
else:
    rows = ((p, m, c) for p, m, c in src.execute("SELECT player, mask, col FROM book")
            if m.bit_count() <= MAX_STONES)

with pg.cursor() as cur:
    cur.execute("CREATE TEMP TABLE staging (player bigint, mask bigint, col smallint) ON COMMIT DROP")
    with cur.copy("COPY staging (player, mask, col) FROM STDIN") as copy:
        n = 0
        for row in rows:
            copy.write_row(row)
            n += 1
            if n % 100_000 == 0:
                print(f"{n:,} rows staged", flush=True)
    cur.execute("INSERT INTO public.book SELECT * FROM staging ON CONFLICT DO NOTHING")
    print(f"inserted {cur.rowcount:,} of {n:,} rows")
pg.commit()
