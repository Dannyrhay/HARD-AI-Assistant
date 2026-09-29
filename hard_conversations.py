"""Local durable conversations. Provider context is loaded from trusted local history."""
import base64
import json
import threading
import time
from hard_core import UserError, identifier, text, safe_name
from hard_chat import MAX_BYTES
from hard_workflows import route_request

class Conversations:
    def __init__(self, workspace, chat):
        self.workspace=workspace; self.chat=chat; self.lock=threading.Lock()
        with workspace.db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY,title TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL,attachments TEXT NOT NULL DEFAULT '[]');
            CREATE TABLE IF NOT EXISTS chat_turns(id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL,question TEXT NOT NULL,answer TEXT,error TEXT,status TEXT NOT NULL,sources TEXT NOT NULL DEFAULT '[]',files TEXT NOT NULL DEFAULT '[]',created REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS chat_turn_order ON chat_turns(conversation_id,created);
            """)
            if 'web' not in {r[1] for r in db.execute('PRAGMA table_info(chat_turns)')}:
                db.execute("ALTER TABLE chat_turns ADD COLUMN web TEXT NOT NULL DEFAULT '{}'")
            if 'actions' not in {r[1] for r in db.execute('PRAGMA table_info(chat_turns)')}:
                db.execute("ALTER TABLE chat_turns ADD COLUMN actions TEXT NOT NULL DEFAULT '[]'")
            db.execute("UPDATE chat_turns SET status='failed',error='HARD closed before this answer finished. Your question was saved; send it again if needed.' WHERE status='pending'")
    def listing(self):
        with self.workspace.db() as db:
            return [dict(r) for r in db.execute('SELECT id,title,created,updated FROM conversations ORDER BY updated DESC,id DESC')]
    def get(self, cid):
        with self.workspace.db() as db:
            row=db.execute('SELECT * FROM conversations WHERE id=?',(cid,)).fetchone()
            if not row:raise UserError('This conversation was not found.')
            result=dict(row);result['attachments']=json.loads(result['attachments']);result['messages']=[]
            for turn in db.execute('SELECT id,question,answer,error,status,sources,web,actions,length(files)>2 AS has_files FROM chat_turns WHERE conversation_id=? ORDER BY created,id',(cid,)):
                result['messages'].append({'role':'user','content':turn['question'],'web':json.loads(turn['web']),'sources':json.loads(turn['sources']),'attachment_turn':turn['id'] if turn['has_files'] else None})
                if turn['answer']:result['messages'].append({'role':'assistant','content':turn['answer'],'actions':json.loads(turn['actions']),'turn_id':turn['id'],'web':json.loads(turn['web'])})
                elif turn['error']:result['messages'].append({'role':'error','content':turn['error'],'web':json.loads(turn['web']),'retry_turn':turn['id'] if turn['status']=='failed' else None})
            return result
    def files(self,turn_id):
        with self.workspace.db() as db:row=db.execute('SELECT files FROM chat_turns WHERE id=?',(turn_id,)).fetchone()
        if not row:raise UserError('These attachments were not found.')
        return json.loads(row['files'])
    def rename(self,cid,title):
        title=text(title,'conversation title',100)
        with self.workspace.db() as db:
            if db.execute('UPDATE conversations SET title=? WHERE id=?',(title,cid)).rowcount!=1:raise UserError('This conversation was not found.')
        return {'renamed':True}
    def delete(self,cid,confirmed):
        if confirmed is not True:raise UserError('Confirm deleting this conversation.')
        if not self.lock.acquire(blocking=False):raise UserError('Wait for the current answer before deleting a chat.')
        try:
            with self.workspace.db() as db:
                db.execute('DELETE FROM chat_turns WHERE conversation_id=?',(cid,));db.execute('DELETE FROM conversations WHERE id=?',(cid,))
            return {'deleted':True}
        finally:self.lock.release()
    def snapshot_files(self,items):
        if not isinstance(items,list) or len(items)>3:raise UserError('Attach up to three files.')
        files=[];total=0
        for item in items:
            if not isinstance(item,dict):raise UserError('Invalid attachment.')
            if item.get('document_id'):
                doc=self.workspace.document(item['document_id']);name=doc['name'];raw=self.workspace.path(doc['id']).read_bytes()
            else:
                name=safe_name(item.get('name'))
                try:raw=base64.b64decode(item.get('data',''),validate=True)
                except (ValueError,TypeError):raise UserError('The attachment upload was incomplete.') from None
            total+=len(raw)
            if total>MAX_BYTES:raise UserError('Attachments must total 12 MB or less.')
            files.append({'name':name,'data':base64.b64encode(raw).decode(),'size':len(raw)})
        return files
    def send(self,body):
        if body.get('confirmed') is not True:raise UserError('Confirm sharing with your AI provider.')
        question=text(body.get('message'),'question',8000)
        rid=text(body.get('request_id'),'request ID',100)
        if not self.lock.acquire(blocking=False):raise UserError('An answer is still being prepared. Please wait.')
        try:
            with self.workspace.db() as db:old=db.execute('SELECT conversation_id FROM chat_turns WHERE id=?',(rid,)).fetchone()
            if old:return {'conversation':self.get(old['conversation_id'])}
            cid=body.get('conversation_id')
            if cid:self.get(cid)
            files=self.snapshot_files(body.get('attachments',[]));now=time.time()
            if not cid:cid=identifier()
            with self.workspace.db() as db:
                db.execute('INSERT OR IGNORE INTO conversations(id,title,created,updated) VALUES(?,?,?,?)',(cid,question[:80],now,now))
                db.execute('UPDATE conversations SET attachments=?,updated=? WHERE id=?',(json.dumps(files),now,cid))
                history=[]
                for t in reversed(list(db.execute("SELECT question,answer FROM chat_turns WHERE conversation_id=? AND status='complete' ORDER BY created DESC,id DESC LIMIT 6",(cid,)))):
                    history.extend([{'role':'user','content':t['question']},{'role':'assistant','content':t['answer']}])
                while sum(len(m['content']) for m in history)>60000:history=history[2:]
                db.execute('INSERT INTO chat_turns(id,conversation_id,question,status,sources,files,created) VALUES(?,?,?,?,?,?,?)',(rid,cid,question,'pending',json.dumps([{'name':f['name'],'mode':'attached file'} for f in files]),json.dumps(files),now))
            with self.workspace.db() as db:db.execute('UPDATE chat_turns SET web=? WHERE id=?',(json.dumps({'enabled':body.get('web_search',False)}),rid))
            try:
                result=route_request(self.workspace,question,files) or self.chat.answer({**body,'history':history,'attachments':files})
            except Exception as exc:
                error=str(exc) if isinstance(exc,UserError) else 'HARD could not finish this answer. Your question is saved. Try again when ready.'
                with self.workspace.db() as db:db.execute("UPDATE chat_turns SET status='failed',error=? WHERE id=?",(error,rid))
                return {'conversation':self.get(cid),'error':error}
            with self.workspace.db() as db:
                db.execute("UPDATE chat_turns SET status='complete',answer=?,sources=?,web=?,actions=? WHERE id=?",(result['answer'],json.dumps(result['attachments']),json.dumps(result.get('web',{})),json.dumps(result.get('actions',[])),rid))
                db.execute('UPDATE conversations SET updated=? WHERE id=?',(time.time(),cid))
            return {'conversation':self.get(cid)}
        finally:self.lock.release()

    def retry(self,body):
        if body.get('confirmed') is not True:raise UserError('Confirm sharing with your AI provider.')
        rid=text(body.get('turn_id'),'message ID',100)
        if not self.lock.acquire(blocking=False):raise UserError('An answer is still being prepared. Please wait.')
        try:
            with self.workspace.db() as db:
                row=db.execute('SELECT * FROM chat_turns WHERE id=? AND conversation_id=?',(rid,body.get('conversation_id'))).fetchone()
                if not row:raise UserError('This saved message was not found.')
                turn=dict(row);cid=turn['conversation_id']
                if turn['status']!='failed':raise UserError('This message no longer needs a retry. Reopen the chat to see its answer.')
                history=[]
                rows=db.execute("SELECT question,answer FROM chat_turns WHERE conversation_id=? AND status='complete' AND (created<? OR (created=? AND id<?)) ORDER BY created DESC,id DESC LIMIT 6",(cid,turn['created'],turn['created'],rid))
                for t in reversed(list(rows)):history.extend([{'role':'user','content':t['question']},{'role':'assistant','content':t['answer']}])
                while sum(len(m['content']) for m in history)>60000:history=history[2:]
                db.execute("UPDATE chat_turns SET status='pending',error=NULL WHERE id=?",(rid,))
            try:
                result=self.chat.answer({**body,'message':turn['question'],'web_search':json.loads(turn['web']).get('enabled',False),'history':history,'attachments':json.loads(turn['files'])})
            except Exception as exc:
                error=str(exc) if isinstance(exc,UserError) else 'HARD could not finish this answer. Your message and attachments are saved. Try again when ready.'
                with self.workspace.db() as db:db.execute("UPDATE chat_turns SET status='failed',error=? WHERE id=?",(error,rid))
                return {'conversation':self.get(cid),'error':error}
            with self.workspace.db() as db:
                db.execute("UPDATE chat_turns SET status='complete',answer=?,error=NULL,sources=?,web=?,actions=? WHERE id=?",(result['answer'],json.dumps(result['attachments']),json.dumps(result.get('web',{})),json.dumps(result.get('actions',[])),rid))
                db.execute('UPDATE conversations SET updated=? WHERE id=?',(time.time(),cid))
            return {'conversation':self.get(cid)}
        finally:self.lock.release()
