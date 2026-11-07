"""Persist successful ASR responses so a later failure does not discard paid work."""
import hashlib
import json
import os
from pathlib import Path
import tempfile


def file_sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()


def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream:
            json.dump(value,stream,ensure_ascii=False,indent=2);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)


class Checkpoint:
    def __init__(self,root,source,contract):
        identity={'source_sha256':file_sha(source),'contract':contract}
        key=hashlib.sha256(json.dumps(identity,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        self.root=Path(root)/'.asr-cache'/key
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        write_json(self.root/'source.json',identity)
    def has(self,index):return (self.root/f'{index}.json').is_file()
    def read(self,index):
        path=self.root/f'{index}.json'
        if not path.exists():return None
        return json.loads(path.read_text(encoding='utf-8'))
    def write(self,index,data):
        if self.has(index):
            import shutil,time
            previous=self.root/'previous';previous.mkdir(exist_ok=True,mode=0o700)
            shutil.copy2(self.root/f'{index}.json',previous/f'{index}-{time.time_ns()}.json')
        write_json(self.root/f'{index}.json',data)


class ASRResult(str):
    pass


class ASRResponseError(RuntimeError):
    pass


def response_text(data):
    if not isinstance(data,dict) or 'error' in data:raise ASRResponseError('invalid ASR response envelope')
    text=data.get('text')
    if text is not None and not isinstance(text,str):raise ASRResponseError('invalid ASR text field')
    if isinstance(text,str) and text.strip():return text
    units=data.get('words') or data.get('segments') or []
    if not isinstance(units,list):raise ASRResponseError('invalid ASR units')
    if units and all(isinstance(u,dict) and isinstance(u.get('text'),str) for u in units):
        words=[u['text'] for u in units]
        separator='' if any(w.isspace() for w in words) else ' '
        recovered=separator.join(words)
        if recovered.strip():return recovered
    if isinstance(text,str) or ('text' in data and text is None) or any(isinstance(data.get(field),list) for field in ('words','segments')):return ''
    raise ASRResponseError('ASR response has neither text nor usable words/segments')
