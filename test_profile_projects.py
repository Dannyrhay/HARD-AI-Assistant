import tempfile,unittest
from pathlib import Path
from hard_core import Workspace,UserError
class ProfileProjects(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.base=Path(self.temp.name);self.w=Workspace(self.base/'data');self.work=self.base/'work';self.work.mkdir();(self.work/'report.txt').write_text('Original report');self.w.add_folder(str(self.work),'Work');self.file=self.w.search()[0];self.folder=self.w.snapshot()['folders'][0]['id']
 def tearDown(self):self.temp.cleanup()
 def test_profile_persists_and_clears_notes(self):
  self.assertIsNone(self.w.profile());self.w.save_profile('Ama','Consultant','Prefer concise notes');self.assertEqual(Workspace(self.base/'data').profile()['name'],'Ama');self.w.save_profile('Ama');self.assertEqual(self.w.profile()['preferences'],'')
 def test_profile_validation(self):
  for name in ['', 'x'*101]:
   with self.assertRaises(UserError):self.w.save_profile(name)
 def test_project_copy_keeps_original_and_is_searchable(self):
  result=self.w.organise_file(self.file['id'],self.folder,'Water study');self.assertTrue(result['original_kept']);self.assertEqual(Path(result['path']).read_text(),'Original report');self.assertTrue((self.work/'report.txt').exists());self.assertEqual(len(self.w.search('Water study')),1)
 def test_no_overwrite(self):
  self.w.organise_file(self.file['id'],self.folder,'Water study')
  with self.assertRaises(UserError):self.w.organise_file(self.file['id'],self.folder,'Water study')
  self.assertEqual((self.work/'Water study/report.txt').read_text(),'Original report')
 def test_reject_escape_and_reserved_names(self):
  for project in ['../escape','nested/path','CON','LPT1','a:b','..']:
   with self.assertRaises(UserError):self.w.organise_file(self.file['id'],self.folder,project)
 def test_missing_source(self):
  (self.work/'report.txt').unlink()
  with self.assertRaises(UserError):self.w.organise_file(self.file['id'],self.folder,'Water study')
