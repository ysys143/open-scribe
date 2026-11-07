"""Updated hosted speech models using the legacy transcriber interface."""
from pathlib import Path
import base64
import math
import subprocess
import tempfile
from src.core.speech.transcribers.base import BaseTranscriber
from src.core.providers.models import ASR_MODELS, credential, post, route, stage
from src.core.speech.audio import get_audio_duration, format_timestamp


class ModernTranscriber(BaseTranscriber):
    def __init__(self,config,selected):
        super().__init__(config)
        if selected not in ASR_MODELS:raise ValueError('unsupported hosted ASR model')
        self.selected=selected
    @property
    def name(self):return self.selected
    @property
    def requires_api_key(self):return True
    def is_available(self):
        from src.core.speech.adapters import policy
        spec,provider,_=policy(self.selected,stage('asr').get('options',{}),stage('asr').get('provider','auto'))
        return bool(credential(route(self.selected)[0] if provider=='auto' else provider))
    def transcribe(self,audio_path,stream=False,return_timestamps=False,**kwargs):
        if not self.validate_audio_file(audio_path):raise ValueError('audio file is missing')
        duration=get_audio_duration(audio_path)
        if not math.isfinite(duration) or duration<=0:raise ValueError('audio duration is unavailable')
        from src.core.speech.adapters import policy,single_request,OpenRouterSTTAdapter
        settings=stage('asr');opts=settings.get('options',{})
        spec,chosen,enabled=policy(self.selected,opts,settings.get('provider','auto'))
        if spec.diarization=='supported':
            return single_request(self.config,Path(audio_path),self.selected,opts,chosen,enabled,return_timestamps,kwargs.get('refresh',False))
        provider,selected=route(self.selected)
        if chosen!='auto':
            provider=chosen
            selected=self.selected if chosen=='openrouter' else self.selected.split('/',1)[-1]
        options=stage('asr').get('options',{}).get('provider_options')
        from src.core.speech.labels import DiarizedText,digest,label_units
        from src.core.speech.checkpoint import Checkpoint,ASRResult,ASRResponseError,response_text,write_json
        checkpoint=Checkpoint(self.config.TRANSCRIPT_PATH,audio_path,
            {'version':1,'provider':provider,'model':selected,'options':stage('asr').get('options',{}),
             'chunk_seconds':30,'encoding':'pcm16-16000-mono'})
        print(f'ASR progress: {checkpoint.root}',flush=True)
        parts=[];turns=[];spans=[];position=0;issues=[];usable=0
        diarization_model=enabled
        with tempfile.TemporaryDirectory(prefix='scribe-audio-') as temporary:
            count=math.ceil(duration/30)
            for index in range(count):
                offset=index*30
                path=Path(temporary)/f'{index}.wav'
                subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-ss',str(offset),'-i',str(audio_path),
                                '-t',str(min(30,duration-offset)),'-vn','-ar','16000','-ac','1','-c:a','pcm_s16le',str(path)],
                               check=True,capture_output=True,timeout=60)
                print(f'[{self.name}] Processing chunk {index+1}/{count}',flush=True)
                form={'model':selected,'response_format':'json'}
                language=stage('asr').get('options',{}).get('language')
                if language:form['languages[]' if provider=='openai' and selected=='gpt-transcribe' else 'language']=language.lower()
                if self.selected=='elevenlabs/scribe-v2':
                    form.update(response_format='verbose_json',timestamp_granularities=['word'])
                cached=not kwargs.get('refresh') and checkpoint.has(index)
                data=checkpoint.read(index) if cached else None
                if not cached:
                    if provider=='openrouter' and options:
                        form['provider']={'options':options,'allow_fallbacks':False}
                        data=post(provider,'audio/transcriptions',json_body={**form,'input_audio':{
                            'data':base64.b64encode(path.read_bytes()).decode('ascii'),'format':'wav'}})
                    else:
                        if 'timestamp_granularities' in form:
                            form['timestamp_granularities[]']=form.pop('timestamp_granularities')[0]
                        with path.open('rb') as audio:
                            data=post(provider,'audio/transcriptions',data=form,files={'file':(path.name,audio,'audio/wav')})
                    checkpoint.write(index,data)
                else:print(f'[{self.name}] Cached chunk {index+1}/{count}',flush=True)
                try:
                    data=OpenRouterSTTAdapter().normalize(data)
                    text=response_text(data)
                except ASRResponseError as error:
                    raise ASRResponseError(f'{error}; response saved at {checkpoint.root}/{index}.json; not retried') from None
                if not text.strip():
                    issue={'chunk':index,'start':offset,'end':min(duration,offset+30),'code':'empty_asr_response'}
                    issues.append(issue)
                    rendered=f'[{format_timestamp(offset)}] [미전사 구간: {format_timestamp(offset)}–{format_timestamp(min(duration,offset+30))}; 무음 여부·인식 실패 확인 필요]'
                    parts.append(rendered);position+=len(rendered)+1
                    turns.append({'id':f'chunk{index}:untranscribed','speaker':None,'text':rendered})
                    print(rendered,flush=True)
                    write_json(checkpoint.root/'status.json',{'processed_chunks':index+1,'total_chunks':count,'issues':issues})
                    continue
                usable+=1
                data=OpenRouterSTTAdapter().normalize({**data,'text':text})
                rendered=text.strip()
                labelled=label_units(data,index,offset,return_timestamps,format_timestamp) if diarization_model else None
                if labelled:
                    rendered,chunk_turns,chunk_spans=labelled
                    turns.extend(chunk_turns)
                    spans.extend({**span,'start':span['start']+position,'end':span['end']+position} for span in chunk_spans)
                elif return_timestamps:
                    units=data.get('segments') or data.get('words') or []
                    lines=[]
                    for unit in units:
                        if not isinstance(unit.get('start'),(int,float)) or not isinstance(unit.get('text'),str):continue
                        speaker=unit.get('speaker_id',unit.get('speaker'))
                        label=f'{speaker}: ' if speaker is not None else ''
                        lines.append(f'[{format_timestamp(offset+unit["start"])}] '+label+unit['text'].strip())
                    rendered='\n'.join(lines) if lines else f'[{format_timestamp(offset)}] '+rendered
                if not labelled:
                    turns.append({'id':f'chunk{index}:unlabelled','speaker':None,'text':data['text']})
                parts.append(rendered)
                position+=len(rendered)+1
                if stream:print(rendered,flush=True)
        text='\n'.join(parts)
        write_json(checkpoint.root/'status.json',{'processed_chunks':count,'total_chunks':count,'issues':issues,'usable_chunks':usable})
        if not usable:
            raise ASRResponseError(f'No speech text returned for any chunk; responses saved at {checkpoint.root}; not retried')
        result=(DiarizedText(text,{'version':1,'engine':self.selected,'text_sha256':digest(text),
                                 'turns':turns,'spans':spans}) if spans else ASRResult(text))
        result.asr_issues=issues;result.asr_cache=str(checkpoint.root)
        return result
