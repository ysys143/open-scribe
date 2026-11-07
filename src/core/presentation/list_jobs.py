"""Read-only recent transcription listing; no inference or database initialization."""
import argparse
from pathlib import Path
import sqlite3


def positive(value):
    try:number=int(value)
    except ValueError:raise argparse.ArgumentTypeError('건수는 양의 정수여야 합니다.') from None
    if number<1:raise argparse.ArgumentTypeError('건수는 양의 정수여야 합니다.')
    return number


def recent(db_path,limit=10):
    path=Path(db_path).expanduser().resolve()
    if not path.is_file():return []
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as connection:
        connection.row_factory=sqlite3.Row
        if not connection.execute("SELECT 1 FROM sqlite_master WHERE name='transcription_jobs' AND type='table'").fetchone():return []
        return [dict(row) for row in connection.execute('''
            SELECT id,title,status,transcript_path,
                   COALESCE(completed_at,updated_at,created_at) AS date
            FROM transcription_jobs
            ORDER BY datetime(COALESCE(completed_at,updated_at,created_at)) DESC,id DESC LIMIT ?
        ''',(limit,))]


def clean(value):
    return ''.join(c if c.isprintable() else ' ' for c in str(value or ''))


def main(argv,db_path):
    parser=argparse.ArgumentParser(prog='scribe ls',description='최근 녹취 목록 (기본 10건)')
    parser.add_argument('n',nargs='?',default=10,type=positive,help='표시할 건수 (기본 10)')
    args=parser.parse_args(argv)
    try:rows=recent(db_path,args.n)
    except sqlite3.Error as error:
        import sys
        print('녹취 목록 조회 실패: '+str(error),file=sys.stderr);return 1
    if not rows:print('저장된 녹취가 없습니다.');return 0
    for row in rows:
        print(f'[{row["id"]}] {clean(row["date"])}  {clean(row["status"])}  {clean(row["title"]) or "(제목 없음)"}')
        if row['transcript_path']:print('  '+clean(row['transcript_path']))
    return 0
