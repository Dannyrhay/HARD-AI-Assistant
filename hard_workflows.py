"""Local workflow suggestions, draft recovery, email checks and reversible file actions."""
import hashlib
import json
import re
import threading
import time
from pathlib import Path
from hard_core import UserError, text, identifier, digest, MAX_FILE

VERSION = '0.2.0'

def route_request(workspace, question, attachments):
    """Only user-written, anchored requests can suggest local actions. No LLM output is executed."""
    q=re.sub(r'^(?:can|could|would) you\s+','',question.strip(),flags=re.I)
    action=None
    match=re.fullmatch(r'(?:please )?(?:find|search(?: for)?|look for) (?:my |the )?(?:latest |newest )?(.*)',q,re.I)
    if match:
        query=re.sub(r'^(?:files?|documents?)(?: named| called| about| for)?\s*','',match[1],flags=re.I).strip(' .?')
        if len(query)>200:return None
        action={'kind':'files','query':query,'label':'Find files'}
    elif re.match(r'^(?:please )?(?:find|show|check)(?: me)? (?:my |the )?duplicates?\b',q,re.I):
        action={'kind':'duplicates','label':'Review duplicate files'}
    elif re.match(r'^(?:please )?(?:convert|turn|change)\b.*\b(?:pdf|word|docx)\b',q,re.I):
        action={'kind':'conversion','label':'Choose document to convert'}
        if attachments:action={'kind':'attachment','index':0,'label':'Open attached document for conversion'}
    elif re.match(r'^(?:please )?(?:prepare|draft|write|send)(?: me)? (?:an? |the )?email\b',q,re.I):
        addresses=re.findall(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",q)
        action={'kind':'email','label':'Prepare email','recipient':addresses[0] if len(addresses)==1 else ''}
    elif re.match(r'^(?:please )?(?:review|check) (?:this |my |the |a )?document\b',q,re.I):
        action={'kind':'documents','label':'Choose document to review'}
        if attachments:action={'kind':'attachment','index':0,'label':'Open attached document for review'}
    elif re.match(r'^(?:please )?(?:organise|organize|rename) (?:my |the |these |a )?files?\b',q,re.I):
        action={'kind':'files','query':'','label':'Choose files to organise'}
    if not action:return None
    if action['kind']=='files' and 'duplicate' in q.lower():action={'kind':'duplicates','label':'Review duplicate files'}
    return {'answer':'I can help with that using HARD’s local tools. Choose the action below to review the details. Nothing has been sent or changed.','attachments':[{'name':f['name'],'mode':'attached file'} for f in attachments],'actions':[action]}

class DraftRecovery:
    def __init__(self,workspace,conversations):self.w=workspace;self.conversations=conversations
    def load(self):
        with self.w.db() as db:row=db.execute("SELECT value FROM settings WHERE key='unsent-work'").fetchone()
        return json.loads(row[0]) if row else {}
    def save(self,body):
        value={}
        if body.get('chat') is not None:
            c=body['chat'];cid=c.get('id')
            if cid:self.conversations.get(cid)
            value['chat']={'id':cid,'message':text(c.get('message',''),'message',8000,False),'files':self.conversations.snapshot_files(c.get('files',[])),'web_search':c.get('web_search') is True}
        if body.get('email') is not None:
            email=body['email']
            keys={'provider':20,'contact':100,'recipient-name':100,'recipient-email':254,'subject':200,'body':20000,'attachment':100,'mode':10}
            value['email']={k:text(email.get(k,''),k,n,False) for k,n in keys.items()}
        with self.w.db() as db:db.execute("INSERT OR REPLACE INTO settings VALUES('unsent-work',?)",(json.dumps(value),))
        return {'saved':True}

def email_preflight(w,body):
    warnings=[]
    recipient=body.get('recipient') or {}
    address=recipient.get('email','')
    if body.get('contact_id'):
        contact=next((c for c in w.contacts() if c['id']==body['contact_id']),None)
        if contact:address=contact['email']
    if address:
        checked=w.check_recipient(address)
        if not checked['verified']:warnings.append('This recipient is not a verified saved contact. Compare it with the original request.')
        if checked['suggestions']:warnings.append('Similar saved address: '+', '.join(c['email'] for c in checked['suggestions'])+'. HARD will not replace your address.')
        domain=address.rsplit('@',1)[-1].lower()
        typos={'gmial.com':'gmail.com','gamil.com':'gmail.com','gmail.con':'gmail.com','outlok.com':'outlook.com','hotmial.com':'hotmail.com'}
        if domain in typos:warnings.append('Possible domain typo: '+domain+'. Did you intend '+typos[domain]+'?')
    content=str(body.get('subject',''))+' '+str(body.get('body',''))
    if re.search(r'\b(?:TODO|TBD|PLACEHOLDER)\b|\[(?:name|client|date|amount|insert)[^]]*\]',content,re.I):warnings.append('The message appears to contain an unfinished placeholder.')
    attachment=body.get('document_id')
    if attachment:
        doc=w.document(attachment)
        names=re.findall(r'[\w.-]+\.(?:pdf|docx|xlsx|pptx)',content,re.I)
        missing=[n for n in names if n.casefold()!=doc['name'].casefold()]
        if missing:warnings.append('The message names other files that are not attached: '+', '.join(missing)+'. HARD attaches one reviewed PDF.')
        if re.search(r'\b(?:both|two|three|multiple) attachments?\b',content,re.I):warnings.append('The message mentions multiple attachments, but this draft has one PDF.')
    else:warnings.append('Choose and review a PDF attachment before sending.')
    fingerprint=digest(json.dumps({k:v for k,v in body.items() if k!='preflight_token'},sort_keys=True).encode())
    return {'warnings':warnings,'token':fingerprint}

class FileJournal:
    def __init__(self,w):
        self.w=w;self.lock=threading.Lock()
        with w.db() as db:db.execute("CREATE TABLE IF NOT EXISTS file_operations(id TEXT PRIMARY KEY,kind TEXT,source TEXT,target TEXT,hash TEXT,status TEXT,created REAL)")
    def listing(self):
        with self.w.db() as db:return [dict(x) for x in db.execute("SELECT * FROM file_operations WHERE status IN ('complete','pending') ORDER BY created DESC LIMIT 50")]
    def checked_path(self,value):
        p=Path(value)
        with self.w.db() as db:roots=[Path(r[0]).resolve() for r in db.execute('SELECT path FROM folders')]
        if not any(p.resolve().is_relative_to(root) for root in roots):raise UserError('The work folder is no longer included. Add it again before undoing.')
        for parent in [p,*p.parents]:
            if parent.is_symlink() or getattr(parent,'is_junction',lambda:False)():raise UserError('Linked folders cannot be used for undo.')
        return p
    def perform(self,kind,body):
        if body.get('confirmed') is not True:raise UserError('Review the file change before confirming.')
        with self.lock:
            source=self.checked_path(str(self.w.indexed_path(body.get('id'))))
            if kind=='rename':target=source.with_name(text(body.get('name'),'file name',200))
            else:
                with self.w.db() as db:row=db.execute('SELECT path FROM folders WHERE id=?',(body.get('folder_id'),)).fetchone()
                if not row:raise UserError('Choose a work folder.')
                target=Path(row[0])/text(body.get('project'),'project name',100)/source.name
            target=self.checked_path(str(target))
            if kind=='move' and source.drive.casefold()!=target.drive.casefold():raise UserError('Move within the same drive, or use Copy to project to preserve the original.')
            raw=source.read_bytes()
            if len(raw)>MAX_FILE:raise UserError('Choose a file smaller than 20 MB.')
            op=identifier()
            with self.w.db() as db:db.execute('INSERT INTO file_operations VALUES(?,?,?,?,?,?,?)',(op,kind,str(source),str(target),digest(raw),'pending',time.time()))
            try:
                result=self.w.rename_file(body['id'],body['name'],True) if kind=='rename' else self.w.organise_file(body['id'],body['folder_id'],body['project'])
                if kind=='move':
                    if digest(source.read_bytes())!=digest(raw) or digest(target.read_bytes())!=digest(raw):raise UserError('The file changed during the move. Both copies were kept; review them manually.')
                    source.unlink();self.w.scan();result['original_kept']=False
            except Exception:
                with self.w.db() as db:db.execute("UPDATE file_operations SET status='failed' WHERE id=?",(op,))
                raise
            with self.w.db() as db:db.execute("UPDATE file_operations SET status='complete' WHERE id=?",(op,))
            return {**result,'operation_id':op}
    def undo(self,op,confirmed):
        if confirmed is not True:raise UserError('Confirm undoing this file change.')
        with self.lock:
            with self.w.db() as db:row=db.execute('SELECT * FROM file_operations WHERE id=?',(op,)).fetchone()
            if not row or row['status']!='complete':raise UserError('This operation cannot be undone automatically.')
            source=self.checked_path(row['source']);target=self.checked_path(row['target'])
            if not target.is_file() or target.stat().st_size>MAX_FILE or digest(target.read_bytes())!=row['hash']:raise UserError('The changed file was edited, moved or removed. Undo stopped to protect your work.')
            if row['kind'] in ('rename','move'):
                if source.exists():raise UserError('The original name is now occupied. Nothing was overwritten.')
                target.rename(source)
            else:
                if not source.is_file() or source.stat().st_size>MAX_FILE or digest(source.read_bytes())!=row['hash']:raise UserError('The original has changed or is missing. The project copy was kept.')
                target.unlink()
            with self.w.db() as db:db.execute("UPDATE file_operations SET status='undone' WHERE id=?",(op,))
            self.w.scan();self.w.event('undo','Undid '+row['kind']+' of '+source.name)
            return {'undone':True}
