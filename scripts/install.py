"""Install an isolated source runtime; never load or copy credentials."""
from pathlib import Path
import os,sys,shutil,subprocess,tempfile,time
source=Path(sys.argv[1]).resolve();external=sys.argv[2];upgrade=sys.argv[3]=='1'
target=Path(os.getenv('OPEN_SCRIBE_HOME',Path.home()/'.local/lib/open-scribe')).expanduser().resolve()
bin_dir=Path(os.getenv('OPEN_SCRIBE_BIN_DIR',Path.home()/'.local/bin')).expanduser()
if target==source:raise SystemExit('source and target must differ')
if target.exists() and not upgrade:raise SystemExit('target exists; use --upgrade')
if target.exists():
    # Existing jobs-v3 processes may still import code at this exact path.
    db=Path(os.getenv('XDG_DATA_HOME',Path.home()/'.local/share'))/'open-scribe/transcription_jobs.db'
    if db.exists():
        import sqlite3
        with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as c:
            if c.execute("SELECT 1 FROM sqlite_master WHERE name='jobs_v3'").fetchone() and c.execute('SELECT 1 FROM jobs_v3 WHERE lease>? LIMIT 1',(time.time(),)).fetchone():raise SystemExit('active execution lease; choose a separate OPEN_SCRIBE_HOME')
target.parent.mkdir(parents=True,exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix=target.name+'.candidate-',dir=target.parent))
for name in ('src','bot','main.py','requirements.txt','requirements.cloud.txt','README.md','LICENSE'):
    path=source/name
    if path.is_dir():shutil.copytree(path,stage/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','.env','.env.*'))
    elif path.is_file():shutil.copy2(path,stage/name)
if external:
    external=Path(external).expanduser().resolve()
    if not (external/'bin/python').is_file():raise SystemExit('external venv Python is missing')
    (stage/'.venv').symlink_to(external,target_is_directory=True)
else:
    subprocess.run([sys.executable,'-m','venv',str(stage/'.venv')],check=True)
    subprocess.run([str(stage/'.venv/bin/python'),'-m','pip','install','-r',str(stage/'requirements.txt')],check=True)
subprocess.run([str(stage/'.venv/bin/python'),'-B',str(stage/'main.py'),'--help'],check=True,stdout=subprocess.DEVNULL)
subprocess.run([str(stage/'.venv/bin/python'),'-B',str(stage/'main.py'),'config','validate'],check=True,stdout=subprocess.DEVNULL)
backup=None
if target.exists():
    backup=target.with_name(target.name+'.before-'+str(time.time_ns()));target.rename(backup)
try:
    stage.rename(target)
    subprocess.run([str(target/'.venv/bin/python'),'-B',str(target/'main.py'),'--help'],check=True,stdout=subprocess.DEVNULL)
except BaseException:
    if target.exists():target.rename(stage)
    if backup:backup.rename(target)
    raise
bin_dir.mkdir(parents=True,exist_ok=True)
launcher=bin_dir/'scribe';temporary=bin_dir/('.scribe-'+str(time.time_ns()))
import shlex
content='#!/bin/bash\nset -e\nscribe_home='+shlex.quote(str(target))+'\nexec "$scribe_home/.venv/bin/python" -B "$scribe_home/main.py" "$@"\n'
temporary.write_text(content);temporary.chmod(0o755)
if launcher.exists() or launcher.is_symlink():
    saved=bin_dir/('scribe.before-'+str(time.time_ns()));shutil.copy2(launcher,saved)
os.replace(temporary,launcher)
for name in ('scr','openscribe'):
    shortcut=bin_dir/name
    if shortcut.exists() and not shortcut.is_symlink():raise SystemExit(name+' is a regular file; inspect before changing')
    if shortcut.is_symlink():shortcut.unlink()
    shortcut.symlink_to('scribe')
print('Installed: '+str(target))
if backup:print('Previous runtime: '+str(backup))
print('Settings, credentials and data were not modified')
