"""Explicit model capabilities and transport-specific normalization."""
from dataclasses import dataclass
import httpx
from typing import TypedDict

class NormalizedTranscript(TypedDict,total=False):
    text:str
    words:list
    segments:list
    diarization_status:str

from src.core.providers.models import ASR_MODELS,credential,post
from src.core.speech.checkpoint import ASRResponseError,response_text,write_json

@dataclass(frozen=True)
class ModelSpec:
    model: str
    diarization: str
    default_provider: str='openrouter'

REGISTRY={m:ModelSpec(m,'supported' if m=='elevenlabs/scribe-v2' else ('unsupported' if 'whisper' in m else 'unverified'), 'elevenlabs' if m=='elevenlabs/scribe-v2' else 'auto') for m in ASR_MODELS}

class SpeechAdapter:
    def normalize(self,data)->NormalizedTranscript:
        if not isinstance(data,dict):raise ASRResponseError('invalid ASR response envelope')
        result=dict(data)
        for field in ('words','segments'):
            units=data.get(field)
            if isinstance(units,list):
                result[field]=[{**u,'text':u.get('text',u.get('word','')),
                    'speaker_id':next((u[k] for k in ('speaker_id','speaker','speaker_label') if u.get(k) is not None),None)} for u in units if isinstance(u,dict)]
        result['text']=response_text(result)
        for unit in result.get('words') or result.get('segments') or []:
            if unit.get('speaker_id') is not None:unit['speaker_id']=str(unit['speaker_id'])
        result['diarization_status']='present' if any(u.get('speaker_id') is not None for u in result.get('words') or result.get('segments') or []) else 'missing'
        return result

class OpenRouterSTTAdapter(SpeechAdapter):
    def request(self,path,model,options,diarize):
        import base64
        form={'model':model,'response_format':'verbose_json' if diarize else 'json'}
        if diarize:form['timestamp_granularities']=['word']
        if options.get('language'):form['language']=options['language']
        provider_options=options.get('provider_options')
        if provider_options:form['provider']={'options':provider_options,'allow_fallbacks':False}
        if diarize:
            form.setdefault('provider',{'allow_fallbacks':False}).setdefault('options',{}).setdefault('elevenlabs',{})['diarize']=True
        if path.stat().st_size>25_000_000:raise ASRResponseError('OpenRouter upload limit exceeded; select ElevenLabs direct. Not split or retried.')
        return post('openrouter','audio/transcriptions',json_body={**form,'input_audio':{'data':base64.b64encode(path.read_bytes()).decode(),'format':path.suffix.lstrip('.').lower()}})

class UploadProgress:
    def __init__(self,stream,total):self.stream=stream;self.total=total;self.sent=0;self.last=-1
    def __getattr__(self,name):return getattr(self.stream,name)
    def read(self,size=-1):
        data=self.stream.read(size);self.sent+=len(data)
        percent=min(100,int(self.sent*100/max(1,self.total)))
        if percent//10!=self.last:
            self.last=percent//10;print(f'Upload {percent}% (client bytes: {self.sent}/{self.total})',flush=True)
        return data

class ElevenLabsScribeAdapter(SpeechAdapter):
    def request(self,path,model,options,diarize):
        key=credential('elevenlabs')
        if not key:raise ASRResponseError('Configure providers.elevenlabs.api_key_file (ELEVENLABS_API_KEY)')
        if path.stat().st_size>3_000_000_000:raise ASRResponseError('ElevenLabs input exceeds 3 GB; not split')
        form={'model_id':'scribe_v2','diarize':str(diarize).lower(),'timestamps_granularity':'word'}
        for k in ('tag_audio_events','no_verbatim'):
            value=(options.get('provider_options') or {}).get('elevenlabs',{}).get(k,False)
            form[k]=str(value).lower()
        if options.get('language'):form['language_code']=options['language']
        try:
            with path.open('rb') as audio,httpx.Client(timeout=httpx.Timeout(options.get('request_timeout_seconds',1800),connect=10)) as client:
                response=client.post('https://api.elevenlabs.io/v1/speech-to-text',headers={'xi-api-key':key},data=form,files={'file':(path.name,UploadProgress(audio,path.stat().st_size))})
            if response.status_code>=400:raise ASRResponseError('ElevenLabs HTTP '+str(response.status_code)+'; not retried')
            return response.json()
        except httpx.HTTPError:raise ASRResponseError('ElevenLabs request outcome uncertain; not retried') from None

