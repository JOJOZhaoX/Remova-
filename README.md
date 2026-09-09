# Remevahe

> Capture the moment. Keep what is real.

Remevahe is a minimal prototype for personal memory capture. The first version focuses on one simple action: write down a moment and revisit it on today's timeline.

## Current version

- Local web interface
- Text notes
- Automatic timestamps
- SQLite persistence
- Today timeline
- `/health` health-check endpoint

AI analysis, photos, video, accounts, cloud sync, and semantic search are intentionally out of scope for this first version. They will be added gradually after the core loop is stable.

## Run locally

```bash
python3 app.py
```

Open <http://127.0.0.1:8000> in your browser.

Data is stored locally in `remevahe.db` and is not uploaded to the cloud.

## API

```text
GET  /health
GET  /api/notes
POST /api/notes  {"content":"Finished the first prototype today"}
```
