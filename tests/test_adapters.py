import contextlib,io,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from src.core.speech.adapters import *

class AdapterTests(unittest.TestCase):
    def test_gateway_word_and_numeric_zero(self):
        raw={'text':'저는 민수입니다','words':[{'word':'저는','start':0,'end':1,'speaker':0},{'word':'민수입니다','start':1,'end':2,'speaker':0}]}
        result=assemble([(0,raw)],'elevenlabs/scribe-v2',OpenRouterSTTAdapter())
        self.assertIn('chunk0/0:',result);self.assertTrue(result.speaker_context['spans']);self.assertNotIn('text',raw['words'][0])
    def test_native_shape_and_unknown_capability(self):
        raw={'text':'hello','words':[{'text':'hello','speaker_id':'speaker_0','type':'word','start':0,'end':1}]}
        self.assertEqual(ElevenLabsScribeAdapter().normalize(raw)['words'][0]['speaker_id'],'speaker_0')
        with self.assertRaises(ASRResponseError):policy('nvidia/nemotron-3.5-transcribe',{'diarize':True})
    def test_single_call_and_cached_replay(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'input.m4a';source.write_bytes(b'fixture')
            config=type('Config',(),{'TRANSCRIPT_PATH':Path(d)/'out'})
            raw={'text':'hello','words':[{'text':'hello','speaker_id':'s0','start':0,'end':1}]}
            with patch('src.core.speech.audio.get_audio_duration',return_value=3600),patch.object(ElevenLabsScribeAdapter,'request',return_value=raw) as request,contextlib.redirect_stdout(io.StringIO()):
                first=single_request(config,source,'elevenlabs/scribe-v2',{},'elevenlabs',True,True)
                second=single_request(config,source,'elevenlabs/scribe-v2',{},'elevenlabs',True,True)
            self.assertEqual(request.call_count,1);self.assertEqual(first,second)

    def test_native_http_contract_and_preflight_size(self):
        import httpx
        from types import SimpleNamespace
        calls=[]
        def handle(request):
            calls.append(request)
            assert request.url.path=='/v1/speech-to-text'
            assert request.headers['xi-api-key']=='fixture'
            assert b'scribe_v2' in request.content and b'name="diarize"' in request.content
            assert b'name="file"' in request.content
            return httpx.Response(200,json={'text':'hello','words':[]})
        real=httpx.Client
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'audio.m4a';p.write_bytes(b'fixture')
            with patch('src.core.speech.adapters.credential',return_value='fixture'),patch('src.core.speech.adapters.httpx.Client',side_effect=lambda **kw:real(transport=httpx.MockTransport(handle))),contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ElevenLabsScribeAdapter().request(p,'elevenlabs/scribe-v2',{},True)['text'],'hello')
                with patch.object(Path,'stat',return_value=SimpleNamespace(st_size=3_000_000_001)):
                    with self.assertRaises(ASRResponseError):ElevenLabsScribeAdapter().request(p,'elevenlabs/scribe-v2',{},True)
        self.assertEqual(len(calls),1)

    def test_wrong_binding_never_falls_back(self):
        with self.assertRaises(ASRResponseError):policy('elevenlabs/scribe-v2',{},'openai')

    def test_friendly_output_keeps_identity_and_name_replacement(self):
        from src.core.speech.labels import friendly_speakers,replace_names
        raw={'text':'hello yes','words':[{'text':'hello','speaker_id':'speaker_2','start':0,'end':1},{'text':'yes','speaker_id':'speaker_0','start':1,'end':2}]}
        original=assemble([(0,raw)],'elevenlabs/scribe-v2',ElevenLabsScribeAdapter())
        friendly=friendly_speakers(original)
        self.assertIn('화자 1: hello',friendly);self.assertIn('화자 2: yes',friendly)
        self.assertEqual(friendly.speaker_context['turns'][0]['speaker'],'chunk0/speaker_2')
        named=replace_names(friendly,{'chunk0/speaker_2':'민수'})
        self.assertIn('민수: hello',named);self.assertIn('화자 2: yes',named)
        from src.core.postprocess.speaker_names import parse_summary
        import json
        summary=parse_summary(json.dumps({'summary':'[[speaker:chunk0/speaker_2]]의 발화','speakers':[]}),friendly.speaker_context)
        self.assertEqual(summary,'화자 1의 발화')
