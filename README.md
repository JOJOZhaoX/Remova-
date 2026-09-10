# Remeva

> Capture the moment. Keep what is real.

Remeva is a minimal prototype for personal memory capture. Capture a moment in words or a photo, revisit it on today's timeline, and add comments later.

## Current version

- Local web interface
- Text notes
- Up to six photos per moment, with individual previews and removal (JPEG, PNG or WebP, up to 5 MB each)
- Comments on individual moments
- Automatic timestamps
- SQLite persistence
- Today timeline
- All moments view with keyword search across notes and comments
- Optional moods, editable after saving, with mood filtering
- ZIP export containing original photos, portable JSON, and a complete SQLite backup
- Date picker, previous/next day navigation, and a Today shortcut
- Edit moment text while preserving its timestamp, photo, and comments
- Soft delete with an Undo button (available until the page is refreshed)
- Click photos to view them at full size and move between photos
- `/health` health-check endpoint

AI analysis, video, accounts, cloud sync, and semantic search are currently out of scope.

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
GET  /api/notes?date=2026-09-09
GET  /api/notes?view=all&q=walk&mood=calm
GET  /api/backup
POST /api/notes  {"content":"Finished the first prototype today"}
POST /api/comments  {"note_id":1,"content":"A thought to revisit"}
POST /api/notes/edit  {"note_id":1,"content":"Updated text"}
POST /api/notes/delete  {"note_id":1}
POST /api/notes/restore  {"note_id":1}
```

Notes accept an `images` array of JPEG, PNG or WebP data URLs. The legacy single `image` field is also supported. A moment must contain text or at least one photo. The optional `mood` field accepts `calm`, `happy`, `grateful`, `sad`, `tired`, `anxious`, or an empty string. Photos, moods and comments are stored in the local SQLite database alongside notes. Existing single-photo records migrate automatically.

## Backup and restore

Click **Export backup** to download the complete collection, regardless of the selected date or filters. The ZIP includes `moments.json`, original images in `photos/`, `remevahe.db`, and restore instructions. Soft-deleted moments are included and marked as deleted.

To restore, stop the app, keep a copy of the current database, replace `remevahe.db` with the archived database, and restart. This replaces the current collection; there is no in-app import or merge yet. Keep backups private, since they contain the journal and original photos.

## Verification

```bash
python3 -m unittest -v test_app
```

Tests use a temporary database to check legacy migration, multiple photos, comment search, moods, soft delete/restore, input validation, and backup integrity. The prototype loads matching records in one response; pagination is a future improvement for large libraries.
