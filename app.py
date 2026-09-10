from __future__ import annotations

import json
import base64
import binascii
import sqlite3
import io
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ROOT = Path(__file__).parent
DB_PATH = ROOT / "remevahe.db"
MOODS = ('', 'calm', 'happy', 'grateful', 'sad', 'tired', 'anxious')


def validate_images(images):
    if not isinstance(images, list) or len(images) > 6:
        raise ValueError
    for image in images:
        if not isinstance(image, str):
            raise ValueError
        prefix, encoded = image.split(',', 1)
        raw = base64.b64decode(encoded, validate=True)
        valid = (prefix == 'data:image/png;base64' and raw.startswith(b'\x89PNG\r\n\x1a\n')) or (prefix == 'data:image/jpeg;base64' and raw.startswith(b'\xff\xd8\xff')) or (prefix == 'data:image/webp;base64' and raw.startswith(b'RIFF') and raw[8:12] == b'WEBP')
        if not valid or len(raw) > 5 * 1024 * 1024:
            raise ValueError
    return images


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Remeva ｜ 存真</title>
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
    .photo { display:block; max-width:100%; max-height:360px; border-radius:12px; margin:12px 0; object-fit:contain; }
    [hidden] { display:none !important; }
    .secondary { background:#ece9e2; color:#45423b; }
    .attachments { margin:8px 0 16px; }
    .photo-add { display:inline-flex; align-items:center; gap:7px; background:#f4f3ef; color:#68645c; padding:7px 11px; font-size:12px; border:1px solid #e9e6df; }
    .photo-add svg { width:15px; height:15px; }
    #remove-photo { padding:6px 10px; font-size:12px; }
    button:focus-visible, summary:focus-visible { outline:2px solid #85816e; outline-offset:3px; }
    button { transition:background .15s,color .15s; }
    .secondary:hover, .photo-add:hover { background:#e5e1d8; }
    details { margin-top:12px; }
    summary { cursor:pointer; color:#666158; font-size:14px; padding:8px 0; }
    .comment-form { margin-top:10px; padding:12px; box-shadow:none; }
    .comment-form textarea { min-height:48px; }
    .comment { margin:8px 0; padding-left:12px; border-left:2px solid #d8d3ca; white-space:pre-wrap; }
    .event p { white-space:pre-wrap; overflow-wrap:anywhere; }
    #status { color:#9a3e30; font-size:13px; }
    #status:empty { display:none; }
    .date-nav { display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top:26px; }
    input[type=date] { font:inherit; padding:8px; border:1px solid #d8d3ca; border-radius:8px; background:white; }
    .note-actions { display:flex; gap:4px; margin-top:8px; justify-content:flex-end; }
    .note-actions button { background:transparent; color:#827d74; font-size:12px; padding:6px 10px; border-radius:7px; }
    .note-actions button:hover { background:#eae7e0; color:#34312c; }
    .note-actions button[data-action=delete]:hover { background:#f1e5e0; color:#9a4937; }
    .event > details { margin-top:0; }
    .event > details > summary { font-size:12px; color:#827d74; }
    .event > time { margin-bottom:10px; }
    .date-nav button { font-size:12px; padding:8px 12px; }
    @media(max-width:420px) { main { padding:26px 16px 60px; } h1 { font-size:26px; } .tagline { font-size:12px; } }
    dialog { border:1px solid #d8d3ca; border-radius:18px; padding:22px; max-width: min(680px,85vw); }
    dialog::backdrop { background:#0009; } dialog img { max-width:100%; max-height:75vh; }
    #edit-dialog { width:560px; } #undo-list { margin-top:16px; }
    .photo-button { display:block; background:none; padding:0; cursor:zoom-in; }
    .browse-bar, .filters, .capture-tools, .viewer-nav { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
    .browse-bar { margin-top:28px; } .browse-bar button, .export-link { font-size:12px; padding:8px 12px; }
    .browse-bar button[aria-pressed=true] { background:#252525; color:white; }
    .export-link { margin-left:auto; color:#777268; text-decoration:none; }
    .filters { margin-top:14px; } .filters input { flex:1; min-width:140px; }
    select, input[type=search] { font:inherit; font-size:12px; border:1px solid #e3dfd6; border-radius:9px; padding:9px; background:#fcfbf8; color:#615c53; }
    .gallery, #photo-previews { display:grid; grid-template-columns:repeat(auto-fit,minmax(100px,1fr)); gap:8px; margin:12px 0; }
    .gallery .photo { width:100%; height:140px; object-fit:cover; margin:0; }
    .gallery .photo-button:only-child .photo { height:auto; max-height:360px; object-fit:contain; }
    .preview-tile { position:relative; } .preview-tile img { width:100%; height:90px; object-fit:cover; border-radius:9px; }
    .preview-tile button { position:absolute; top:4px; right:4px; padding:4px 8px; font-size:12px; }
    .mood-tag { display:inline-block; font-size:11px; color:#77705d; background:#ece9df; padding:4px 8px; border-radius:12px; margin-bottom:8px; }
    .viewer-nav { justify-content:space-between; margin:10px 0; } .viewer-nav button { padding:7px 12px; font-size:12px; }
    #photo-previews:empty { display:none; } #export-status { font-size:12px; color:#777268; }
  </style>
</head>
<body>
  <main>
    <header>
      <div><h1>Remeva ｜ 存真</h1><div class="tagline">Capture the moment. Keep what is real.</div></div>
      <time id="today"></time>
    </header>
    <form id="note-form">
      <textarea id="note" maxlength="1000" placeholder="What is worth keeping from this moment?"></textarea>
      <div class="attachments"><input id="photo" type="file" accept="image/jpeg,image/png,image/webp" multiple hidden><div class="capture-tools"><button id="add-photo" class="photo-add" type="button">＋ Add photos</button><select id="mood" aria-label="Mood (optional)"></select></div><div id="photo-previews"></div></div>
      <p id="status" role="status"></p>
      <div class="form-footer"><span id="length">0 / 1000</span><button id="save" type="submit">Save this moment</button></div>
    </form>
    <nav class="browse-bar" aria-label="Browse moments"><button id="view-day" class="secondary" aria-pressed="true">Today</button><button id="view-all" class="secondary" aria-pressed="false">All moments</button><button id="export" class="secondary export-link">↓ Export backup</button></nav><div id="export-status" role="status"></div>
    <div class="filters"><input id="search" type="search" aria-label="Search moments and comments" placeholder="Search moments & comments…" maxlength="1000" hidden><select id="mood-filter" aria-label="Filter by mood"></select></div>
    <nav class="date-nav" id="date-nav" aria-label="Timeline date"><button id="prev-day" class="secondary" aria-label="Previous day">←</button><input type="date" id="selected-date" aria-label="Choose a date"><button id="next-day" class="secondary" aria-label="Next day">→</button><button id="go-today" class="secondary">Today</button></nav>
    <div id="undo-list" aria-live="polite"></div>
    <section id="timeline" aria-live="polite"></section>
    <dialog id="edit-dialog" aria-labelledby="edit-title"><h2 id="edit-title">Edit moment</h2><form id="edit-form"><textarea id="edit-content" aria-label="Moment text" maxlength="1000"></textarea><select id="edit-mood" aria-label="Edit mood"></select><p id="edit-status" role="status"></p><button type="submit">Save changes</button> <button type="button" id="cancel-edit" class="secondary">Cancel</button></form></dialog>
    <dialog id="image-dialog" aria-label="Photo viewer"><button id="close-image" aria-label="Close photo">Close</button><div class="viewer-nav"><button id="previous-photo" aria-label="Previous photo">←</button><span id="photo-position"></span><button id="next-photo" aria-label="Next photo">→</button></div><img id="full-image" alt="Full size moment photo"></dialog>
  </main>
  <script>
    const note = document.querySelector('#note');
    const timeline = document.querySelector('#timeline');
    const length = document.querySelector('#length');
    const photo = document.querySelector('#photo');
    document.querySelector('#add-photo').addEventListener('click', () => photo.click());
    const status = document.querySelector('#status');
    let imageData = [], readingPhotos = false, view = 'day', galleryImages = [], galleryIndex = 0;
    const search = document.querySelector('#search');
    const mood = document.querySelector('#mood');
    const moodFilter = document.querySelector('#mood-filter');
    const moodOptions = ['Calm','Happy','Grateful','Sad','Tired','Anxious'].map(value => `<option value="${value.toLowerCase()}">${value}</option>`).join('');
    mood.innerHTML = '<option value="">Mood · optional</option>' + moodOptions;
    document.querySelector('#edit-mood').innerHTML = mood.innerHTML;
    moodFilter.innerHTML = '<option value="">All moods</option>' + moodOptions;
    moodFilter.onchange = () => reloadTimeline();
    let searchTimer;
    search.oninput = () => { ++requestNumber; clearTimeout(searchTimer); searchTimer = setTimeout(reloadTimeline, 250); };
    function setView(next) { view = next; document.querySelector('#date-nav').hidden = next === 'all'; search.hidden = next !== 'all'; document.querySelector('#view-day').setAttribute('aria-pressed', next === 'day'); document.querySelector('#view-all').setAttribute('aria-pressed', next === 'all'); }
    document.querySelector('#view-day').onclick = () => { setView('day'); dateInput.value = localDay(); reloadTimeline(); };
    document.querySelector('#view-all').onclick = () => { setView('all'); reloadTimeline(); };
    document.querySelector('#export').onclick = async event => {
      const button = event.currentTarget, message = document.querySelector('#export-status'); button.disabled = true; message.textContent = 'Preparing all moments, photos and comments…';
      try { const response = await fetch('/api/backup'); if (!response.ok) throw new Error('Export failed. Please try again.'); const blob = await response.blob(); const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `remeva-backup-${localDay()}.zip`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 60000); message.textContent = 'Backup download started. Includes deleted moments and restore instructions.'; }
      catch(error) { message.textContent = error.message; } finally { button.disabled = false; }
    };
    function showPhoto() { document.querySelector('#full-image').src = galleryImages[galleryIndex]; document.querySelector('#photo-position').textContent = `${galleryIndex+1} / ${galleryImages.length}`; document.querySelector('#previous-photo').disabled = galleryIndex === 0; document.querySelector('#next-photo').disabled = galleryIndex === galleryImages.length - 1; }
    document.querySelector('#previous-photo').onclick = () => { if (galleryIndex > 0) { galleryIndex--; showPhoto(); } };
    document.querySelector('#next-photo').onclick = () => { if (galleryIndex < galleryImages.length - 1) { galleryIndex++; showPhoto(); } };
    const dateInput = document.querySelector('#selected-date');
    function localDay(date = new Date()) { return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`; }
    dateInput.value = localDay();
    let currentNotes = [], requestNumber = 0, editingId = null;
    const editDialog = document.querySelector('#edit-dialog');
    const imageDialog = document.querySelector('#image-dialog');
    const undoList = document.querySelector('#undo-list');
    function reloadTimeline() { loadNotes().catch(error => status.textContent = error.message); }
    dateInput.addEventListener('change', () => { if (dateInput.value) reloadTimeline(); });
    function shiftDay(amount) { const day = new Date(dateInput.value + 'T12:00:00'); day.setDate(day.getDate()+amount); dateInput.value = localDay(day); reloadTimeline(); }
    document.querySelector('#prev-day').onclick = () => shiftDay(-1);
    document.querySelector('#next-day').onclick = () => shiftDay(1);
    document.querySelector('#go-today').onclick = () => { dateInput.value = localDay(); reloadTimeline(); };
    document.querySelector('#cancel-edit').onclick = () => editDialog.close();
    document.querySelector('#close-image').onclick = () => imageDialog.close();
    timeline.addEventListener('click', async event => {
      const button = event.target.closest('[data-action]'); if (!button) return;
      const item = currentNotes.find(note => note.id === Number(button.dataset.id)); if (!item) return;
      if (button.dataset.action === 'zoom') { galleryImages = item.images; galleryIndex = Number(button.dataset.index); showPhoto(); imageDialog.showModal(); return; }
      if (button.dataset.action === 'edit') { editingId = item.id; document.querySelector('#edit-content').value = item.content; document.querySelector('#edit-mood').value = item.mood; document.querySelector('#edit-status').textContent = ''; editDialog.showModal(); return; }
      button.disabled = true;
      try {
        await post('/api/notes/delete', {note_id:item.id});
        const row = document.createElement('div'); row.textContent = 'Moment deleted. ';
        const undo = document.createElement('button'); undo.textContent = 'Undo'; undo.className = 'secondary'; row.append(undo); undoList.append(row);
        undo.onclick = async () => { undo.disabled = true; try { await post('/api/notes/restore', {note_id:item.id}); row.remove(); dateInput.value = item.created_at.slice(0,10); await loadNotes(); } catch(error) { status.textContent = error.message; undo.disabled = false; } };
        await loadNotes();
      } catch(error) { status.textContent = error.message; button.disabled = false; }
    });
    document.querySelector('#edit-form').addEventListener('submit', async event => {
      event.preventDefault(); const button = event.target.querySelector('button'); button.disabled = true;
      try { await post('/api/notes/edit', {note_id:editingId, content:document.querySelector('#edit-content').value, mood:document.querySelector('#edit-mood').value}); editDialog.close(); await loadNotes(); }
      catch(error) { document.querySelector('#edit-status').textContent = error.message; }
      finally { button.disabled = false; }
    });
    function renderPreviews() { document.querySelector('#photo-previews').innerHTML = imageData.map((src,index) => `<div class="preview-tile"><img src="${src}" alt="Selected photo ${index+1}"><button type="button" data-remove="${index}" aria-label="Remove photo ${index+1}">×</button></div>`).join(''); }
    function clearPhoto() { imageData = []; photo.value = ''; renderPreviews(); }
    document.querySelector('#photo-previews').onclick = event => { const button = event.target.closest('[data-remove]'); if (button && !readingPhotos) { imageData.splice(Number(button.dataset.remove),1); renderPreviews(); } };
    photo.addEventListener('change', async () => {
      const files = Array.from(photo.files); if (!files.length) return;
      if (files.length + imageData.length > 6 || files.some(file => !['image/jpeg','image/png','image/webp'].includes(file.type) || file.size > 5*1024*1024)) { status.textContent = 'Choose up to 6 JPEG, PNG or WebP photos, each up to 5 MB.'; photo.value = ''; return; }
      readingPhotos = true; document.querySelector('#add-photo').disabled = true; status.textContent = 'Loading photos…';
      try { const results = await Promise.all(files.map(file => new Promise((resolve,reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = () => reject(new Error('Could not read photos. Please try again.')); reader.readAsDataURL(file); }))); imageData.push(...results); renderPreviews(); status.textContent = ''; }
      catch(error) { status.textContent = error.message; }
      finally { readingPhotos = false; photo.value = ''; document.querySelector('#add-photo').disabled = false; }
    });
    async function post(url, body) {
      const response = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
      if (!response.ok) throw new Error('Could not save. Please check your input and try again.');
      return response.json();
    }
    document.querySelector('#today').textContent = new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric'}).format(new Date());
    note.addEventListener('input', () => length.textContent = `${note.value.length} / 1000`);
    function escapeHtml(value) { const div = document.createElement('div'); div.textContent = value; return div.innerHTML; }
    function formatTime(value) { return new Date(value).toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'}); }
    async function loadNotes() {
      const serial = ++requestNumber;
      const selectedDay = dateInput.value;
      const params = new URLSearchParams({date:selectedDay, view, mood:moodFilter.value, q:view === 'all' ? search.value.trim() : ''});
      const response = await fetch('/api/notes?' + params);
      if (!response.ok) throw new Error('Could not load moments. Please refresh to retry.');
      const notes = await response.json();
      if (serial !== requestNumber) return;
      currentNotes = notes;
      document.querySelector('#view-day').textContent = selectedDay === localDay() ? 'Today' : 'By date';
      if (!notes.length) { timeline.innerHTML = '<div class="empty">No matching moments. Try another date or clear your filters.</div>'; return; }
      timeline.innerHTML = `<div class="count">${view === 'all' ? 'All moments' : selectedDay === localDay() ? 'Today' : selectedDay} · ${notes.length} note${notes.length === 1 ? '' : 's'}</div>` + notes.map(item =>
        `<article class="event"><time>${view === 'all' ? item.created_at.slice(0,10) + ' · ' : ''}${formatTime(item.created_at)}</time>${item.mood ? `<span class="mood-tag">${escapeHtml(item.mood)}</span>` : ''}${item.content ? `<p>${escapeHtml(item.content)}</p>` : ''}${item.images.length ? `<div class="gallery">${item.images.map((src,index) => `<button class="photo-button" data-action="zoom" data-id="${item.id}" data-index="${index}" aria-label="Enlarge photo ${index+1}"><img class="photo" loading="lazy" src="${escapeHtml(src)}" alt="Photo ${index+1} saved with this moment"></button>`).join('')}</div>` : ''}<div class="note-actions" role="group" aria-label="Moment actions"><button data-action="edit" data-id="${item.id}">Edit</button><button data-action="delete" data-id="${item.id}">Delete</button></div><details><summary>Comments · ${item.comments.length} — Add a comment</summary>${item.comments.map(comment => `<div class="comment"><time>${formatTime(comment.created_at)}</time>${escapeHtml(comment.content)}</div>`).join('')}<form class="comment-form" data-note-id="${item.id}"><textarea aria-label="Comment" placeholder="Add a thought to this moment…" maxlength="1000" required></textarea><button type="submit">Post comment</button><div role="status"></div></form></details></article>`
      ).join('');
    }
    document.querySelector('#note-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      if (readingPhotos) { status.textContent = 'Please wait for your photos to load.'; return; }
      const content = note.value.trim(); if (!content && !imageData.length) { status.textContent = 'Write a moment or add a photo first.'; return; }
      const button = document.querySelector('#save'); button.disabled = true;
      try { await post('/api/notes', {content, images:imageData, mood:mood.value}); note.value = ''; length.textContent = '0 / 1000'; clearPhoto(); mood.value = ''; moodFilter.value = ''; search.value = ''; setView('day'); status.textContent = ''; dateInput.value = localDay(); await loadNotes(); }
      catch (error) { status.textContent = error.message; }
      finally { button.disabled = false; }
    });
    timeline.addEventListener('submit', async event => {
      const form = event.target.closest('.comment-form'); if (!form) return;
      event.preventDefault(); const input = form.querySelector('textarea'); const button = form.querySelector('button');
      if (!input.value.trim()) return;
      button.disabled = true;
      try { await post('/api/comments', {note_id:Number(form.dataset.noteId), content:input.value.trim()}); await loadNotes(); const updated = timeline.querySelector(`[data-note-id="${form.dataset.noteId}"]`); if (updated) updated.closest('details').open = true; }
      catch (error) { form.querySelector('[role="status"]').textContent = error.message; }
      finally { button.disabled = false; }
    });
    loadNotes().catch(error => status.textContent = error.message);
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
        if 'image' not in {row[1] for row in db.execute('PRAGMA table_info(notes)')}:
            db.execute("ALTER TABLE notes ADD COLUMN image TEXT NOT NULL DEFAULT ''")
        if 'deleted' not in {row[1] for row in db.execute('PRAGMA table_info(notes)')}:
            db.execute('ALTER TABLE notes ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0')
        columns = {row[1] for row in db.execute('PRAGMA table_info(notes)')}
        if 'images' not in columns:
            db.execute("ALTER TABLE notes ADD COLUMN images TEXT NOT NULL DEFAULT '[]'")
            for note_id, image in db.execute("SELECT id, image FROM notes WHERE image != ''").fetchall():
                db.execute('UPDATE notes SET images = ? WHERE id = ?', (json.dumps([image]), note_id))
        if 'mood' not in columns:
            db.execute("ALTER TABLE notes ADD COLUMN mood TEXT NOT NULL DEFAULT ''")
        db.execute('CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, note_id INTEGER NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL)')


def notes_for_today(day=None, all_moments=False, query='', mood='') -> list[dict[str, str | int]]:
    today = day or datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_PATH) as db:
        db.row_factory = sqlite3.Row
        clauses = ['deleted = 0']
        params = []
        if not all_moments:
            clauses.append('created_at LIKE ?')
            params.append(f'{today}%')
        if mood:
            clauses.append('mood = ?')
            params.append(mood)
        if query:
            clauses.append('(instr(lower(content), lower(?)) > 0 OR EXISTS (SELECT 1 FROM comments WHERE comments.note_id = notes.id AND instr(lower(comments.content), lower(?)) > 0))')
            params.extend([query, query])
        rows = db.execute('SELECT id, content, created_at, images, mood FROM notes WHERE ' + ' AND '.join(clauses) + ' ORDER BY created_at DESC, id DESC', params).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item['images'] = json.loads(item['images'])
            item['image'] = item['images'][0] if item['images'] else ''
            item['comments'] = [dict(comment) for comment in db.execute('SELECT id, content, created_at FROM comments WHERE note_id = ? ORDER BY id', (item['id'],))]
            result.append(item)
    return result


def create_backup():
    """Export a consistent database snapshot plus portable text and photos."""
    output = io.BytesIO()
    with tempfile.TemporaryDirectory() as folder:
        snapshot = Path(folder) / 'remevahe.db'
        with sqlite3.connect(DB_PATH) as source, sqlite3.connect(snapshot) as target:
            source.backup(target)
        with sqlite3.connect(snapshot) as db, zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            db.row_factory = sqlite3.Row
            records = []
            for row in db.execute('SELECT id, content, created_at, images, mood, deleted FROM notes ORDER BY created_at, id'):
                item = dict(row)
                photos = json.loads(item.pop('images'))
                item['photos'] = []
                for index, image in enumerate(photos):
                    prefix, encoded = image.split(',', 1)
                    extension = {'data:image/png;base64':'png', 'data:image/jpeg;base64':'jpg', 'data:image/webp;base64':'webp'}[prefix]
                    filename = f"photos/{item['id']}-{index + 1}.{extension}"
                    archive.writestr(filename, base64.b64decode(encoded))
                    item['photos'].append(filename)
                item['comments'] = [dict(comment) for comment in db.execute('SELECT id, content, created_at FROM comments WHERE note_id = ? ORDER BY id', (item['id'],))]
                records.append(item)
            archive.write(snapshot, 'remevahe.db')
            archive.writestr('moments.json', json.dumps({'version':1, 'moments':records}, ensure_ascii=False, indent=2))
            archive.writestr('README.txt', 'Remeva backup\n\nIncludes all moments, moods, photos, comments, and soft-deleted records.\nRead moments.json and the photos folder in any compatible tool.\nTo restore: stop Remeva, keep a copy of your current remevahe.db,\nthen replace it with the included remevahe.db and restart the app.\nRestoring the database replaces the current local collection.\nKeep this archive private: it contains your original journal and photos.\n')
    return output.getvalue()


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
            query = parse_qs(urlparse(self.path).query)
            day = query.get('date', [datetime.now().strftime('%Y-%m-%d')])[0]
            try:
                if datetime.strptime(day, '%Y-%m-%d').strftime('%Y-%m-%d') != day:
                    raise ValueError
            except ValueError:
                self.send_json({'error':'invalid_date'}, 400)
                return
            self.send_json(notes_for_today(day, query.get('view') == ['all'], query.get('q', [''])[0][:1000], query.get('mood', [''])[0]))
        elif path == '/api/backup':
            data = create_backup()
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Disposition', 'attachment; filename="remeva-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.zip"')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path == "/health":
            self.send_json({"status": "ok", "name": "remevahe"})
        else:
            self.send_json({"error": "not_found"}, 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path in ('/api/notes/edit', '/api/notes/delete', '/api/notes/restore'):
            self.modify_note(path)
            return
        if path not in ("/api/notes", "/api/comments"):
            self.send_json({"error": "not_found"}, 404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 42 * 1024 * 1024:
                raise ValueError
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict) or not isinstance(payload.get('content', ''), str):
                raise ValueError
            content = payload.get('content', '').strip()
            images = validate_images(payload.get('images', [payload['image']] if payload.get('image') else [])) if path == '/api/notes' else []
            mood = payload.get('mood', '')
            if mood not in MOODS or len(content) > 1000 or (not content and not images):
                raise ValueError
            if path == '/api/comments' and type(payload.get('note_id')) is not int:
                raise ValueError
        except (ValueError, binascii.Error):
            self.send_json({"error": "invalid_input"}, 400)
            return
        created_at = datetime.now().isoformat(timespec="seconds")
        with sqlite3.connect(DB_PATH) as db:
            if path == '/api/comments':
                if not db.execute('SELECT 1 FROM notes WHERE id = ? AND deleted = 0', (payload['note_id'],)).fetchone():
                    self.send_json({'error':'note_not_found'}, 404)
                    return
                cursor = db.execute('INSERT INTO comments (note_id, content, created_at) VALUES (?, ?, ?)', (payload['note_id'], content, created_at))
            else:
                cursor = db.execute("INSERT INTO notes (content, created_at, image, images, mood) VALUES (?, ?, ?, ?, ?)", (content, created_at, images[0] if images else '', json.dumps(images), mood))
            note_id = cursor.lastrowid
        self.send_json({"id": note_id, "content": content, "created_at": created_at}, 201)

    def modify_note(self, path):
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 16384:
                raise ValueError
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict) or type(payload.get('note_id')) is not int:
                raise ValueError
            with sqlite3.connect(DB_PATH) as db:
                row = db.execute('SELECT image, deleted FROM notes WHERE id = ?', (payload['note_id'],)).fetchone()
                if not row or (row[1] and path != '/api/notes/restore'):
                    self.send_json({'error':'note_not_found'}, 404)
                    return
                if path == '/api/notes/edit':
                    content = payload.get('content')
                    if not isinstance(content, str) or len(content.strip()) > 1000 or (not content.strip() and not row[0]):
                        raise ValueError
                    mood = payload.get('mood')
                    if mood is not None and mood not in MOODS:
                        raise ValueError
                    db.execute('UPDATE notes SET content = ? WHERE id = ?', (content.strip(), payload['note_id']))
                    if mood is not None:
                        db.execute('UPDATE notes SET mood = ? WHERE id = ?', (mood, payload['note_id']))
                else:
                    db.execute('UPDATE notes SET deleted = ? WHERE id = ?', (int(path == '/api/notes/delete'), payload['note_id']))
            self.send_json({'status':'ok'})
        except ValueError:
            self.send_json({'error':'invalid_input'}, 400)

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
