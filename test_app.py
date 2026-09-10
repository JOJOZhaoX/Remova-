import io
import json
import sqlite3
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app


PNG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='


class MomentsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_path = app.DB_PATH
        app.DB_PATH = Path(self.temp.name) / 'test.db'
        # Simulate the previous single-photo schema and an existing record.
        with sqlite3.connect(app.DB_PATH) as db:
            db.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, created_at TEXT NOT NULL, image TEXT NOT NULL DEFAULT '', deleted INTEGER NOT NULL DEFAULT 0)")
            db.execute('INSERT INTO notes(content,created_at,image) VALUES (?,?,?)', ('Old moment', '2025-01-01T12:00:00', PNG))
        app.init_db()
        app.init_db()
        self.server = app.ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.root = 'http://127.0.0.1:' + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        app.DB_PATH = self.original_path
        self.temp.cleanup()

    def get(self, query):
        return json.load(urlopen(self.root + '/api/notes?' + query))

    def post(self, path, payload):
        request = Request(self.root + path, json.dumps(payload).encode(), {'Content-Type':'application/json'})
        return json.load(urlopen(request))

    def test_collection_search_moods_and_multiphoto(self):
        old = self.get('date=2025-01-01')[0]
        self.assertEqual(old['images'], [PNG])
        new = self.post('/api/notes', {'content':'A quiet walk', 'images':[PNG, PNG], 'mood':'calm'})
        self.post('/api/comments', {'note_id':new['id'], 'content':'Found a SUNFLOWER'})
        self.assertEqual(len(self.get('view=all')), 2)
        found = self.get('view=all&q=sunflower&mood=calm')
        self.assertEqual(found[0]['id'], new['id'])
        self.assertEqual(len(found[0]['images']), 2)
        self.assertEqual(self.get('view=all&q=sunflower&mood=sad'), [])
        self.assertEqual(self.get('view=all&q=%25'), [])
        self.post('/api/notes/edit', {'note_id':new['id'], 'content':'Updated', 'mood':'happy'})
        edited = self.get('view=all&mood=happy')[0]
        self.assertEqual(len(edited['images']), 2)
        self.assertEqual(len(edited['comments']), 1)
        self.post('/api/notes/delete', {'note_id':new['id']})
        self.assertEqual(self.get('view=all&q=sunflower'), [])
        self.post('/api/notes/restore', {'note_id':new['id']})
        self.assertEqual(len(self.get('view=all&q=sunflower')), 1)

    def test_validation(self):
        for payload in ({'content':'', 'images':[]}, {'images':[PNG]*7}, {'images':['data:text/html;base64,AAAA']}, {'content':'OK', 'mood':'unknown'}, {'images':'wrong'}):
            with self.assertRaises(HTTPError) as caught:
                self.post('/api/notes', payload)
            self.assertEqual(caught.exception.code, 400)

    def test_backup_can_be_restored(self):
        record = self.post('/api/notes', {'content':'Backup me', 'images':[PNG,PNG], 'mood':'grateful'})
        self.post('/api/comments', {'note_id':record['id'], 'content':'Keep this comment'})
        self.post('/api/notes/delete', {'note_id':record['id']})
        response = urlopen(self.root + '/api/backup')
        self.assertIn('attachment', response.headers['Content-Disposition'])
        with zipfile.ZipFile(io.BytesIO(response.read())) as archive:
            manifest = json.loads(archive.read('moments.json'))
            saved = next(item for item in manifest['moments'] if item['id'] == record['id'])
            self.assertEqual(saved['deleted'], 1)
            self.assertEqual(saved['mood'], 'grateful')
            self.assertEqual(len(saved['photos']), 2)
            self.assertEqual(saved['comments'][0]['content'], 'Keep this comment')
            self.assertTrue(archive.read(saved['photos'][0]).startswith(b'\x89PNG'))
            archive.extract('remevahe.db', self.temp.name)
        with sqlite3.connect(Path(self.temp.name)/'remevahe.db') as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM notes').fetchone()[0], 2)


if __name__ == '__main__':
    unittest.main()
