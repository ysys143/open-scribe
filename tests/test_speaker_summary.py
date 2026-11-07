import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.core.speech.labels import DiarizedText,digest,label_units,replace_names,restore_context,save_context
from src.core.postprocess.speaker_names import parse_summary
from src.core.postprocess.summary import generate_summary


def fixture():
    text='[00:00] chunk0/speaker_0: 저는 김민수입니다. speaker_0라는 단어는 그대로 둡니다.'
    start=text.index('chunk0/speaker_0')
    return DiarizedText(text,{'version':1,'engine':'elevenlabs/scribe-v2','text_sha256':digest(text),
        'turns':[{'id':'chunk0:turn0','speaker':'chunk0/speaker_0','text':'저는 김민수입니다. speaker_0라는 단어는 그대로 둡니다.'},
                 {'id':'chunk1:turn0','speaker':'chunk1/speaker_0','text':'반갑습니다.'}],
        'spans':[{'start':start,'end':start+len('chunk0/speaker_0'),'label':'chunk0/speaker_0'}]})


def response(**change):
    item={'label':'chunk0/speaker_0','name':'김민수','turn_id':'chunk0:turn0',
          'evidence':'저는 김민수입니다.','basis':'self_introduction'}
    item.update(change)
    return json.dumps({'summary':'[[speaker:chunk0/speaker_0]]의 발표','speakers':[item]},ensure_ascii=False)


class SpeakerSummaryTests(unittest.TestCase):
    def test_valid_names_replace_label_spans_only(self):
        text=fixture();summary=parse_summary(response(),text.speaker_context)
        self.assertEqual(summary,'김민수의 발표')
        changed=replace_names(text,summary.speaker_mapping)
        self.assertEqual(changed,'[00:00] 김민수: 저는 김민수입니다. speaker_0라는 단어는 그대로 둡니다.')
        self.assertIn('chunk0/speaker_0:',text)

    def test_unknown_cross_chunk_and_unsupported_evidence_not_applied(self):
        text=fixture()
        for invalid in ({'label':'invented'},{'turn_id':'chunk1:turn0'},
                        {'name':'이영희'},{'evidence':'없는 인용문'},{'basis':'guess'}):
            result=parse_summary(response(**invalid),text.speaker_context)
            self.assertEqual(result.speaker_mapping,{})
            self.assertEqual(result,'chunk0/speaker_0의 발표')

    def test_conflicting_names_are_not_applied(self):
        text=fixture();context={**text.speaker_context,'turns':[{'id':'t','speaker':'chunk0/speaker_0','text':'김민수 이영희'}]}
        data={'summary':'발표','speakers':[{'label':'chunk0/speaker_0','name':n,'turn_id':'t','evidence':'김민수 이영희','basis':'self_introduction'} for n in ('김민수','이영희')]}
        self.assertEqual(parse_summary(json.dumps(data),context).speaker_mapping,{})

    def test_context_roundtrip_rejects_changed_text_and_other_engine(self):
        text=fixture()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'context.json';save_context(p,text)
            self.assertIsInstance(restore_context(p,str(text),'elevenlabs/scribe-v2'),DiarizedText)
            self.assertNotIsInstance(restore_context(p,str(text)+'changed','elevenlabs/scribe-v2'),DiarizedText)
            self.assertNotIsInstance(restore_context(p,str(text),'openai/gpt-transcribe'),DiarizedText)

    def test_no_actual_labels_or_incomplete_units_do_not_enable(self):
        self.assertIsNone(label_units({'text':'hello','words':[{'text':'hello'}]},0,0,False,str))
        self.assertIsNone(label_units({'text':'hello missing','words':[{'text':'hello','speaker_id':'0'}]},0,0,False,str))
        labelled=label_units({'text':'hello','words':[{'text':'hello','speaker_id':'0'}]},1,30,False,str)
        self.assertEqual(labelled[0],'chunk1/0: hello')

    def test_unlabelled_chunk_is_kept_in_summary_context(self):
        from src.core.speech.transcribers.modern import ModernTranscriber
        from src.core.config.settings import Config
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'source.wav';source.write_bytes(b'fixture')
            replies=[{'text':'저는 김민수입니다.','words':[{'text':'저는 김민수입니다.','start':0,'speaker_id':'0'}]},
                     {'text':'화자 레이블이 없는 중요한 후반부'}]
            def ffmpeg(args,**kwargs):Path(args[-1]).write_bytes(b'fixture')
            from src.core.speech.adapters import ModelSpec
            with patch('src.core.speech.adapters.policy',return_value=(ModelSpec('elevenlabs/scribe-v2','unsupported'),'auto',True)),patch('src.core.speech.transcribers.modern.get_audio_duration',return_value=60),patch('src.core.speech.transcribers.modern.subprocess.run',side_effect=ffmpeg),patch('src.core.speech.transcribers.modern.stage',return_value={'options':{'provider_options':{'elevenlabs':{'diarize':True}}}}),patch('src.core.speech.transcribers.modern.route',return_value=('openrouter','elevenlabs/scribe-v2')),patch('src.core.speech.transcribers.modern.post',side_effect=replies):
                config=type('TempConfig',(Config,),{'TRANSCRIPT_PATH':Path(d)/'transcripts'})
                result=ModernTranscriber(config,'elevenlabs/scribe-v2').transcribe(str(source))
            self.assertEqual(result.speaker_context['turns'][-1]['text'],'화자 레이블이 없는 중요한 후반부')
            self.assertIsNone(result.speaker_context['turns'][-1]['speaker'])

    def test_plain_transcript_uses_original_summary_one_call(self):
        from types import SimpleNamespace
        reply=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='일반 요약'))])
        with patch('src.core.postprocess.summary.text_available',return_value=True),patch('src.core.postprocess.summary.TextClient') as factory:
            factory.return_value.chat.completions.create.return_value=reply
            self.assertEqual(generate_summary('화자 분리 없는 본문'),'일반 요약')
            self.assertEqual(factory.return_value.chat.completions.create.call_count,1)
            self.assertNotIn('self_introduction',str(factory.return_value.chat.completions.create.call_args))
