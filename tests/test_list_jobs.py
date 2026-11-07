import contextlib
import io
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from src.core.presentation.list_jobs import main,recent


class ListingTests(unittest.TestCase):
    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'missing/db'
            with contextlib.redirect_stdout(io.StringIO()) as output:self.assertEqual(main([],path),0)
            self.assertIn('없습니다',output.getvalue());self.assertFalse(path.parent.exists())

    def test_default_ten_and_requested_limit_latest_first_readonly(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'db'
            with sqlite3.connect(path) as c:
                c.execute('CREATE TABLE transcription_jobs(id INTEGER,title,status,transcript_path,created_at,updated_at,completed_at)')
                c.executemany('INSERT INTO transcription_jobs VALUES(?,?,?,?,?,?,?)',[(n,'회의 '+str(n),'completed','/out/'+str(n),f'2026-11-{n:02} 12:00:00',None,None) for n in range(1,17)])
            before=path.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()) as output:self.assertEqual(main([],path),0)
            self.assertEqual(len(recent(path)),10);self.assertEqual(recent(path)[0]['id'],16)
            self.assertEqual([r['id'] for r in recent(path,3)],[16,15,14])
            with contextlib.redirect_stdout(io.StringIO()) as output:main(['3'],path)
            self.assertEqual(len(output.getvalue().splitlines()),6)
            self.assertEqual(before,path.read_bytes())

    def test_bad_limit_and_cli_dispatch_do_not_transcribe(self):
        from src.core.presentation import cli
        for value in ('0','-2','abc'):
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:main([value],'/missing')
            self.assertEqual(error.exception.code,2)
        with patch('sys.argv',['scr','ls','3']),patch('src.core.presentation.list_jobs.main',return_value=0) as listing,patch.object(cli,'process_single_video',side_effect=AssertionError('transcription called')):
            self.assertEqual(cli.main(),0);listing.assert_called_once_with(['3'],cli.Config.DB_PATH)
