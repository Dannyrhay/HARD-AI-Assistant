import io,json,sqlite3,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import Mock
from hard_core import Workspace,UserError
from hard_workflows import FileJournal,DraftRecovery,route_request,email_preflight
from hard_conversations import Conversations
from hard_backup import create_backup,restore_backup

class WorkflowTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.w=Workspace(self.root/'Data');self.work=self.root/'work';self.work.mkdir();(self.work/'proposal.txt').write_text('Original proposal');self.w.add_folder(str(self.work),'Projects');self.file=self.w.search()[0];self.folder=self.w.snapshot()['folders'][0]['id'];self.journal=FileJournal(self.w)
 def tearDown(self):self.temp.cleanup()
 def test_routing_does_not_call_provider_or_perform_action(self):
  provider=Mock();store=Conversations(self.w,provider)
  c=store.send({'message':'Find my latest proposal','request_id':'local1','confirmed':True})['conversation']
  provider.answer.assert_not_called();self.assertEqual(c['messages'][-1]['actions'][0]['query'],'proposal');self.assertEqual(len(list(self.work.iterdir())),1)
  self.assertEqual(Conversations(self.w,provider).get(c['id'])['messages'][-1]['actions'][0]['kind'],'files')
 def test_no_action_from_quoted_or_general_questions(self):
  self.assertIsNone(route_request(self.w,'Explain the phrase "send an email"',[]))
  self.assertIsNone(route_request(self.w,'What is a watershed?',[]))
  self.assertEqual(route_request(self.w,'Prepare an email to client@example.com',[])['actions'][0]['recipient'],'client@example.com')
 def test_copy_undo_survives_restart(self):
  result=self.journal.perform('copy',{'id':self.file['id'],'folder_id':self.folder,'project':'New project','confirmed':True})
  self.assertTrue(Path(result['path']).exists());FileJournal(self.w).undo(result['operation_id'],True)
  self.assertFalse(Path(result['path']).exists());self.assertEqual((self.work/'proposal.txt').read_text(),'Original proposal')
 def test_move_preview_confirmation_and_durable_undo(self):
  body={'id':self.file['id'],'folder_id':self.folder,'project':'Client','confirmed':False}
  with self.assertRaises(UserError):self.journal.perform('move',body)
  result=self.journal.perform('move',{**body,'confirmed':True})
  self.assertFalse((self.work/'proposal.txt').exists());self.assertTrue(Path(result['path']).exists())
  FileJournal(self.w).undo(result['operation_id'],True);self.assertTrue((self.work/'proposal.txt').exists())
 def test_rename_undo_protects_modified_file(self):
  r=self.journal.perform('rename',{'id':self.file['id'],'name':'renamed.txt','confirmed':True})
  target=self.work/'renamed.txt';target.write_text('New content')
  with self.assertRaises(UserError):self.journal.undo(r['operation_id'],True)
  self.assertEqual(target.read_text(),'New content')
 def test_undo_collision_and_confirmation(self):
  r=self.journal.perform('rename',{'id':self.file['id'],'name':'renamed.txt','confirmed':True})
  with self.assertRaises(UserError):self.journal.undo(r['operation_id'],False)
  (self.work/'proposal.txt').write_text('Another file')
  with self.assertRaises(UserError):self.journal.undo(r['operation_id'],True)
 def test_copy_no_overwrite_and_original_missing(self):
  body={'id':self.file['id'],'folder_id':self.folder,'project':'Client','confirmed':True};r=self.journal.perform('copy',body)
  with self.assertRaises(UserError):self.journal.perform('copy',body)
  (self.work/'proposal.txt').unlink()
  with self.assertRaises(UserError):self.journal.undo(r['operation_id'],True)
  self.assertTrue(Path(r['path']).exists())
 def test_drafts_survive_restart_without_approval_or_secrets(self):
  c=Conversations(self.w,Mock());drafts=DraftRecovery(self.w,c)
  drafts.save({'chat':{'message':'Unsent question','files':[{'name':'notes.txt','data':'bm90ZXM='}]},'email':{'subject':'Proposal','body':'Draft body','confirmed':True,'api_key':'secret'}})
  recovered=DraftRecovery(Workspace(self.root/'Data'),c).load()
  self.assertEqual(recovered['chat']['message'],'Unsent question');self.assertEqual(len(recovered['chat']['files']),1);self.assertNotIn('confirmed',recovered['email']);self.assertNotIn('api_key',recovered['email'])
  with self.assertRaises(UserError):drafts.save({'chat':{'message':'x'*8001}})
 def test_preflight_typos_placeholders_and_promised_files(self):
  doc=self.w.import_document('proposal.txt',b'Sample')
  result=email_preflight(self.w,{'recipient':{'email':'client@gmial.com'},'document_id':doc['id'],'subject':'[client]','body':'See budget.xlsx and both attachments.'})
  self.assertEqual(len(result['warnings']),5)
  self.assertNotEqual(result['token'],email_preflight(self.w,{'subject':'Changed'})['token'])
 def test_backup_roundtrip_excludes_keys_and_preserves_current_credentials(self):
  self.w.import_document('proposal.txt',b'Original proposal');self.w.save_profile('Test user');(self.w.directory/'ai.key').write_bytes(b'secret')
  archive=create_backup(self.w)
  with zipfile.ZipFile(io.BytesIO(archive)) as z:self.assertNotIn('ai.key',z.namelist())
  backup=self.root/'backup.zip';backup.write_bytes(archive);destination=self.root/'Restored';destination.mkdir();(destination/'ai.key').write_bytes(b'current-key')
  r=restore_backup(backup,destination);restored=Workspace(destination)
  self.assertEqual(restored.profile()['name'],'Test user');self.assertEqual(restored.list_documents()[0]['name'],'proposal.txt');self.assertEqual(restored.snapshot()['folders'],[]);self.assertEqual((destination/'ai.key').read_bytes(),b'current-key');self.assertTrue(Path(r['previous']).exists())
 def test_bad_backup_leaves_current_data_untouched(self):
  backup=self.root/'bad.zip'
  with zipfile.ZipFile(backup,'w') as z:z.writestr('manifest.json',json.dumps({'format':'hard-backup','version':1,'files':{'../outside':'bad'}}));z.writestr('../outside','bad')
  self.w.save_profile('Keep me')
  with self.assertRaises(UserError):restore_backup(backup,self.w.directory)
  self.assertEqual(self.w.profile()['name'],'Keep me');self.assertFalse((self.root/'outside').exists())