def policy(model,options,provider='auto'):
    spec=REGISTRY[model]
    if provider=='auto':provider=spec.default_provider
    old=(options.get('provider_options') or {}).get('elevenlabs',{}).get('diarize') if model=='elevenlabs/scribe-v2' else None
    enabled=options.get('diarize')
    if enabled is not None and old is not None and enabled!=old:raise ASRResponseError('Conflicting diarization options')
    enabled=enabled if enabled is not None else (old if old is not None else spec.diarization=='supported')
    if enabled and spec.diarization!='supported':raise ASRResponseError('Diarization not supported or unverified for '+model)
    allowed={'openrouter','auto'}
    if model=='elevenlabs/scribe-v2':allowed={'openrouter','elevenlabs'}
    if model in ('openai/gpt-transcribe','openai/whisper-1'):allowed.add('openai')
    if provider not in allowed:raise ASRResponseError('Unsupported model/provider binding: '+model+'/'+provider)
    if provider=='elevenlabs' and model!='elevenlabs/scribe-v2':raise ASRResponseError('Model not supported by ElevenLabs adapter')
    return spec,provider,enabled


def assemble(raws,model,adapter,timestamps=True,diarize=True,chunk_seconds=30):
    from src.core.speech.labels import label_units,DiarizedText,digest
    from src.core.speech.audio import format_timestamp
    from src.core.speech.checkpoint import ASRResult
    parts=[];turns=[];spans=[];issues=[];position=0
    for index,raw in raws:
        data=adapter.normalize(raw);text=data['text'];offset=index*chunk_seconds
        if not text.strip():
            issues.append({'chunk':index,'start':offset,'code':'empty_asr_response'})
            rendered=f'[{format_timestamp(offset)}] [미전사 구간: 인식 결과 없음; 확인 필요]'
            labelled=None
        else:
            labelled=label_units(data,index,offset,timestamps,format_timestamp) if diarize else None
            rendered=labelled[0] if labelled else (f'[{format_timestamp(offset)}] ' if timestamps else '')+text
        if labelled:
            turns.extend(labelled[1]);spans.extend({**s,'start':s['start']+position,'end':s['end']+position} for s in labelled[2])
        else:
            turns.append({'id':f'chunk{index}:unlabelled','speaker':None,'text':rendered})
            if diarize and text.strip():issues.append({'code':'diarization_missing','chunk':index})
        parts.append(rendered);position+=len(rendered)+1
    text='\n'.join(parts)
    result=DiarizedText(text,{'version':2,'engine':model,'text_sha256':digest(text),'turns':turns,'spans':spans}) if spans else ASRResult(text)
    result.asr_issues=issues

    return result


def single_request(config,source,model,options,provider,enabled,timestamps,refresh=False):
    from src.core.speech.audio import get_audio_duration
    from src.core.speech.checkpoint import Checkpoint
    import time,threading
    if get_audio_duration(str(source))>36000:raise ASRResponseError('Input exceeds 10 hour limit; not split')
    adapter=ElevenLabsScribeAdapter() if provider=='elevenlabs' else OpenRouterSTTAdapter()
    cache=Checkpoint(config.TRANSCRIPT_PATH,source,{'version':2,'provider':provider,'model':model,'options':options,'mode':'single'})
    print('Single request; transcript streaming disabled. ASR progress: '+str(cache.root),flush=True)
    if cache.has(0) and not refresh:raw=cache.read(0)
    else:
        done=threading.Event();started=time.monotonic()
        def waiting():
            while not done.wait(5):print(f'Server response pending: {int(time.monotonic()-started)}s (server percentage unavailable)',flush=True)
        thread=threading.Thread(target=waiting,daemon=True);thread.start()
        try:raw=adapter.request(source,model,options,enabled)
        finally:done.set();thread.join()
        cache.write(0,raw)
    result=assemble([(0,raw)],model,adapter,timestamps,enabled)
    if all(i.get('code')=='empty_asr_response' for i in result.asr_issues) and not adapter.normalize(raw)['text'].strip():raise ASRResponseError('No ASR text; original response saved at '+str(cache.root))
    from src.core.speech.labels import friendly_speakers
    result=friendly_speakers(result)
    result.asr_cache=str(cache.root)
    print(str(result),flush=True)
    return result
