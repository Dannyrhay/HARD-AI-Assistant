"""Explicit OAuth connections and single-attempt email sending. No auto-send."""
import base64
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import secrets
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from hard_core import UserError, digest, text

PROVIDERS={
 'gmail': {'auth':'https://accounts.google.com/o/oauth2/v2/auth','token':'https://oauth2.googleapis.com/token','scope':'https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly','profile':'https://gmail.googleapis.com/gmail/v1/users/me/profile'},
 'outlook': {'auth':'https://login.microsoftonline.com/common/oauth2/v2.0/authorize','token':'https://login.microsoftonline.com/common/oauth2/v2.0/token','scope':'offline_access User.Read Mail.Send Mail.Read','profile':'https://graph.microsoft.com/v1.0/me?$select=mail,userPrincipalName'}
}

class ProviderRejected(UserError):
    pass

def request_json(url,data=None,headers=None,form=False):
    body=None if data is None else (urlencode(data).encode() if form else json.dumps(data).encode())
    request=Request(url,data=body,headers={**({'Content-Type':'application/x-www-form-urlencoded' if form else 'application/json'} if body else {}),**(headers or {})})
    try:
        with urlopen(request,timeout=30) as response:
            raw=response.read(5*1024*1024)
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        if exc.code in {400,401,403,404,413,422,429}:raise ProviderRejected('The email provider rejected the request. Check the account, recipient and attachment before preparing a new draft.') from None
        raise UserError('The email provider did not confirm this request. Check Sent mail before retrying.') from None
    except (URLError,TimeoutError,json.JSONDecodeError) as exc:
        raise UserError('The email provider did not confirm this request. Check the account connection and your internet access.') from exc

