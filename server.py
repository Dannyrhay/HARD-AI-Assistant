"""Loopback-only personal assistant service. Never expose this port to a network."""
import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import secrets
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,parse_qs
from hard_core import Workspace,UserError,MAX_FILE,text
from hard_mail import Mail
from hard_ai import AIReview
from hard_chat import Chat
from hard_conversations import Conversations
from hard_models import ModelCatalog
from hard_backup import create_backup
from hard_preview import preview
from hard_workflows import FileJournal, DraftRecovery, email_preflight, VERSION

BASE=Path(__file__).parent.resolve()

def handler_factory(workspace,mail,origin,desktop=False):
    ai=AIReview(workspace);chat=Chat(ai);conversations=Conversations(workspace,chat);catalog=ModelCatalog();journal=FileJournal(workspace);recovery=DraftRecovery(workspace,conversations)
    csrf=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        server_version='HARD'
        def log_message(self,*args): pass  # Never log filenames, OAuth codes or request bodies.
        def headers_ok(self):
            if self.headers.get('Host')!=urlparse(origin).netloc: raise UserError('This address is not allowed.')
            if self.command=='POST':
                if self.headers.get('Origin')!=origin or not secrets.compare_digest(self.headers.get('X-HARD-CSRF',''),csrf): raise UserError('Reload HARD before continuing.')
                if self.headers.get('Content-Type','').split(';')[0]!='application/json': raise UserError('Expected a JSON request.')
        def respond(self,value,status=200,content_type='application/json',filename=None):
            raw=json.dumps(value).encode() if content_type=='application/json' else value
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
            if filename:
                from urllib.parse import quote
                self.send_header('Content-Disposition',"attachment; filename*=UTF-8''"+quote(filename))
            self.end_headers();self.wfile.write(raw)
        def do_GET(self):
            try:
                self.headers_ok();parsed=urlparse(self.path);path=parsed.path;query=parse_qs(parsed.query)
                if path=='/api/state': return self.respond({**workspace.snapshot(),'accounts':mail.status(),'ai':ai.status(),'csrf':csrf,'profile':workspace.profile(),'desktop':desktop,'version':VERSION})
                if path.startswith('/api/chat-attachments/'): return self.respond(conversations.files(path.rsplit('/',1)[1]))
                if path=='/api/openrouter-models': return self.respond(catalog.list(query.get('refresh',['0'])[0]=='1'))
                if path=='/api/recovery': return self.respond(recovery.load())
                if path=='/api/file-operations': return self.respond(journal.listing())
                if path=='/api/conversations': return self.respond(conversations.listing())
                if path.startswith('/api/conversation/'): return self.respond(conversations.get(path.rsplit('/',1)[1]))
                if path=='/api/ai-review': return self.respond(ai.saved(query.get('id',[''])[0]))
                if path=='/api/delivery-status': return self.respond(mail.delivery_status())
                if path=='/api/search': return self.respond(workspace.search(query.get('q',[''])[0]))
                if path.startswith('/api/document/'):
                    doc_id=path.rsplit('/',1)[1];return self.respond(workspace.document(doc_id))
                if path.startswith('/api/draft/'):
                    return self.respond(workspace.draft(path.rsplit('/',1)[1]))
                if path.startswith('/document/'):
                    doc=workspace.document(path.rsplit('/',1)[1]);data=workspace.path(doc['id']).read_bytes()
                    mime={'.pdf':'application/pdf','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','.txt':'text/plain; charset=utf-8'}[doc['suffix']]
                    return self.respond(data,content_type=mime,filename=None if doc['suffix']=='.pdf' and query.get('inline') else doc['name'])
                if path.startswith('/draft/'):
                    return self.respond(workspace.export_eml(path.rsplit('/',1)[1]),content_type='message/rfc822',filename='HARD email draft.eml')
                if path=='/oauth/callback':
                    mail.callback(query.get('state',[''])[0],query.get('code',[''])[0]);return self.respond(b'<!doctype html><html lang="en"><meta charset="utf-8"><title>HARD account connected</title><link rel="stylesheet" href="/style.css"><main><h1>Account connected.</h1><p>You can now return to your workspace.</p><a class="button" href="/">Return to HARD</a></main></html>',content_type='text/html; charset=utf-8')
                allowed={'/':'index.html','/index.html':'index.html','/style.css':'style.css','/app.js':'app.js','/hard-icon.svg':'hard-icon.svg','/markdown-it.min.js':'markdown-it.min.js','/purify.min.js':'purify.min.js','/format.js':'format.js'}
                if path not in allowed: return self.respond({'error':'Not found'},404)
                asset=BASE/'dist'/allowed[path]
                return self.respond(asset.read_bytes(),content_type=mimetypes.guess_type(asset)[0] or 'application/octet-stream')
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError): pass
            except UserError as exc: self.respond({'error':str(exc)},400)
            except (OSError,ValueError): self.respond({'error':'This file or request is unavailable.'},400)
            except Exception: self.respond({'error':'HARD could not complete this request. Please try again.'},500)
        def do_POST(self):
            try:
                self.headers_ok()
                size=int(self.headers.get('Content-Length','0'))
                if size<=0 or size>MAX_FILE*1.4: raise UserError('Choose a file smaller than 20 MB.')
                self.connection.settimeout(30)
                body=json.loads(self.rfile.read(size))
                if not isinstance(body,dict): raise UserError('Invalid request.')
                path=urlparse(self.path).path
                if path=='/api/profile': result=workspace.save_profile(body.get('name'),body.get('role',''),body.get('preferences',''))
                elif path=='/api/ai-configure': result=ai.configure(body.get('key'),body.get('provider','openai'),body.get('model',''),body.get('endpoint',''),body.get('name',''))
                elif path=='/api/ai-model': result=ai.select_model(body.get('id'),body.get('model'))
                elif path=='/api/ai-select': result=ai.select(body.get('id'))
                elif path=='/api/voice-typing':
                    if not desktop: raise UserError('Open the HARD desktop app to use Windows voice typing.')
                    from hard_voice import start_voice_typing
                    result=start_voice_typing()
                elif path=='/api/backup': return self.respond(create_backup(workspace),content_type='application/zip',filename='HARD-backup.zip')
                elif path=='/api/recovery': result=recovery.save(body)
                elif path=='/api/undo-file': result=journal.undo(body.get('id'),body.get('confirmed'))
                elif path=='/api/email-preflight': result=email_preflight(workspace,body)
                elif path=='/api/chat': result=conversations.send(body)
                elif path=='/api/chat-retry': result=conversations.retry(body)
                elif path=='/api/delivery-notice': result=mail.notice_details(body.get('provider'),body.get('id'))
                elif path=='/api/delivery-handled': result=mail.handle_notice(body.get('key'),body.get('handled'))
                elif path=='/api/delivery-refresh': result=mail.delivery_status(force=True)
                elif path=='/api/conversation-rename': result=conversations.rename(body.get('id'),body.get('title'))
                elif path=='/api/conversation-delete': result=conversations.delete(body.get('id'),body.get('confirmed'))
                elif path=='/api/ai-review': result=ai.review(body.get('id'),body.get('confirmed'))
                elif path=='/api/import':
                    try: data=base64.b64decode(body.get('data',''),validate=True)
                    except Exception as exc: raise UserError('The file upload was incomplete.') from exc
                    result=workspace.import_document(body.get('name'),data)
                elif path=='/api/rename-file': result=journal.perform('rename',body)
                elif path=='/api/duplicates': result=workspace.duplicates()
                elif path=='/api/reveal-file':
                    if not desktop: raise UserError('Open in folder is available in the desktop app.')
                    import subprocess
                    file=workspace.indexed_path(body.get('id'))
                    subprocess.Popen(['explorer.exe','/select,',str(file)],shell=False)
                    result={'opened':True}
                elif path=='/api/organise-file': result=journal.perform('move' if body.get('mode')=='move' else 'copy',body)
                elif path=='/api/import-indexed': result=workspace.import_indexed(body.get('id'))
                elif path=='/api/decide': result=workspace.decide(body.get('id'),body.get('issue_id'),body.get('note'))
                elif path=='/api/approve-document': result=workspace.approve(body.get('id'))
                elif path=='/api/replace': result=workspace.replace(body.get('id'),body.get('old'),body.get('new'))
                elif path=='/api/attachment-preview': result=preview(workspace,body)
                elif path=='/api/convert': result=workspace.convert_to(body.get('id'),body.get('target'))
                elif path=='/api/pdf': result=workspace.convert(body.get('id'))
                elif path=='/api/folders': result=workspace.add_folder(body.get('path'),body.get('label'))
                elif path=='/api/scan': result=workspace.scan()
                elif path=='/api/remove-folder':
                    with workspace.db() as db:
                        db.execute('DELETE FROM files WHERE folder_id=?',(body.get('id'),));db.execute('DELETE FROM folders WHERE id=?',(body.get('id'),))
                    result={'removed':True}
                elif path=='/api/contacts': result=workspace.add_contact(body.get('name'),body.get('email'),body.get('organization'),body.get('source'),body.get('confirm'))
                elif path=='/api/check-recipient': result=workspace.check_recipient(body.get('email'))
                elif path=='/api/stage-email':
                    preflight=email_preflight(workspace,body)
                    if preflight['warnings'] and body.get('preflight_token')!=preflight['token']:raise UserError('Run the email checks and review the warnings before saving this draft.')
                    result=workspace.stage_email(body.get('contact_id'),body.get('document_id'),body.get('subject'),body.get('body'),body.get('provider'),body.get('visual_confirmed'),body.get('recipient'))
                elif path=='/api/approve-email': result=mail.approve(body.get('id'),body.get('confirmed'),body.get('expected_sender'))
                elif path=='/api/send': result=mail.send(body.get('id'),body.get('approval'))
                elif path=='/api/configure-account': result=mail.configure(body.get('provider'),body.get('credentials'))
                elif path=='/api/connect':
                    result=mail.begin(body.get('provider'))
                    if desktop:
                        import webbrowser
                        if not webbrowser.open(result['url']): raise UserError('Your browser could not open. Check the default browser in Windows Settings.')
                        result={'external':True}
                elif path=='/api/disconnect': result=mail.disconnect(body.get('provider'))
                elif path=='/api/failures': result=mail.failures(body.get('provider'))
                else: return self.respond({'error':'Not found'},404)
                self.respond(result)
            except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError): pass
            except UserError as exc: self.respond({'error':str(exc)},400)
            except (ValueError,TypeError,KeyError): self.respond({'error':'The request was incomplete. Please check the fields and try again.'},400)
            except Exception: self.respond({'error':'HARD could not complete this request. Check the current status before repeating a file change or email send.'},500)
    return Handler

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=5188);parser.add_argument('--data',default=str(BASE/'.data'));args=parser.parse_args()
    workspace=Workspace(args.data);origin=f'http://127.0.0.1:{args.port}';mail=Mail(workspace,origin)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),handler_factory(workspace,mail,origin))
    print('HARD Assistant: '+origin,flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__=='__main__': main()
