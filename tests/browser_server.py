"""Isolated browser fixture: no personal workspace or provider requests."""
import sys,tempfile,io,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hard_core import Workspace,UserError
from pypdf import PdfWriter
from hard_ai import AIReview
import hard_chat
from hard_chat import Chat
from hard_mail import Mail
from server import handler_factory
from http.server import ThreadingHTTPServer
with tempfile.TemporaryDirectory(prefix='hard-browser-') as directory:
 w=Workspace(Path(directory)/'Data');w.save_profile('Test user')
 folder=Path(directory)/'work';folder.mkdir();(folder/'proposal.txt').write_text('Proposal fixture');w.add_folder(str(folder),'Test projects')
 pdf=PdfWriter();pdf.add_blank_page(width=200,height=200);buffer=io.BytesIO();pdf.write(buffer);doc=w.import_document('fixture.pdf',buffer.getvalue())
 with w.db() as db:db.execute('UPDATE documents SET reviewed=1 WHERE id=?',(doc['id'],))
 AIReview(w).configure('fake-browser-key','openrouter','fixture-model',name='Primary test')
 AIReview(w).configure('fake-browser-key-2','openrouter','second-model',name='Second test')
 calls=0
 def reply(request,timeout=90):
  global calls
  calls+=1
  if calls==1:raise UserError('Synthetic offline failure')
  return io.BytesIO(json.dumps({'choices':[{'finish_reason':'stop','message':{'content':'A saved fixture answer.'}}]}).encode())
 hard_chat.urlopen=reply
 origin='http://127.0.0.1:5291'
 server=ThreadingHTTPServer(('127.0.0.1',5291),handler_factory(w,Mail(w,origin),origin))
 print(origin,flush=True)
 try:server.serve_forever()
 finally:server.server_close()
