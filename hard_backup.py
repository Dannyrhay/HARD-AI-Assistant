"""Versioned, credential-free backups; restore only while the desktop service is stopped."""
from contextlib import closing
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile
import uuid
import zipfile
from hard_core import UserError

LIMIT=512*1024*1024
SECRET_FILES={'ai.key','ai.config','ai.connections','gmail.client','gmail.token','outlook.client','outlook.token'}

def valid_member(name):
    return name=='workspace.sqlite3' or bool(re.fullmatch(r'documents/[a-f0-9]{32}\.(?:pdf|docx|txt)',name)) or bool(re.fullmatch(r'[a-f0-9]{32}\.ai\.json',name))

def create_backup(workspace):
    with tempfile.TemporaryDirectory() as temp:
        database=Path(temp)/'workspace.sqlite3'
        with workspace.db() as source,closing(sqlite3.connect(database)) as target:source.backup(target)
        if database.stat().st_size>LIMIT:raise UserError('The workspace database exceeds the in-app backup limit.')
        members={'workspace.sqlite3':database.read_bytes()}
        with closing(sqlite3.connect(database)) as db:
            for doc_id,suffix,sha in db.execute('SELECT id,suffix,hash FROM documents'):
                name='documents/'+doc_id+suffix
                if not valid_member(name):raise UserError('An invalid document record prevented backup.')
                path=workspace.directory/name
                if path.is_symlink():raise UserError('Linked documents cannot be backed up.')
                data=path.read_bytes()
                if hashlib.sha256(data).hexdigest()!=sha:raise UserError('A document changed. Check your workspace before backing up.')
                members[name]=data
                review=workspace.directory/(doc_id+'.ai.json')
                if review.is_file() and not review.is_symlink():members[review.name]=review.read_bytes()
                if sum(map(len,members.values()))>LIMIT:raise UserError('This workspace is too large for in-app backup (512 MB). Close HARD and copy its Data folder instead.')
        manifest={'format':'hard-backup','version':1,'files':{name:hashlib.sha256(data).hexdigest() for name,data in members.items()}}
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('manifest.json',json.dumps(manifest))
            for name,data in members.items():z.writestr(name,data)
        return out.getvalue()

def restore_backup(archive,directory):
    directory=Path(directory).absolute()
    if directory.is_symlink() or any(p.is_symlink() or getattr(p,'is_junction',lambda:False)() for p in [directory,*directory.parents]):raise UserError('Restore requires an ordinary local workspace folder.')
    directory.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='hard-restore-',dir=directory.parent))
    previous=directory.with_name(directory.name+'.previous-'+uuid.uuid4().hex[:8])
    try:
        with zipfile.ZipFile(archive) as z:
            names=z.namelist()
            if len(names)!=len(set(names)) or len(names)>10002 or 'manifest.json' not in names:raise UserError('Invalid backup manifest.')
            if sum(x.file_size for x in z.infolist())>LIMIT or z.getinfo('manifest.json').file_size>2*1024*1024:raise UserError('Backup exceeds the restore size limit.')
            manifest=json.loads(z.read('manifest.json'))
            if manifest.get('format')!='hard-backup' or manifest.get('version')!=1 or set(manifest.get('files',{}))!=set(names)-{'manifest.json'}:raise UserError('Unsupported or incomplete backup.')
            for name,sha in manifest['files'].items():
                if not valid_member(name):raise UserError('Backup contains an unexpected file.')
                data=z.read(name)
                if hashlib.sha256(data).hexdigest()!=sha:raise UserError('Backup integrity check failed.')
                dest=stage/name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(data)
        database=stage/'workspace.sqlite3'
        if not database.is_file():raise UserError('Backup database is missing.')
        with closing(sqlite3.connect(database)) as db:
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise UserError('Backup database is damaged.')
            # Do not allow triggers or views to run during restoration or later application operations.
            if db.execute("SELECT count(*) FROM sqlite_master WHERE type IN ('trigger','view')").fetchone()[0]:raise UserError('Backup contains an unsupported database schema.')
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'documents','settings','drafts','contacts','folders','files','events'}<=tables:raise UserError('Not a HARD workspace backup.')
            for doc_id,suffix,sha in db.execute('SELECT id,suffix,hash FROM documents'):
                name='documents/'+doc_id+suffix
                if not valid_member(name) or not (stage/name).is_file() or hashlib.sha256((stage/name).read_bytes()).hexdigest()!=sha:raise UserError('Backup document verification failed.')
            db.execute("UPDATE drafts SET status='uncertain' WHERE status='sending'")
            if 'chat_turns' in tables:db.execute("UPDATE chat_turns SET status='failed',error='Restored an unfinished request. Review it before retrying.' WHERE status='pending'")
            if 'file_operations' in tables:db.execute("UPDATE file_operations SET status='restored' WHERE status IN ('pending','complete')")
            # Work folder paths need re-selection on this device; never follow restored external paths.
            db.execute('DELETE FROM files');db.execute('DELETE FROM folders');db.commit()
        for name in SECRET_FILES:
            current=directory/name
            if current.is_file() and not current.is_symlink():shutil.copy2(current,stage/name)
        if directory.exists():directory.rename(previous)
        try:stage.rename(directory)
        except Exception:
            if previous.exists():previous.rename(directory)
            raise
        return {'restored':True,'previous':str(previous) if previous.exists() else None}
    finally:
        # stage was created immediately above and is a direct child of the workspace parent.
        if stage.exists() and stage.parent==directory.parent:shutil.rmtree(stage)
