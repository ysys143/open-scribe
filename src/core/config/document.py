"""Single non-secret settings document; credentials remain named file references."""
import copy
from functools import lru_cache
import json
import os
from pathlib import Path
import re


def settings_path():
    return Path(os.getenv('OPEN_SCRIBE_SETTINGS') or Path(os.getenv('XDG_CONFIG_HOME',Path.home()/'.config'))/'open-scribe/settings.json').expanduser().resolve()


def defaults():
    home=Path.home();root=Path(__file__).resolve().parents[3]
    def key(name):return {'api_key_env':name,'api_key_file':None}
    def text(language=None,enabled=None):
        result={'model':'openai/gpt-6-luna','options':{'effort':'medium','max_output_tokens':8192}}
        if language is not None:result['options']['language']=language
        if enabled is not None:result['enabled']=enabled
        return result
    return {'version':1,'copy_to_path':None,
        'paths':{'data':str(home/'.local/share/open-scribe'),'cache':str(home/'.cache/open-scribe'),
                 'audio':None,'video':None,'transcript':None,'temp':None,'database':None},
        'workers':{'min':1,'max':5},
        'output':{'stream':False,'downloads':True,'keep_audio':False,'video':False,'srt':False,'timestamp':True,'verbose':True,'debug':False},
        'whisper_cpp':{'model_path':str(root/'whisper.cpp/models/ggml-large-v3.bin'),'executable':str(root/'whisper.cpp/build/bin/whisper-cli')},
        'stages':{'asr':{'provider':'auto','model':'elevenlabs/scribe-v2','options':{'provider_options':None,'language':None,'diarize':None,'request_timeout_seconds':1800}},
                  'summary':text('auto',True),'translate':text('Korean',False),'correct':text(),'keywords':text()},
        'providers':{p:key(p.upper()+'_API_KEY') for p in ('openrouter','openai','anthropic','elevenlabs')},
        'integrations':{'notion':{**key('NOTION_API_KEY'),'enabled':False,'database_id':''},
                        'telegram':key('TELEGRAM_BOT_TOKEN'),'proxy':key('PROXY_URL'),'proxy_list':key('WEBSHARE_PROXY_LIST_URL')},
        'download':{'cookies_browser':'','remote_components':None,'player_clients':[]},
        'bot':{'port':8080,'temp_path':'/tmp/open-scribe'}}


def merge(base,patch,path='settings'):
    if not isinstance(patch,dict):raise ValueError(path+': object required')
    result=copy.deepcopy(base)
    for key,value in patch.items():
        if key not in base:raise ValueError(path+'.'+key+': unknown setting')
        result[key]=merge(base[key],value,path+'.'+key) if isinstance(base[key],dict) else copy.deepcopy(value)
    return result


def pairs(items):
    result={}
    for name,value in items:
        if name in result:raise ValueError('duplicate settings key: '+name)
        result[name]=value
    return result


def validate(data,path):
    result=merge(defaults(),data)
    def check(ok,field):
        if not ok:raise ValueError(field+': invalid setting')
    check(type(result['version']) is int and result['version']==1,'version')
    for name,value in result['output'].items():check(type(value) is bool,'output.'+name)
    for name in ('summary','translate'):check(type(result['stages'][name]['enabled']) is bool,'stages.'+name+'.enabled')
    check(all(type(v) is int and v>0 for v in result['workers'].values()) and result['workers']['min']<=result['workers']['max'],'workers')
    check(type(result['bot']['port']) is int and 1<=result['bot']['port']<=65535,'bot.port')
    for name,value in result['stages'].items():
        check(isinstance(value['model'],str) and bool(value['model'].strip()),'stages.'+name+'.model')
        if name!='asr':check(value['options']['effort'] in ('low','medium','high','xhigh','max'),'stages.'+name+'.options.effort')
    for name in ('summary','translate'):check(isinstance(result['stages'][name]['options']['language'],str) and bool(result['stages'][name]['options']['language']),'stages.'+name+'.options.language')
    check(result['stages']['asr']['options']['language'] is None or isinstance(result['stages']['asr']['options']['language'],str) and re.fullmatch('[A-Za-z]{2}',result['stages']['asr']['options']['language']),'stages.asr.options.language')
    options=result['stages']['asr']['options']['provider_options']
    check(options is None or isinstance(options,dict) and all(isinstance(v,dict) for v in options.values()),'stages.asr.options.provider_options')
    check(result['stages']['asr']['provider'] in ('auto','openrouter','openai','elevenlabs'),'stages.asr.provider')
    check(result['stages']['asr']['options']['diarize'] is None or type(result['stages']['asr']['options']['diarize']) is bool,'stages.asr.options.diarize')
    check(type(result['stages']['asr']['options']['request_timeout_seconds']) is int and result['stages']['asr']['options']['request_timeout_seconds']>0,'stages.asr.options.request_timeout_seconds')
    for name in ('summary','translate','correct','keywords'):
        limit=result['stages'][name]['options']['max_output_tokens'];check(type(limit) is int and limit>0,'stages.'+name+'.options.max_output_tokens')
    notion=result['integrations']['notion'];check(type(notion['enabled']) is bool and isinstance(notion['database_id'],str),'integrations.notion')
    for name in ('cookies_browser',):check(isinstance(result['download'][name],str),'download.'+name)
    for name in ('remote_components','player_clients'):
        value=result['download'][name];check(value is None and name=='remote_components' or isinstance(value,list) and all(isinstance(v,str) and v for v in value),'download.'+name)
    def resolve(value,field,nullable=False):
        if value is None and nullable:return None
        check(isinstance(value,str) and bool(value.strip()),field)
        value=Path(value).expanduser()
        return str((path.parent/value).resolve() if not value.is_absolute() else value.resolve())
    result['copy_to_path']=resolve(result['copy_to_path'],'copy_to_path',True)
    for name,value in result['paths'].items():result['paths'][name]=resolve(value,'paths.'+name,name not in ('data','cache'))
    data_path=Path(result['paths']['data'])
    for name,suffix in {'audio':'audio','video':'video','transcript':'transcript','temp':'temp_audio','database':'transcription_jobs.db'}.items():
        if result['paths'][name] is None:result['paths'][name]=str(data_path/suffix)
    for name,value in result['whisper_cpp'].items():result['whisper_cpp'][name]=resolve(value,'whisper_cpp.'+name)
    result['bot']['temp_path']=resolve(result['bot']['temp_path'],'bot.temp_path')
    for group in ('providers','integrations'):
        for name,entry in result[group].items():
            check(isinstance(entry['api_key_env'],str) and re.fullmatch('[A-Z_][A-Z0-9_]*',entry['api_key_env']),group+'.'+name+'.api_key_env')
            entry['api_key_file']=resolve(entry['api_key_file'],group+'.'+name+'.api_key_file',True)
    return result


@lru_cache(maxsize=8)
def _read(path):
    path=Path(path)
    raw=json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=pairs) if path.exists() else {}
    return validate(raw,path)


def load_settings(path=None):
    """Each selected file is snapshotted for the life of this process."""
    return copy.deepcopy(_read(str(Path(path).expanduser().resolve() if path else settings_path())))
