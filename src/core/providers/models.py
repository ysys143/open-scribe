"""Model/API compatibility for the legacy CLI. No UI, job-v3, or Keychain."""
import base64
import json
import os
from pathlib import Path
import re
import shlex
import stat
from types import SimpleNamespace
import httpx

ASR_MODELS=('elevenlabs/scribe-v2','nvidia/nemotron-3.5-transcribe','openai/gpt-transcribe',
            'openai/whisper-1','openai/whisper-large-v3','openai/whisper-large-v3-turbo')
TEXT_MODELS=('openai/gpt-6-luna','anthropic/claude-haiku-5.5','deepseek/deepseek-v4.1-flash')


def settings():
    from src.core.config.document import load_settings
    return load_settings()


def stage(name):
    return settings().get('stages',{}).get(name,{})


def model(name):
    return stage(name).get('model') or ('elevenlabs/scribe-v2' if name=='asr' else TEXT_MODELS[0])


def credential(provider):
    document=settings()
    config=document.get('providers',{}).get(provider) or document.get('integrations',{}).get(provider,{})
    name=config.get('api_key_env',provider.upper()+'_API_KEY')
    path=config.get('api_key_file')
    if path:
        path=Path(path).expanduser()
        if not path.is_absolute():
            from src.core.config.document import settings_path
            path=settings_path().parent/path
        try:
            with path.open() as stream:
                meta=os.fstat(stream.fileno())
                if not stat.S_ISREG(meta.st_mode) or meta.st_uid!=os.getuid() or meta.st_mode & 0o077:
                    raise ValueError('credential file requires owner-only permissions')
                values=[]
                for line in stream:
                    match=re.match(r'\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$',line)
                    if match and match[1]==name:
                        parts=shlex.split(match[2],comments=True,posix=True)
                        if len(parts)!=1 or '$' in parts[0] or '`' in parts[0]:raise ValueError('literal credential required')
                        values.append(parts[0])
            if len(values)>1:raise ValueError('duplicate credential assignment')
            value=values[0] if values else None
        except Exception:
            raise ValueError('cannot read configured credential file') from None
    else:value=os.getenv(name)
    if value and any(c.isspace() or ord(c)<32 or ord(c)==127 for c in value):raise ValueError('invalid credential')
    return value


def route(selected):
    native={'openai/gpt-6-luna':('openai','gpt-6-luna'),
            'openai/gpt-transcribe':('openai','gpt-transcribe'),
            'anthropic/claude-haiku-5.5':('anthropic','claude-haiku-5-5')}.get(selected)
    if native and credential(native[0]):return native
    if '/' not in selected:return 'openai',selected
    return 'openrouter',selected


def post(provider,endpoint,*,json_body=None,data=None,files=None):
    key=credential(provider)
    if not key:raise ValueError(provider+' credential missing; configure providers.'+provider+'.api_key_file')
    base={'openai':'https://api.openai.com/v1','anthropic':'https://api.anthropic.com/v1','openrouter':'https://openrouter.ai/api/v1'}[provider]
    headers=({'x-api-key':key,'anthropic-version':'2023-06-01'} if provider=='anthropic' else {'Authorization':'Bearer '+key})
    try:
        with httpx.Client(timeout=httpx.Timeout(180,connect=10)) as client:
            response=client.post(base+'/'+endpoint,headers=headers,json=json_body,data=data,files=files)
        if response.status_code>=400:raise ValueError(provider+' HTTP '+str(response.status_code)+'; not retried')
        return response.json()
    except (httpx.HTTPError,json.JSONDecodeError):
        raise ValueError(provider+' request failed; outcome uncertain, not retried') from None


class TextClient:
    def __init__(self,task):
        self.task=task
        self.chat=SimpleNamespace(completions=self)
    def create(self,**body):
        provider,selected=route(body['model'])
        body={**body,'model':selected}
        effort=stage(self.task).get('options',{}).get('effort','medium')
        limit=body.pop('max_completion_tokens',None) or body.pop('max_tokens',8192)
        body.pop('temperature',None)
        if provider=='openai':
            body.update(max_completion_tokens=limit)
            if selected.startswith(('gpt-6','gpt-5')):
                body.update(reasoning_effort=effort,service_tier='default')
                if selected=='gpt-6-luna':body['prompt_cache_options']={'mode':'explicit','ttl':'30m'}
            data=post(provider,'chat/completions',json_body=body)
            text=data['choices'][0]['message'].get('content')
        elif provider=='anthropic':
            messages=body.pop('messages')
            body.update(system='\n\n'.join(m['content'] for m in messages if m['role']=='system'),
                        messages=[m for m in messages if m['role']!='system'],max_tokens=limit,
                        thinking={'type':'adaptive'},output_config={'effort':effort},service_tier='standard_only')
            data=post(provider,'messages',json_body=body)
            text=''.join(p['text'] for p in data.get('content',[]) if p.get('type')=='text')
        else:
            body.update(max_tokens=limit,reasoning={'effort':effort},provider={'allow_fallbacks':False})
            data=post(provider,'chat/completions',json_body=body)
            text=data['choices'][0]['message'].get('content')
        from src.core.config.document import load_settings
        from src.core.speech.checkpoint import write_json
        import time
        from pathlib import Path
        destination=Path(load_settings()['paths']['data'])/'model-responses'/f'{self.task}-{time.time_ns()}.json'
        write_json(destination,{'provider':provider,'model':selected,'limit':limit,'response':data})
        if not isinstance(text,str) or not text.strip():
            reason=(data.get('choices') or [{}])[0].get('finish_reason',data.get('stop_reason'))
            raise ValueError(f'empty model response; finish_reason={reason}; diagnostic={destination}; not retried')
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def text_available(task):
    return bool(credential(route(model(task))[0]))
