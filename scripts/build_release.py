"""Build a deterministic source distribution from an explicit, non-secret allowlist."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[1]
INCLUDE=('src','bot','scripts','tests','docs','.agents','main.py','requirements.txt','requirements.cloud.txt','settings.example.json','README.md','CHANGELOG.md','LICENSE','Makefile','Dockerfile','.dockerignore')


def build(version,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    archive=output/f'open-scribe-{version}.tar.gz'
    with archive.open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as zipped,tarfile.open(fileobj=zipped,mode='w') as tar:
        for included in INCLUDE:
            root=ROOT/included
            if not root.exists():continue
            paths=sorted(root.rglob('*')) if root.is_dir() else [root]
            for path in paths:
                relative=path.relative_to(ROOT)
                if any(p in {'__pycache__','.venv','.git','node_modules'} for p in relative.parts) or path.suffix=='.pyc':continue
                if path.name.startswith('.env') or path.name.endswith('.db'):continue
                if not path.is_file():continue
                data=path.read_bytes();info=tarfile.TarInfo(f'open-scribe-{version}/'+relative.as_posix())
                info.size=len(data);info.mode=0o755 if path.suffix=='.sh' else 0o644
                info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
                tar.addfile(info,io.BytesIO(data))
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    (output/'SHA256SUMS').write_text(f'{digest}  {archive.name}\n')
    print(f'{digest}  {archive}')
    return archive,digest


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('version');parser.add_argument('--output',default='dist')
    args=parser.parse_args();build(args.version,args.output)
