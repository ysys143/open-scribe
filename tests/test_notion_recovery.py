"""Offline regressions for Notion receipts and CLI stage failures."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from src.integrations import notion
from src.core.presentation import cli
from src.core.runtime.database import TranscriptionDatabase
from src.core.speech.checkpoint import ASRResult


class NotionTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(patch.object(notion, 'credential', return_value='fixture'))
        self.stack.enter_context(patch.object(notion, 'load_settings', return_value={
            'integrations': {'notion': {'database_id': 'database'}}}))
        self.client = Mock()
        self.client.post.return_value.json.return_value = {'id': 'page-id'}
        self.stack.enter_context(patch.object(notion, '_get_client', return_value=SimpleNamespace(Client=Mock(return_value=self.client))))

    def save(self, **kwargs):
        return notion.save_to_notion(title='title', url=kwargs.pop('url', '/tmp/audio.wav'), engine='fixture', transcript=kwargs.pop('transcript', 'text'), **kwargs)

    def test_default_completed_and_local_path_not_a_url(self):
        self.assertEqual(self.save(), 'page-id')
        props = self.client.post.call_args.kwargs['json']['properties']
        self.assertEqual(props['Status']['select']['name'], 'completed')
        self.assertNotIn('URL', props)
        self.save(url='https://example.com/audio', status='partial')
        props = self.client.post.call_args.kwargs['json']['properties']
        self.assertEqual(props['URL']['url'], 'https://example.com/audio')
        self.assertEqual(props['Status']['select']['name'], 'partial')

    def test_receipt_persisted_before_append_and_completed_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'receipt.json'
            def append(*args, **kwargs):
                self.assertEqual(json.loads(path.read_text())['page_id'], 'page-id')
                return Mock()
            self.client.patch.side_effect = append
            text = 'x' * 210000
            self.assertEqual(self.save(transcript=text, state_path=path), 'page-id')
            self.assertEqual(json.loads(path.read_text())['status'], 'completed')
            self.assertEqual(self.save(transcript=text, state_path=path), 'page-id')
            self.assertEqual(self.client.post.call_count, 1)
            self.assertEqual(self.client.patch.call_count, 1)
            self.assertTrue(self.client.close.called)

    def test_unknown_create_or_append_never_reissued(self):
        for append in (False, True):
            with self.subTest(append=append), tempfile.TemporaryDirectory() as folder:
                self.client.reset_mock()
                self.client.post.side_effect = None if append else TimeoutError('lost response')
                self.client.patch.side_effect = TimeoutError('lost append response')
                path = Path(folder)/'receipt.json'
                text = 'x'*210000 if append else 'text'
                self.assertIsNone(self.save(transcript=text, state_path=path))
                state = json.loads(path.read_text())
                self.assertEqual(state['status'], 'unknown')
                self.assertEqual(state.get('page_id'), 'page-id' if append else None)
                self.assertIsNone(self.save(transcript=text, state_path=path))
                self.assertEqual(self.client.post.call_count, 1)
                self.assertEqual(self.client.patch.call_count, int(append))
                self.assertTrue(self.client.close.called)

    def test_changed_or_corrupt_state_does_not_create(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'receipt.json'
            self.save(state_path=path)
            self.assertIsNone(self.save(state_path=path, transcript='changed'))
            path.write_text('{bad json')
            self.assertIsNone(self.save(state_path=path))
            self.assertEqual(self.client.post.call_count, 1)


class CLIStageTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        folder = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.config = SimpleNamespace(DB_PATH=folder/'jobs.db', TRANSCRIPT_PATH=folder/'transcripts', DOWNLOADS_PATH=None)
        self.source = folder/'fixture.wav'
        self.source.write_bytes(b'fixture')
        self.args = SimpleNamespace(engine='fixture', downloads=False, audio=False, video=False, summary=True, srt=False, translate=False, force=False, stream=False, timestamp=False, verbose=False)
        transcriber = Mock()
        self.result = ASRResult('fixture transcript')
        self.result.asr_issues = [{'start': 0}]
        self.result.asr_cache = '/fixture/cache'
        transcriber.transcribe.return_value = self.result
        self.stack.enter_context(patch.object(cli, 'get_transcriber', return_value=transcriber))
        self.stack.enter_context(patch.object(cli.notion, 'is_configured', return_value=True))
        self.save = self.stack.enter_context(patch.object(cli.notion, 'save_to_notion', return_value='page-id'))
        self.stack.enter_context(patch('src.core.postprocess.keywords.extract_keywords', return_value=[]))
        self.summary = self.stack.enter_context(patch.object(cli, 'generate_summary', return_value='summary'))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def run_cli(self):
        return cli.process_single_video(str(self.source), self.args, self.config)

    def job(self):
        return TranscriptionDatabase(self.config.DB_PATH).get_job_progress('local_fixture', 'fixture')

    def test_metadata_exists_before_summary_and_exception_leaves_partial(self):
        def summary(*args, **kwargs):
            record = json.loads((self.config.TRANSCRIPT_PATH/'fixture_asr_status.json').read_text())
            self.assertEqual(record['issues'], self.result.asr_issues)
            self.assertEqual(record['cache_path'], '/fixture/cache')
            raise RuntimeError('postprocess failed')
        self.summary.side_effect = summary
        with self.assertRaisesRegex(RuntimeError, 'postprocess failed'):
            self.run_cli()
        self.assertEqual(self.job()['status'], 'partial')
        self.summary.side_effect = None
        self.run_cli()
        self.assertEqual(self.save.call_args.kwargs['status'], 'partial')
        self.assertIsNotNone(self.save.call_args.kwargs['state_path'])
        self.assertIsNone(self.save.call_args.kwargs['url'])

    def test_diarization_issue_uses_generic_review_wording(self):
        self.result.asr_issues = [{'reason': 'diarization_missing'}]
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertFalse(self.run_cli())
        self.assertIn('ASR 확인 필요 항목 1개', output.getvalue())
        self.assertNotIn('미전사 구간', output.getvalue())
        summary = self.save.call_args.kwargs['summary']
        self.assertIn('ASR 확인 필요 항목 1개', summary)
        self.assertNotIn('전체 발화가 반영되지 않았습니다', summary)
        self.assertEqual(self.job()['status'], 'partial')

    def test_summary_translation_notion_failure_each_leaves_partial(self):
        self.result.asr_issues = []
        self.summary.return_value = None
        self.assertFalse(self.run_cli())
        self.assertEqual(self.job()['status'], 'partial')
        self.assertEqual(self.save.call_args.kwargs['status'], 'partial')
        self.summary.return_value = 'summary'
        self.args.translate = True
        with patch.object(cli, 'SubtitleTranslator') as translator:
            translator.return_value.translate_text.return_value = ('', False)
            self.assertFalse(self.run_cli())
        self.assertEqual(self.job()['status'], 'partial')
        self.args.translate = False
        self.save.return_value = None
        self.assertFalse(self.run_cli())
        self.assertEqual(self.job()['status'], 'partial')

    def test_transcriber_exception_leaves_failed(self):
        with patch.object(cli, 'get_transcriber', side_effect=RuntimeError('setup failed')):
            with self.assertRaisesRegex(RuntimeError, 'setup failed'):
                self.run_cli()
        self.assertEqual(self.job()['status'], 'failed')

    def test_clean_success_is_completed_and_suppresses_unrequested_calls(self):
        self.result.asr_issues = []
        self.args.summary = False
        with patch.object(cli, 'SubtitleTranslator', side_effect=AssertionError('unrequested translation')):
            self.assertTrue(self.run_cli())
        self.summary.assert_not_called()
        self.assertEqual(self.job()['status'], 'completed')
        self.assertEqual(self.save.call_args.kwargs['status'], 'completed')

    def test_keyword_exception_keeps_asr_metadata_and_partial_status(self):
        self.result.asr_issues = []
        with patch('src.core.postprocess.keywords.extract_keywords', side_effect=RuntimeError('keyword failure')):
            with self.assertRaisesRegex(RuntimeError, 'keyword failure'):
                self.run_cli()
        self.assertEqual(self.job()['status'], 'partial')
        self.assertTrue((self.config.TRANSCRIPT_PATH/'fixture_asr_status.json').exists())
        self.save.assert_not_called()

    def test_srt_failure_leaves_partial_and_retries_requested_stage(self):
        self.result.asr_issues = []
        self.args.srt = True
        self.config.AUDIO_PATH = self.source.parent
        self.config.VIDEO_PATH = self.source.parent
        self.config.TEMP_PATH = self.source.parent
        self.config.COOKIES_BROWSER = None
        url = 'https://www.youtube.com/watch?v=fixture'
        with patch.object(cli, 'YouTubeDownloader') as downloader, patch.object(cli, 'convert_transcript_to_srt', side_effect=RuntimeError('srt failure')) as convert:
            downloader.return_value.get_video_info.return_value = {'id': 'fixture', 'title': 'fixture', 'duration': 1, 'uploader': 'fixture'}
            downloader.return_value.download_audio.return_value = str(self.source)
            self.assertFalse(cli.process_single_video(url, self.args, self.config))
            job = TranscriptionDatabase(self.config.DB_PATH).get_job_progress('fixture', 'fixture')
            self.assertEqual(job['status'], 'partial')
            self.assertEqual(self.save.call_args.kwargs['status'], 'partial')
            self.assertFalse(cli.process_single_video(url, self.args, self.config))
            self.assertEqual(convert.call_count, 2)


class DispatchTests(unittest.TestCase):
    def test_models_and_repair_dispatch_before_parser_without_transcription(self):
        import sys
        for command, module, tail in (
            ('models', 'src.core.speech.catalog', []),
            ('repair', 'src.core.speech.repair', ['input.wav', '--fixture']),
        ):
            main = Mock(return_value=7)
            with patch.dict(sys.modules, {module: SimpleNamespace(main=main)}), patch.object(sys, 'argv', ['scr', command, *tail]), patch.object(cli, 'create_argument_parser', side_effect=AssertionError('parser invoked')):
                self.assertEqual(cli.main(), 7)
            if command == 'models':
                main.assert_called_once_with()
            else:
                main.assert_called_once_with(tail)