def protect(data,decrypt=False):
    if os.name!='nt': raise UserError('Account storage requires the Windows version of HARD.')
    class Blob(ctypes.Structure):
        _fields_=[('cbData',wintypes.DWORD),('pbData',ctypes.POINTER(ctypes.c_char))]
    buffer=ctypes.create_string_buffer(data)
    source=Blob(len(data),ctypes.cast(buffer,ctypes.POINTER(ctypes.c_char)))
    result=Blob()
    api=ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    ok=api(ctypes.byref(source),None,None,None,None,1,ctypes.byref(result))
    if not ok: raise UserError('Windows could not unlock the saved account. Reconnect it from Settings.')
    try: return ctypes.string_at(result.pbData,result.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree.argtypes=[ctypes.c_void_p]
        ctypes.windll.kernel32.LocalFree(ctypes.cast(result.pbData,ctypes.c_void_p))

class Mail:
    def __init__(self,workspace,origin):
        self.workspace=workspace;self.origin=origin;self.pending={};self.approvals={};self.lock=threading.RLock();self.delivery_lock=threading.Lock();self.delivery_cache=None;self.delivery_checked=0
    def config(self,provider):
        if provider not in PROVIDERS: raise UserError('Unknown email provider.')
        prefix='HARD_GOOGLE' if provider=='gmail' else 'HARD_MICROSOFT'
        configured_id=os.environ.get(prefix+'_CLIENT_ID','')
        if configured_id:
            return {'client_id':configured_id,'client_secret':os.environ.get(prefix+'_CLIENT_SECRET','')}
        path=self.workspace.directory/(provider+'.client')
        if not path.exists(): return {'client_id':'','client_secret':''}
        try:
            value=json.loads(protect(path.read_bytes(),True))
            if not isinstance(value,dict) or not isinstance(value.get('client_id'),str): raise ValueError()
            return value
        except (ValueError,OSError) as exc:
            raise UserError('The saved application setup could not be read. Import its credentials again.') from exc
    def configure(self,provider,credentials):
        import re
        if provider not in PROVIDERS: raise UserError('Unknown email provider.')
        if not isinstance(credentials,dict): raise UserError('Choose the application credentials JSON file.')
        if provider=='gmail':
            value=credentials.get('installed')
            if not isinstance(value,dict): raise UserError('Choose Google Desktop app credentials, not Web app or service-account credentials.')
            client_id=text(value.get('client_id'),'Google client ID',300)
            if not re.fullmatch(r'[A-Za-z0-9_-]+\.apps\.googleusercontent\.com',client_id): raise UserError('The Google client ID is not in the expected format.')
            secret=text(value.get('client_secret',''),'client secret',3000,False)
        else:
            client_id=text(credentials.get('client_id'),'Microsoft application ID',100)
            if not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',client_id): raise UserError('Enter the Microsoft Application (client) ID as a UUID.')
            secret=''
        prefix='HARD_GOOGLE' if provider=='gmail' else 'HARD_MICROSOFT'
        if os.environ.get(prefix+'_CLIENT_ID'): raise UserError('This application is configured by an environment variable. Update that configuration and restart HARD.')
        with self.lock:
            if (self.workspace.directory/(provider+'.token')).exists(): raise UserError('Disconnect this account before changing its application setup.')
            path=self.workspace.directory/(provider+'.client');temporary=path.with_suffix('.tmp')
            temporary.write_bytes(protect(json.dumps({'client_id':client_id,'client_secret':secret}).encode()))
            os.replace(temporary,path)
            self.pending={};self.approvals={}
        return {'configured':True,'provider':provider}
    def token_path(self,provider):
        self.config(provider)
        return self.workspace.directory/(provider+'.token')
    def load(self,provider):
        path=self.token_path(provider)
        if not path.exists(): return None
        return json.loads(protect(path.read_bytes(),True))
    def save(self,provider,token):
        path=self.token_path(provider);temporary=path.with_suffix('.tmp')
        temporary.write_bytes(protect(json.dumps(token).encode()));os.replace(temporary,path)
    def status(self):
        statuses={}
        for provider in PROVIDERS:
            try:
                saved=self.load(provider)
                statuses[provider]={'configured':bool(self.config(provider)['client_id']),'connected':bool(saved),'address':saved.get('address') if saved else None}
            except (UserError,ValueError,OSError): statuses[provider]={'configured':False,'connected':False,'address':None,'error':'Check this account’s application setup.'}
        return statuses
    def begin(self,provider):
        config=self.config(provider)
        if not config['client_id']: raise UserError('Account setup is required. Add the application’s OAuth client ID before connecting this account.')
        verifier=secrets.token_urlsafe(48);state=secrets.token_urlsafe(32)
        with self.lock:
            self.pending={k:v for k,v in self.pending.items() if v['expires']>time.time()}
            self.pending[state]={'provider':provider,'verifier':verifier,'expires':time.time()+300}
        params={'client_id':config['client_id'],'redirect_uri':self.origin+'/oauth/callback','response_type':'code','scope':PROVIDERS[provider]['scope'],'state':state,'code_challenge':base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('='),'code_challenge_method':'S256'}
        if provider=='gmail': params.update(access_type='offline',prompt='consent')
        return {'url':PROVIDERS[provider]['auth']+'?'+urlencode(params)}
    def callback(self,state,code):
        with self.lock: pending=self.pending.pop(state,None)
        if not pending or pending['expires']<time.time(): raise UserError('This sign-in request expired. Start again from Settings.')
        provider=pending['provider'];config=self.config(provider)
        params={'client_id':config['client_id'],'code':code,'redirect_uri':self.origin+'/oauth/callback','grant_type':'authorization_code','code_verifier':pending['verifier']}
        if config['client_secret']: params['client_secret']=config['client_secret']
        token=request_json(PROVIDERS[provider]['token'],params,form=True)
        if not token.get('access_token'): raise UserError('The provider did not return an access token.')
        profile=request_json(PROVIDERS[provider]['profile'],headers={'Authorization':'Bearer '+token['access_token']})
        address=profile.get('emailAddress') if provider=='gmail' else profile.get('mail') or profile.get('userPrincipalName')
        if not address: raise UserError('The signed-in email address could not be confirmed.')
        token.update(address=address,expires_at=time.time()+int(token.get('expires_in',3600)))
        self.save(provider,token)
        return provider
    def access(self,provider):
        with self.lock:
            token=self.load(provider)
            if not token: raise UserError('Connect this email account in Settings first.')
            if token.get('expires_at',0)<time.time()+90:
                if not token.get('refresh_token'): raise UserError('Your sign-in expired. Reconnect this account.')
                config=self.config(provider)
                params={'client_id':config['client_id'],'refresh_token':token['refresh_token'],'grant_type':'refresh_token'}
                if config['client_secret']: params['client_secret']=config['client_secret']
                new=request_json(PROVIDERS[provider]['token'],params,form=True)
                if not new.get('access_token'): raise UserError('Reconnect this email account.')
                token.update(new);token['expires_at']=time.time()+int(new.get('expires_in',3600));self.save(provider,token)
            return token
    def disconnect(self,provider):
        with self.lock:
            self.token_path(provider).unlink(missing_ok=True)
            self.approvals={};self.delivery_cache=None
        return {'disconnected':True}
    def approve(self,draft_id,confirmed,expected_sender=None):
        if confirmed is not True: raise UserError('Confirm the sender, recipient, message and PDF before sending.')
        draft=self.workspace.draft(draft_id)
        if draft['status']!='draft': raise UserError('This message is no longer an unsent draft.')
        token=self.access(draft['payload']['provider'])
        if expected_sender != token['address']: raise UserError('The sending account changed. Refresh the draft and review it again.')
        approval=secrets.token_urlsafe(32)
        with self.lock:
            self.approvals={k:v for k,v in self.approvals.items() if v['expires']>time.time()}
            self.approvals[approval]={'draft':draft_id,'expires':time.time()+300,'address':token['address']}
        return {'approval':approval,'sender':token['address']}
    def send(self,draft_id,approval):
        with self.lock: approved=self.approvals.pop(approval,None)
        if not approved or approved['draft']!=draft_id or approved['expires']<time.time(): raise UserError('Review this draft again before sending.')
        draft=self.workspace.draft(draft_id);p=draft['payload'];token=self.access(p['provider'])
        if token['address']!=approved['address']: raise UserError('The sending account changed. Review the draft again.')
        doc=self.workspace.document(p['document_id'])
        if not doc['reviewed']: raise UserError('The attachment review changed. Review the PDF again.')
        data=self.workspace.path(p['document_id']).read_bytes()
        if p['provider']=='outlook' and len(data)>3*1024*1024: raise UserError('Outlook attachments above 3 MB need the large-upload workflow. Download this draft and finish in Outlook.')
        if digest(data)!=p['attachment_hash']: raise UserError('The attachment changed. Prepare a new draft.')
        raw=self.workspace.export_eml(draft_id)
        with self.workspace.db() as db:
            db.execute('BEGIN IMMEDIATE')
            cursor=db.execute("UPDATE drafts SET status='sending' WHERE id=? AND status='draft'",(draft_id,))
            if cursor.rowcount!=1: raise UserError('This message was already submitted. It will not be sent twice.')
        try:
            if p['provider']=='gmail':
                result=request_json('https://gmail.googleapis.com/gmail/v1/users/me/messages/send',{'raw':base64.urlsafe_b64encode(raw).decode()},headers={'Authorization':'Bearer '+token['access_token']})
                if not result.get('id'): raise UserError('Gmail did not return a message receipt.')
                receipt=result['id'];status='sent'
            else:
                request_json('https://graph.microsoft.com/v1.0/me/sendMail',{'message':{'subject':p['subject'],'body':{'contentType':'Text','content':p['body']},'toRecipients':[{'emailAddress':{'address':p['contact']['email']}}],'attachments':[{'@odata.type':'#microsoft.graph.fileAttachment','name':p['attachment_name'],'contentType':'application/pdf','contentBytes':base64.b64encode(data).decode()}]},'saveToSentItems':True},headers={'Authorization':'Bearer '+token['access_token']})
                receipt=None;status='accepted'
        except ProviderRejected:
            with self.workspace.db() as db:db.execute("UPDATE drafts SET status='failed' WHERE id=?",(draft_id,))
            self.workspace.event('email','Provider rejected '+p['subject']+'. Review the account and recipient before preparing a new draft.')
            raise UserError('Email was not accepted by the provider. Check your account, recipient and attachment, then prepare a new draft.') from None
        except Exception as exc:
            with self.workspace.db() as db: db.execute("UPDATE drafts SET status='uncertain' WHERE id=?",(draft_id,))
            raise UserError('The sending result is uncertain. Check Sent mail before taking any further action. HARD will not retry automatically.') from exc
        with self.workspace.db() as db: db.execute('UPDATE drafts SET status=?,provider_id=? WHERE id=?',(status,receipt,draft_id))
        self.workspace.event('email','Provider accepted '+p['subject']+' for '+p['contact']['email']+'. Delivery not confirmed.')
        return self.workspace.draft(draft_id)
    def delivery_status(self,force=False):
        if not self.delivery_lock.acquire(blocking=False):return self.delivery_view(self.delivery_cache) if self.delivery_cache else {'checking':True,'messages':[],'errors':[]}
        try:
            if not force and self.delivery_cache is not None and time.time()-self.delivery_checked<300:return self.delivery_view(self.delivery_cache)
            messages=[];errors=[];checked_accounts=[]
            for provider,account in self.status().items():
                if not account['connected']:continue
                try:
                    result=self.failures(provider)
                    checked_accounts.append(provider)
                    messages.extend({**m,'provider':provider} for m in result['messages'])
                except UserError:errors.append(provider)
            self.delivery_checked=time.time()
            self.delivery_cache={'messages':messages,'errors':errors,'checked_at':self.delivery_checked,'checked_accounts':checked_accounts}
            return self.delivery_view(self.delivery_cache)
        finally:self.delivery_lock.release()

    def failures(self,provider):
        token=self.access(provider);headers={'Authorization':'Bearer '+token['access_token']}
        if provider=='gmail':
            query=urlencode({'q':'newer_than:30d {from:mailer-daemon from:postmaster subject:"delivery status notification"}','maxResults':30})
            found=request_json('https://gmail.googleapis.com/gmail/v1/users/me/messages?'+query,headers=headers)
            messages=[]
            for record in found.get('messages',[]):
                item=request_json('https://gmail.googleapis.com/gmail/v1/users/me/messages/'+record['id']+'?format=metadata&metadataHeaders=Subject&metadataHeaders=Date',headers=headers)
                fields={h['name'].lower():h['value'] for h in item.get('payload',{}).get('headers',[])}
                messages.append({'id':record['id'],'subject':fields.get('subject','Delivery notice'),'date':fields.get('date','')})
        else:
            found=request_json('https://graph.microsoft.com/v1.0/me/messages?'+urlencode({'$top':30,'$search':'"from:postmaster OR subject:undeliverable"','$select':'id,subject,receivedDateTime'}),headers=headers)
            messages=[{'id':m['id'],'subject':m['subject'],'date':m.get('receivedDateTime','')} for m in found.get('value',[])]
        return {'messages':messages,'note':'Possible delivery notices. This search is not exhaustive, and no matching notice does not prove delivery. Open your inbox to inspect them.'}

    def notice_details(self,provider,message_id):
        import re
        from email import policy
        from email.parser import BytesParser
        if provider!='gmail':raise UserError('Open your Outlook inbox to inspect this notice.')
        if not isinstance(message_id,str) or not re.fullmatch(r'[a-fA-F0-9]{1,64}',message_id):raise UserError('Choose a valid delivery notice.')
        token=self.access(provider)
        result=request_json('https://gmail.googleapis.com/gmail/v1/users/me/messages/'+message_id+'?format=raw',headers={'Authorization':'Bearer '+token['access_token']})
        raw=result.get('raw','')
        try:message=BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(raw+'='*(-len(raw)%4)))
        except Exception:raise UserError('This notice could not be read. Open it in Gmail.') from None
        diagnostics=[]
        for part in message.walk():
            if part.get_content_type()!='message/delivery-status':continue
            for block in part.get_payload():
                if block.get('Action') or block.get('Status'):
                    diagnostics.append({k:str(block.get(header,''))[:1500] for k,header in [('action','Action'),('status','Status'),('reason','Diagnostic-Code'),('recipient','Final-Recipient')]})
        return {'diagnostics':diagnostics,'note':'This describes a delivery result, not whether HARD is connected. Check the recipient against the original contact before sending again.'}

    def delivery_view(self,cached):
        import hashlib
        accounts=self.status()
        scope={p:hashlib.sha256((p+':'+str(a.get('address') or '')).lower().encode()).hexdigest() for p,a in accounts.items() if a.get('connected')}
        messages=[]
        with self.workspace.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS delivery_notices(key TEXT PRIMARY KEY,account TEXT NOT NULL,notice TEXT NOT NULL,handled REAL)')
            for m in cached.get('messages',[]):
                account=scope.get(m['provider'])
                if not account:continue
                identity=m.get('id') or (m.get('date','')+':'+m.get('subject',''))
                key=hashlib.sha256((account+':'+identity).encode()).hexdigest()
                notice={**m,'key':key}
                db.execute('INSERT INTO delivery_notices(key,account,notice) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET notice=excluded.notice',(key,account,json.dumps(notice)))
                if db.execute('SELECT handled FROM delivery_notices WHERE key=?',(key,)).fetchone()['handled'] is None:messages.append(notice)
            handled=[];messages=[]
            for row in db.execute('SELECT account,notice,handled FROM delivery_notices ORDER BY handled DESC,rowid DESC'):
                if row['account'] not in scope.values():continue
                notice=json.loads(row['notice'])
                if row['handled'] is None:messages.append(notice)
                else:handled.append({**notice,'handled_at':row['handled']})
        return {**cached,'messages':messages,'handled':handled}

    def handle_notice(self,key,handled):
        if not isinstance(key,str) or len(key)!=64 or not isinstance(handled,bool):raise UserError('Choose a delivery notice.')
        current=self.delivery_status()
        if key not in {n['key'] for n in current.get('messages',[])+current.get('handled',[])}:raise UserError('This notice is no longer available for the connected account.')
        with self.workspace.db() as db:db.execute('UPDATE delivery_notices SET handled=? WHERE key=?',(time.time() if handled else None,key))
        return self.delivery_status()
