import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.core.speech.transcribers.modern import ModernTranscriber
from src.core.speech.checkpoint import ASRResponseError,response_text


class EmptyASRTests(unittest.TestCase):
    def setup_fixture(self,folder):
        folder=Path(folder);source=folder/'input.wav';source.write_bytes(b'fixture source')
        config=type('TempConfig',(),{'TRANSCRIPT_PATH':folder/'transcripts'})
        return source,config
    def patches(self,replies):
        import contextlib
        stack=contextlib.ExitStack()
        from src.core.speech.adapters import REGISTRY,ModelSpec
        stack.enter_context(patch.dict(REGISTRY,{'elevenlabs/scribe-v2':ModelSpec('elevenlabs/scribe-v2','unsupported')}))
        stack.enter_context(patch('src.core.speech.transcribers.modern.get_audio_duration',return_value=60))
        stack.enter_context(patch('src.core.speech.transcribers.modern.subprocess.run',side_effect=lambda args,**kwargs:Path(args[-1]).write_bytes(b'fixture audio')))
        stack.enter_context(patch('src.core.speech.transcribers.modern.route',return_value=('openrouter','elevenlabs/scribe-v2')))
        stack.enter_context(patch('src.core.speech.transcribers.modern.stage',return_value={'options':{'provider_options':{'elevenlabs':{'diarize':False}}}}))
        mock=stack.enter_context(patch('src.core.speech.transcribers.modern.post',side_effect=replies))
        stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        return stack,mock

    def test_empty_first_chunk_continues_marks_gap_and_reuses_completed_responses(self):
        with tempfile.TemporaryDirectory() as d:
            source,config=self.setup_fixture(d);stack,post=self.patches([{'text':'','words':[]},{'text':'본문'}])
            with stack:
                first=ModernTranscriber(config,'elevenlabs/scribe-v2').transcribe(str(source))
                second=ModernTranscriber(config,'elevenlabs/scribe-v2').transcribe(str(source))
            self.assertIn('미전사 구간',first);self.assertIn('본문',first)
            self.assertEqual(len(first.asr_issues),1);self.assertEqual(first.asr_issues[0]['start'],0)
            self.assertEqual(first,second);self.assertEqual(post.call_count,2)
            root=Path(first.asr_cache)
            self.assertEqual(json.loads((root/'0.json').read_text()),{'text':'','words':[]})
            self.assertEqual(json.loads((root/'status.json').read_text())['usable_chunks'],1)

    def test_later_failure_reuses_first_paid_response_on_next_invocation(self):
        with tempfile.TemporaryDirectory() as d:
            source,config=self.setup_fixture(d);stack,post=self.patches([{'text':'앞부분'},RuntimeError('fixture network failure'),{'text':'뒷부분'}])
            with stack:
                with self.assertRaisesRegex(RuntimeError,'network'):ModernTranscriber(config,'elevenlabs/scribe-v2').transcribe(str(source))
                result=ModernTranscriber(config,'elevenlabs/scribe-v2').transcribe(str(source))
            self.assertEqual(post.call_count,3);self.assertEqual(result,'앞부분\n뒷부분')

    def test_all_empty_is_not_a_success_and_malformed_response_is_not_retried(self):
        for replies in ([{'text':''},{'text':''}],[None]):
            with tempfile.TemporaryDirectory() as d:
                source,config=self.setup_fixture(d);stack,post=self.patches(replies)
                with stack:
                    with self.assertRaises(ASRResponseError):ModernTranscriber(config,'elevenlabs/scribe-v2').transcribe(str(source))
                    before=post.call_count
                    with self.assertRaises(ASRResponseError):ModernTranscriber(config,'elevenlabs/scribe-v2').transcribe(str(source))
                    self.assertEqual(post.call_count,before)

    def test_force_is_explicit_and_preserves_previous_raw_responses(self):
        with tempfile.TemporaryDirectory() as d:
            source,config=self.setup_fixture(d)
            stack,post=self.patches([{'text':'old one'},{'text':'old two'},{'text':'new one'},{'text':'new two'}])
            with stack:
                ModernTranscriber(config,'elevenlabs/scribe-v2').transcribe(str(source))
                result=ModernTranscriber(config,'elevenlabs/scribe-v2').transcribe(str(source),refresh=True)
            self.assertEqual(post.call_count,4)
            self.assertEqual(result,'new one\nnew two')
            saved=list((Path(result.asr_cache)/'previous').glob('0-*.json'))
            self.assertEqual(json.loads(saved[0].read_text())['text'],'old one')

    def test_words_only_response_is_recovered_without_another_request(self):
        self.assertEqual(response_text({'words':[{'text':'hello'},{'text':' '},{'text':'world'}]}),'hello world')
        self.assertEqual(response_text({'text':None,'words':[]}),'')
        with self.assertRaises(ASRResponseError):response_text({})
        with self.assertRaises(ASRResponseError):response_text({'error':'upstream failure'})
