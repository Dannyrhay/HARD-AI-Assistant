import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from hard_core import Workspace,UserError
from hard_ai import AIReview
from hard_mail import Mail
class ExpandedTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.w=Workspace(self.root/'data');self.work=self.root/'work';self.work.mkdir();(self.work/'a.txt').write_text('same');(self.work/'b.txt').write_text('same');(self.work/'c.txt').write_text('diff');self.w.add_folder(str(self.work),'Work');self.file=next(x for x in self.w.search() if x['name']=='a.txt')
 def tearDown(self):self.tmp.cleanup()
 def test_rename_and_undo(self):
  result=self.w.rename_file(self.file['id'],'renamed.txt',True);self.assertFalse((self.work/'a.txt').exists());self.assertEqual((self.work/'renamed.txt').read_text(),'same');self.w.rename_file(result['id'],result['previous_name'],True);self.assertTrue((self.work/'a.txt').exists())
 def test_rename_rejects_collision_and_extension_and_escape(self):
  for name in ['b.txt','a.pdf','../x.txt','CON.txt','a.txt.']:
   with self.assertRaises(UserError):self.w.rename_file(self.file['id'],name,True)
  self.assertEqual((self.work/'a.txt').read_text(),'same')
 def test_rename_requires_confirmation(self):
  with self.assertRaises(UserError):self.w.rename_file(self.file['id'],'renamed.txt',False)
 def test_duplicates_use_content_not_name(self):
  r=self.w.duplicates();self.assertEqual(len(r['groups']),1);self.assertEqual({x['name'] for x in r['groups'][0]['files']},{'a.txt','b.txt'});self.assertEqual(len(list(self.work.iterdir())),3)
 def test_typed_recipient_not_saved_or_verified(self):
  doc={'suffix':'.pdf','reviewed':True,'name':'p.pdf','hash':'x'}
  with patch.object(self.w,'document',return_value=doc):
   draft=self.w.stage_email(None,'pdf','Subject','Message','gmail',True,{'name':'Client','email':'client@example.com','confirmed':True})
  self.assertIsNone(draft['payload']['contact']['verified']);self.assertEqual(self.w.contacts(),[])
 def test_invalid_typed_recipients(self):
  for address in ['client@example.com.','client@bad..com','client@-bad.com','client@example.com\nBcc:x@y.com']:
   with self.assertRaises(UserError):self.w.stage_email(None,'pdf','Subject','Message','gmail',True,{'name':'Client','email':address,'confirmed':True})
  with self.assertRaises(UserError):self.w.stage_email(None,'pdf','Subject','Message','gmail',True,{'name':'Client','email':'client@example.com','confirmed':False})
 def test_delivery_status_caches_and_reports_unavailable(self):
  mail=Mail(self.w,'http://127.0.0.1:5188')
  with patch.object(mail,'status',return_value={'gmail':{'connected':True},'outlook':{'connected':False}}),patch.object(mail,'failures',return_value={'messages':[{'subject':'Delivery failed','date':'today'}]}) as call:
   self.assertEqual(mail.delivery_status()['messages'][0]['provider'],'gmail');mail.delivery_status();call.assert_called_once()
  mail.delivery_cache=None
  with patch.object(mail,'status',return_value={'gmail':{'connected':True}}),patch.object(mail,'failures',side_effect=UserError('offline')):self.assertEqual(mail.delivery_status()['errors'],['gmail'])
 def test_provider_adapters_and_encryption(self):
  for provider in ['gemini','anthropic','compatible']:
   with self.subTest(provider=provider):
    w=Workspace(self.root/provider);ai=AIReview(w);model='gemini-test-model' if provider=='gemini' else 'test-model';ai.configure('test-key-not-real-123456',provider,model,'https://example.com/v1/chat/completions');doc=w.import_document('test.txt',b'Source document text.');value={'summary':'Checked','findings':[]}
    response={'stop_reason':'end_turn','content':[{'type':'text','text':json.dumps(value)}]} if provider=='anthropic' else {'choices':[{'finish_reason':'stop','message':{'content':json.dumps(value)}}]}
    with patch('hard_ai.urlopen',return_value=io.BytesIO(json.dumps(response).encode())) as call:
     result=ai.review(doc['id'],True);self.assertEqual(result['provider'],provider);request=call.call_args.args[0];self.assertEqual(json.loads(request.data)['model'],model);self.assertNotIn('tools',json.loads(request.data))
    self.assertNotIn('test-key',json.dumps(ai.status()));self.assertNotIn(b'test-key',(w.directory/'ai.config').read_bytes())
 def test_bad_endpoints_rejected(self):
  ai=AIReview(self.w)
  for endpoint in ['http://example.com/v1/chat/completions','https://user:key@example.com/v1/chat/completions','https://example.com/v1/chat/completions?key=secret','https://example.com/wrong']:
   with self.assertRaises(UserError):ai.configure('test-key-not-real-123456','compatible','test',endpoint)

class RejectedSendTests(unittest.TestCase):
 def test_explicit_rejection_is_failed_not_uncertain(self):
  from test_hard import CoreTests
  from hard_mail import ProviderRejected
  fixture=CoreTests();fixture.setUp()
  try:
   draft=fixture.draft();mail=Mail(fixture.w,'http://127.0.0.1:5188')
   with patch.object(mail,'access',return_value={'access_token':'fake','address':'sender@example.com'}),patch('hard_mail.request_json',side_effect=ProviderRejected('Rejected')):
    approval=mail.approve(draft['id'],True,'sender@example.com')
    with self.assertRaises(UserError):mail.send(draft['id'],approval['approval'])
   self.assertEqual(fixture.w.draft(draft['id'])['status'],'failed')
  finally:fixture.tearDown()
