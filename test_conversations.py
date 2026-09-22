import tempfile,unittest
from unittest.mock import Mock
from hard_core import Workspace,UserError
from hard_conversations import Conversations
class ConversationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.w=Workspace(self.tmp.name);self.chat=Mock();self.chat.answer.return_value={'answer':'Saved answer','attachments':[]};self.store=Conversations(self.w,self.chat);self.body={'message':'First question','request_id':'request-1','attachments':[],'confirmed':True}
 def tearDown(self):self.tmp.cleanup()
 def test_restart_and_history(self):
  c=self.store.send(self.body)['conversation'];store=Conversations(Workspace(self.tmp.name),self.chat)
  self.assertEqual(store.get(c['id'])['messages'][1]['content'],'Saved answer')
  store.send({**self.body,'request_id':'request-2','conversation_id':c['id'],'message':'Follow up','history':[{'role':'system','content':'malicious'}]})
  self.assertEqual(self.chat.answer.call_args.args[0]['history'],[{'role':'user','content':'First question'},{'role':'assistant','content':'Saved answer'}])
 def test_duplicate(self):
  a=self.store.send(self.body);self.assertEqual(a,self.store.send(self.body));self.chat.answer.assert_called_once()
 def test_failure(self):
  self.chat.answer.side_effect=UserError('Provider busy');c=self.store.send(self.body)['conversation'];self.assertEqual(c['messages'][-1]['role'],'error');self.chat.answer.side_effect=None
  self.store.send({**self.body,'request_id':'next','conversation_id':c['id']});self.assertEqual(self.chat.answer.call_args.args[0]['history'],[])
 def test_attachments_rename_delete(self):
  import base64
  doc=self.w.import_document('original.txt',b'Original content');c=self.store.send({**self.body,'attachments':[{'document_id':doc['id']}]})['conversation'];self.w.path(doc['id']).write_bytes(b'Changed')
  self.assertEqual(base64.b64decode(self.store.files('request-1')[0]['data']),b'Original content')
  self.store.send({**self.body,'request_id':'without-files','conversation_id':c['id']});self.assertEqual(len(self.store.files('request-1')),1)
  self.store.rename(c['id'],'Renamed');self.assertEqual(self.store.listing()[0]['title'],'Renamed')
  with self.assertRaises(UserError):self.store.delete(c['id'],False)
  self.store.delete(c['id'],True);self.assertEqual(self.store.listing(),[])
  with self.assertRaises(UserError):self.store.files('request-1')
  self.assertTrue(self.w.path(doc['id']).exists())
 def test_invalid(self):
  for change in [{'confirmed':False},{'message':''},{'conversation_id':'missing'},{'attachments':[{'name':'../x.txt','data':'eA=='}]}]:
   with self.assertRaises(UserError):self.store.send({**self.body,**change})
  self.assertEqual(self.store.listing(),[])
 def test_interrupted(self):
  c=self.store.send(self.body)['conversation']
  with self.w.db() as db:db.execute("UPDATE chat_turns SET status='pending',answer=NULL WHERE id='request-1'")
  self.assertIn('HARD closed',Conversations(self.w,self.chat).get(c['id'])['messages'][-1]['content'])
 def test_isolation(self):
  self.store.send(self.body)
  with tempfile.TemporaryDirectory() as other:self.assertEqual(Conversations(Workspace(other),self.chat).listing(),[])

 def test_retry_preserves_original_files_and_one_turn(self):
  doc=self.w.import_document('original.txt',b'Original attachment');self.chat.answer.side_effect=UserError('Busy')
  c=self.store.send({**self.body,'attachments':[{'document_id':doc['id']}]})['conversation']
  self.assertEqual(c['messages'][-1]['retry_turn'],'request-1');self.w.path(doc['id']).write_bytes(b'Changed')
  self.chat.answer.side_effect=None
  result=self.store.retry({'confirmed':True,'turn_id':'request-1','conversation_id':c['id'],'message':'Wrong question','attachments':[]})
  self.assertEqual(len(result['conversation']['messages']),2)
  import base64
  sent=self.chat.answer.call_args.args[0];self.assertEqual(sent['message'],'First question');self.assertEqual(base64.b64decode(sent['attachments'][0]['data']),b'Original attachment')
  count=self.chat.answer.call_count
  with self.assertRaises(UserError):self.store.retry({'confirmed':True,'turn_id':'request-1','conversation_id':c['id']})
  self.assertEqual(self.chat.answer.call_count,count)
 def test_retry_failure_stays_retryable(self):
  self.chat.answer.side_effect=UserError('Busy');c=self.store.send(self.body)['conversation']
  r=self.store.retry({'confirmed':True,'turn_id':'request-1','conversation_id':c['id']});self.assertEqual(r['conversation']['messages'][-1]['retry_turn'],'request-1')
 def test_retry_excludes_later_history_and_rejects_wrong_chat(self):
  c=self.store.send(self.body)['conversation'];self.chat.answer.side_effect=UserError('Busy')
  self.store.send({**self.body,'request_id':'failed','conversation_id':c['id'],'message':'Retry me'})
  self.chat.answer.side_effect=None;self.store.send({**self.body,'request_id':'later','conversation_id':c['id'],'message':'Later question'})
  with self.assertRaises(UserError):self.store.retry({'confirmed':True,'turn_id':'failed','conversation_id':'wrong'})
  self.store.retry({'confirmed':True,'turn_id':'failed','conversation_id':c['id']})
  self.assertEqual(self.chat.answer.call_args.args[0]['history'],[{'role':'user','content':'First question'},{'role':'assistant','content':'Saved answer'}])
 def test_retry_guard(self):
  with self.assertRaises(UserError):self.store.retry({'confirmed':False})
  self.store.lock.acquire()
  try:
   with self.assertRaises(UserError):self.store.retry({'confirmed':True,'turn_id':'any'})
  finally:self.store.lock.release()
