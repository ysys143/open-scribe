import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave
import httpx
from src.core.providers import models as models
from src.core.config.settings import Config
from src.core.presentation.cli import create_argument_parser, process_single_video


class LegacyModelTests(unittest.TestCase):
    def configuration(self):
        return {'stages':{'asr':{'provider':'openrouter','model':'elevenlabs/scribe-v2','options':{'provider_options':{'elevenlabs':{'diarize':True,'tag_audio_events':False,'no_verbatim':False}}}},'summary':{'model':'openai/gpt-6-luna','options':{'effort':'medium'}}}}

    def pipeline(self,stream=True,identify=False,diarized=True,summary_enabled=True,partial=False):
        utterance="저는 김민수입니다." if identify else "첫 발화입니다."
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            audio=folder/'source.wav'
            with wave.open(str(audio),'wb') as output:
                output.setparams((1,2,16000,0,'NONE','not compressed'));output.writeframes(b'\0\0'*1600)
            requests=[]
            def handle(request):
                requests.append(request)
                body=json.loads(request.content)
                if request.url.path.endswith('audio/transcriptions'):
                    if partial and len(requests)==1:return httpx.Response(200,json={'text':'','words':[]})
                    self.assertEqual(body['model'],'elevenlabs/scribe-v2')
                    self.assertTrue(body['provider']['options']['elevenlabs']['diarize'])
                    self.assertEqual(body['input_audio']['format'],'wav')
                    unit={'text':utterance,'start':0,'end':.1}
                    if diarized:unit['speaker_id']='speaker_0'
                    return httpx.Response(200,json={'text':utterance,'words':[unit]})
                self.assertEqual(body['model'],'gpt-6-luna')
                self.assertEqual(body['reasoning_effort'],'medium')
                self.assertNotIn('temperature',body)
                self.assertNotIn('max_tokens',body)
                has_context='self_introduction' in body['messages'][0]['content']
                self.assertEqual(has_context,diarized)
                names=[{'label':'chunk0/speaker_0','name':'김민수','turn_id':'chunk0:turn0','evidence':utterance,'basis':'self_introduction'}] if identify else []
                content=json.dumps({'summary':'회의 요약입니다.','speakers':names},ensure_ascii=False) if has_context else '회의 요약입니다.'
                return httpx.Response(200,json={'choices':[{'message':{'content':content}}]})
            real_client=httpx.Client
            def client_factory(*args,**kwargs):return real_client(transport=httpx.MockTransport(handle))
            output=io.StringIO()
            args=create_argument_parser().parse_args(['https://youtu.be/oQypVVv1u1o','--engine','elevenlabs/scribe-v2','--audio','--downloads','--summary' if summary_enabled else '--no-summary','--timestamp'])
            args.stream=stream
            config=type('TestConfig',(Config,),{'DB_PATH':folder/'test.db','AUDIO_PATH':folder/'audio','VIDEO_PATH':folder/'video','TEMP_PATH':folder/'tmp','TRANSCRIPT_PATH':folder/'transcripts','DOWNLOADS_PATH':folder/'downloads'})()
            config.TRANSCRIPT_PATH.mkdir()
            from src.core.speech.adapters import REGISTRY,ModelSpec
            with patch('src.core.config.document.load_settings',return_value={'paths':{'data':str(folder/'diagnostics')}}),patch.dict(REGISTRY,{'elevenlabs/scribe-v2':ModelSpec('elevenlabs/scribe-v2','unsupported')}),patch('src.core.speech.adapters.policy',return_value=(ModelSpec('elevenlabs/scribe-v2','unsupported'),'auto',True)),patch.dict(os.environ,{'OPENAI_API_KEY':'test-openai','OPENROUTER_API_KEY':'test-openrouter'}),patch.object(models,'settings',return_value=self.configuration()),patch.object(httpx,'Client',side_effect=client_factory),patch('src.core.presentation.cli.YouTubeDownloader') as downloader,patch('src.core.presentation.cli.notion.is_configured',return_value=False),contextlib.redirect_stdout(output):
                downloader.return_value.get_video_info.return_value={'id':'oQypVVv1u1o','title':'복원 회의','duration':1,'uploader':'fixture'}
                downloader.return_value.download_audio.return_value=str(audio)
                if partial:
                    with patch('src.core.speech.transcribers.modern.get_audio_duration',return_value=60):
                        self.assertFalse(process_single_video(args.input,args,config))
                    self.assertFalse(process_single_video(args.input,args,config))
                else:self.assertTrue(process_single_video(args.input,args,config))
            files={p.name:p.read_text() for p in config.DOWNLOADS_PATH.iterdir()}
            self.assertIn('복원_회의.txt',files)
            self.assertIn(utterance,files['복원_회의.txt'])
            if summary_enabled:
                self.assertIn('회의 요약입니다.',files['복원_회의_summary.txt'])
            else:self.assertNotIn('복원_회의_summary.txt',files)
            self.assertEqual(len(requests),(3 if summary_enabled else 2) if partial else (2 if summary_enabled else 1))
            if partial:
                self.assertIn('미전사 구간',files['복원_회의.txt'])
                self.assertIn('확인 필요',files['복원_회의_summary.txt'])
                import sqlite3
                with sqlite3.connect(config.DB_PATH) as connection:self.assertEqual(connection.execute('SELECT status FROM transcription_jobs').fetchone()[0],'partial')
            if identify and summary_enabled:
                self.assertTrue(files['복원_회의.txt'].startswith('[00:00] 김민수:'))
                raw=list(config.TRANSCRIPT_PATH.glob('*_raw_*.txt'))
                self.assertEqual(len(raw),1)
                self.assertIn('chunk0/speaker_0:',raw[0].read_text())
                self.assertIn('김민수', (config.TRANSCRIPT_PATH/'복원_회의_speaker_names.json').read_text())
            if diarized:
                if stream:self.assertLess(output.getvalue().index('speaker_0: '+utterance),output.getvalue().index('Transcript saved:'))
                else:self.assertNotIn('speaker_0: '+utterance,output.getvalue())
            return output.getvalue()

    def test_title_stream_summary_and_copy_end_to_end(self):self.pipeline()
    def test_no_stream_preserves_files(self):self.pipeline(False)

    def test_speaker_names_reach_transcript_copy_and_preserve_raw(self):self.pipeline(identify=True)
    def test_model_without_actual_diarization_keeps_normal_summary(self):self.pipeline(diarized=False)
    def test_no_summary_does_not_call_identity_model(self):self.pipeline(identify=True,summary_enabled=False)

    def test_empty_chunk_persists_partial_state_and_cannot_become_completed_on_cached_run(self):self.pipeline(partial=True)

    def test_http_error_is_not_retried_or_fallback(self):
        calls=[]
        def handle(request):
            calls.append(request);return httpx.Response(401,json={'error':'fixture'})
        with patch.object(models,'credential',return_value='fixture'),patch.object(httpx,'Client',return_value=httpx.Client(transport=httpx.MockTransport(handle))):
            with self.assertRaisesRegex(ValueError,'HTTP 401'):models.post('openrouter','audio/transcriptions',json_body={})
        self.assertEqual(len(calls),1)

    def test_explicit_key_file_does_not_export_or_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'keys';path.write_text('OPENROUTER_API_KEY="fixture-file"\n');path.chmod(0o600)
            with patch.object(models,'settings',return_value={'providers':{'openrouter':{'api_key_file':str(path)}}}),patch.dict(os.environ,{'OPENROUTER_API_KEY':'fixture-env'}):
                self.assertEqual(models.credential('openrouter'),'fixture-file')
                self.assertEqual(os.environ['OPENROUTER_API_KEY'],'fixture-env')
                path.write_text('OTHER=fixture\n')
                self.assertIsNone(models.credential('openrouter'))

if __name__=='__main__':unittest.main()
