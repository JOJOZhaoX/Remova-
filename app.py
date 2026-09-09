from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).parent
DB_PATH = ROOT / "remevahe.db"

HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Remevahe</title>
  <style>
    :root { color-scheme: light; font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    body { margin:0; background:#f5f4f0; color:#252525; }
    main { max-width:720px; margin:0 auto; padding:36px 20px 80px; }
    header { display:flex; justify-content:space-between; align-items:end; margin-bottom:28px; }
    h1 { margin:0; font-size:30px; letter-spacing:-.04em; }
    .tagline { color:#817e77; margin-top:7px; font-size:14px; }
    time { color:#817e77; font-size:13px; }
    form { background:#fff; border:1px solid #e6e2da; border-radius:18px; padding:16px; box-shadow:0 8px 24px #2420190b; }
    textarea { width:100%; box-sizing:border-box; resize:vertical; min-height:86px; border:0; outline:0; font:inherit; color:inherit; }
    button { border:0; border-radius:999px; background:#252525; color:white; padding:10px 18px; cursor:pointer; font-size:14px; }
    button:disabled { opacity:.5; cursor:wait; }
    .form-footer { display:flex; justify-content:space-between; align-items:center; color:#9a968f; font-size:12px; }
    #timeline { margin-top:30px; }
    .empty { color:#9a968f; text-align:center; padding:50px 0; }
    .event { position:relative; padding:0 0 24px 25px; border-left:1px solid #d8d3ca; }
    .event::before { content:""; position:absolute; left:-5px; top:4px; width:9px; height:9px; border-radius:50%; background:#252525; }
    .event time { display:block; margin-bottom:6px; }
    .event p { margin:0; background:#fff; border:1px solid #e6e2da; border-radius:14px; padding:14px 16px; line-height:1.55; }
    .count { color:#817e77; font-size:13px; margin-bottom:14px; }
  </style>
</head>
<body>
  <main>
    <header>
      <div><h1>Remevahe</h1><div class="tagline">Capture the moment. Keep what is real.</div></div>
      <time id="today"></time>
    </header>
    <form id="note-form">
      <textarea id="note" maxlength="1000" placeholder="What is worth keeping from this moment?"></textarea>
      <div class="form-footer"><span id="length">0 / 1000</span><button id="save" type="submit">Save this moment</button></div>
    </form>
    <section id="timeline"></section>
  </main>
  <script>
    const note = document.querySelector("#note");
    const timeline = document.querySelector("#timeline");
    const length = document.querySelector("#length");
    document.querySelector("#today").textContent = new Intl.DateTimeFormat("en-US",{month:"short",day:"numeric"}).format(new Date());
    note.addEventListener("input", () => length.textContent = `${note.value.length} / 1000`);
    function escapeHtml(value) { const div = document.createElement("div"); div.textContent = value; return div.innerHTML; }
    function formatTime(value) { return new Date(value).toLocaleTimeString("en-US",{hour:"2-digit",minute:"2-digit"}); }
    async function loadNotes() {
      const response = await fetch("/api/notes");
      const notes = await response.json();
      if (!notes.length) { timeline.innerHTML = "<div class="empty">No notes yet. Save your first moment today.</div>"; return; }
      timeline.innerHTML = `<div class="count">Today · ${notes.length} note(s)</div>` + notes.map(item =>
        `<article class="event"><time>${formatTime(item.created_at)}</time><p>${escapeHtml(item.content)}</p></article>`
      ).join("");
    }
    document.querySelector("#note-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const content = note.value.trim(); if (!content) return;
      const button = document.querySelector("#save"); button.disabled = true;
      await fetch("/api/notes", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({content})});
      note.value = ""; length.textContent = "0 / 1000"; button.disabled = false; await loadNotes();
    });
    loadNotes();
  </script>
</body>
</html>"""

def init_db() -> None:
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

def notes_for_today() -> list[dict[str, str | int]]:
    today = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT id, content, created_at FROM notes WHERE created_at LIKE ? ORDER BY created_at DESC",
            (f"{today}%",),
        ).fetchall()
    return [dict(row) for row in rows]

class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            data = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path == "/api/notes":
            self.send_json(notes_for_today())
        elif path == "/health":
            self.send_json({"status": "ok", "name": "remevahe"})
        else:
            self.send_json({"error": "not_found"}, 404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/notes":
            self.send_json({"error": "not_found"}, 404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(size))
            content = str(payload.get("content", "")).strip()
            if not content or len(content) > 1000:
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            self.send_json({"error": "content_required"}, 400)
            return
        created_at = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(DB_PATH) as db:
            cursor = db.execute("INSERT INTO notes (content, created_at) VALUES (?, ?)", (content, created_at))
            note_id = cursor.lastrowid
        self.send_json({"id": note_id, "content": content, "created_at": created_at}, 201)

    def log_message(self, format: str, *args: object) -> None:
        return

if __name__ == "__main__":
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Remevahe running at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
