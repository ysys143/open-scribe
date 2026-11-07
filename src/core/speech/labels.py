"""Request-scoped ASR labels and replacement restricted to recorded label spans."""
import hashlib
import json
from pathlib import Path


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class DiarizedText(str):
    def __new__(cls,text,context):
        value=super().__new__(cls,text)
        value.speaker_context=context
        return value


def label_units(data,index,offset,timestamps,stamp):
    units=data.get('words') or data.get('segments') or []
    if not any(u.get('speaker_id',u.get('speaker')) is not None for u in units):return None
    # Do not drop source text when the provider's labelled units are incomplete.
    if ''.join(''.join(u.get('text','') for u in units).split())!=''.join(data['text'].split()):return None
    turns=[]
    explicit_spacing=any(u.get('type')=='spacing' or u.get('text','').isspace() for u in units)
    for unit in units:
        text=unit.get('text','')
        if not text:continue
        speaker=unit.get('speaker_id',unit.get('speaker'))
        if unit.get('type')=='spacing' and turns:speaker=turns[-1]['raw_speaker']
        if turns and turns[-1]['raw_speaker']==speaker:
            # Scribe includes explicit spacing events; segment-only responses may not.
            separator='' if explicit_spacing else ' '
            turns[-1]['text']+=separator+text
        else:
            turns.append({'raw_speaker':speaker,'text':text,'start':unit.get('start')})
    text_parts=[];records=[];spans=[];position=0
    for number,turn in enumerate(turns):
        text=turn['text'].strip()
        if not text:continue
        speaker=turn['raw_speaker']
        label=f'chunk{index}/{speaker}' if speaker is not None else None
        prefix=''
        if timestamps and isinstance(turn['start'],(int,float)):
            prefix=f'[{stamp(offset+turn["start"])}] '
        if label:
            spans.append({'start':position+len(prefix),'end':position+len(prefix)+len(label),'label':label})
            prefix+=label+': '
        rendered=prefix+text
        text_parts.append(rendered);position+=len(rendered)+1
        records.append({'id':f'chunk{index}:turn{number}','speaker':label,'text':text})
    return '\n'.join(text_parts),records,spans


def save_context(path,text):
    context=getattr(text,'speaker_context',None)
    if context:Path(path).write_text(json.dumps(context,ensure_ascii=False,indent=2),encoding='utf-8')


def restore_context(path,text,engine):
    try:
        context=json.loads(Path(path).read_text(encoding='utf-8'))
        if context['engine']==engine and context['text_sha256']==digest(text):return DiarizedText(text,context)
    except (OSError,ValueError,KeyError,TypeError):pass
    return text


def replace_names(text,mapping):
    context=getattr(text,'speaker_context',None)
    if not context or context['text_sha256']!=digest(text):raise ValueError('speaker context does not match transcript')
    result=str(text)
    for span in sorted(context['spans'],key=lambda s:s['start'],reverse=True):
        start,end,label=span['start'],span['end'],span['label']
        if result[start:end]!=label:raise ValueError('speaker label span changed')
        identity=span.get('speaker',label)
        if identity in mapping:result=result[:start]+mapping[identity]+result[end:]
    return result


def friendly_speakers(value):
    """Readable labels for one request, retaining stable IDs for name attribution."""
    import copy
    context=getattr(value,'speaker_context',None)
    if not context:return value
    context=copy.deepcopy(context)
    identities=list(dict.fromkeys(t['speaker'] for t in context['turns'] if t.get('speaker')))
    names={identity:f'화자 {i+1}' for i,identity in enumerate(identities)}
    parts=[];cursor=0;length=0;spans=[]
    for span in context['spans']:
        start,end,label=span['start'],span['end'],span['label']
        if value[start:end]!=label:raise ValueError('speaker label span changed')
        prefix=value[cursor:start];parts.append(prefix);length+=len(prefix)
        identity=span.get('speaker',label);display=names[identity]
        spans.append({'start':length,'end':length+len(display),'label':display,'speaker':identity})
        parts.append(display);length+=len(display);cursor=end
    parts.append(value[cursor:]);text=''.join(parts)
    context.update(version=3,spans=spans,display_labels=names,text_sha256=digest(text))
    result=DiarizedText(text,context)
    result.asr_issues=getattr(value,'asr_issues',[])
    return result
