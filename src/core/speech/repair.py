"""Offline replay of cached ASR responses. Never submits inference or publication."""
import argparse,json,sqlite3,subprocess,shlex
from pathlib import Path
from src.core.config.settings import Config
from src.core.speech.checkpoint import file_sha,write_json
from src.core.speech.adapters import assemble,OpenRouterSTTAdapter,ElevenLabsScribeAdapter
from src.core.speech.labels import save_context,digest
from src.core.presentation.files import sanitize_filename,copy_to_downloads

def main(argv):
    parser=argparse.ArgumentParser(prog='scr repair');parser.add_argument('job',type=int);parser.add_argument('--cache',type=Path)
    args=parser.parse_args(argv)
    with sqlite3.connect(Config.DB_PATH.as_uri()+'?mode=ro',uri=True) as c:
        c.row_factory=sqlite3.Row;row=c.execute('SELECT * FROM transcription_jobs WHERE id=?',(args.job,)).fetchone()
    if row is None:raise ValueError('Unknown job')
    row=dict(row);source=Path(row['url'])
    if not source.is_file():raise ValueError('Local source file required to verify cache identity')
    for line in subprocess.check_output(['ps','-axo','command'],text=True).splitlines():
        try:parts=shlex.split(line)
        except ValueError:continue
        if str(source) in parts and any(p.endswith('/main.py') for p in parts):raise ValueError('Transcription process still running; repair deferred')
    sha=file_sha(source);candidates=[]
    for p in ([args.cache] if args.cache else (Config.TRANSCRIPT_PATH/'.asr-cache').glob('*')):
        try:meta=json.loads((p/'source.json').read_text())
        except (OSError,ValueError):continue
        if meta['source_sha256']==sha and meta['contract']['model']==row['engine']:candidates.append((p,meta))
    if len(candidates)!=1:raise ValueError('Select exactly one matching cache with --cache')
    cache,meta=candidates[0];raws=[(int(p.stem),json.loads(p.read_text())) for p in cache.glob('*.json') if p.stem.isdigit()];raws.sort()
    if not raws:raise ValueError('No cached ASR responses')
    status=json.loads((cache/'status.json').read_text()) if (cache/'status.json').exists() else {}
    expected=status.get('total_chunks',len(raws))
    if [n for n,_ in raws]!=list(range(expected)):raise ValueError('Incomplete cache; no inference started')
    contract=meta['contract'];adapter=ElevenLabsScribeAdapter() if contract['provider']=='elevenlabs' else OpenRouterSTTAdapter()
    text=assemble(raws,row['engine'],adapter,True,True,contract.get('chunk_seconds',30))
    base=Config.TRANSCRIPT_PATH/f'{sanitize_filename(row["title"])}_job{args.job}_diarized';target=Path(str(base)+'.txt')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(str(text),encoding='utf-8');save_context(str(base)+'_diarization.json',text)
    write_json(str(base)+'_asr_status.json',{'text_sha256':digest(text),'issues':text.asr_issues,'cache_path':str(cache),'summary_regenerated':False})
    overall='partial' if text.asr_issues or not row['summary_completed'] else 'completed'
    with sqlite3.connect(Config.DB_PATH) as c:
        updated=c.execute('UPDATE transcription_jobs SET transcript_path=?,status=? WHERE id=? AND status=? AND transcript_path IS ?',(str(target),overall,args.job,row['status'],row['transcript_path']))
        if updated.rowcount!=1:raise ValueError('Job changed; repair output retained but job not modified')
    if Config.COPY_TO_DOWNLOADS:copy_to_downloads(target,Config.DOWNLOADS_PATH)
    print(f'{target}에 있는 화자 정보를 갱신했습니다. 요약·Notion은 재호출하지 않았습니다.')
    return 0
