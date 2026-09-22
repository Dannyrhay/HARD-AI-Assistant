import tempfile,unittest,json,io
from unittest.mock import patch
from hard_core import Workspace,UserError
from hard_ai import AIReview,ENDPOINTS
from hard_chat import Chat
from hard_mail import protect
class ConnectionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.w=Workspace(self.tmp.name);self.ai=AIReview(self.w)
 def tearDown(self):self.tmp.cleanup()
 def test_multiple_restart_and_no_secrets(self):
  a=self.ai.configure('key-one-long-enough','gemini','gemini-test',name='Work Gemini')
  b=self.ai.configure('key-two-long-enough','anthropic','claude-test',name='Writing')
  self.assertEqual(len(b['connections']),2);self.assertNotIn('key-one',json.dumps(b));self.assertNotIn(b'key-two',(self.w.directory/'ai.connections').read_bytes())
  ai=AIReview(self.w);ai.select(a['connection_id']);self.assertEqual(ai.key(),'key-one-long-enough');self.assertEqual(ai.status()['label'],'Google Gemini')
 def test_legacy_migration(self):
  c={'provider':'gemini','model':'gemini-test','endpoint':ENDPOINTS['gemini'],'key':'old-key-long-enough'}
  (self.w.directory/'ai.config').write_bytes(protect(json.dumps(c).encode()))
  self.assertEqual(self.ai.status()['connection_id'],'legacy')
  self.ai.configure('new-key-long-enough','anthropic','claude-test');self.ai.select('legacy');self.assertEqual(self.ai.key(),c['key'])
 def test_invalid_selection_no_change(self):
  a=self.ai.configure('key-one-long-enough')
  with self.assertRaises(UserError):self.ai.select('missing')
  self.assertEqual(self.ai.status()['connection_id'],a['connection_id'])
 def test_same_model_different_key_stale_selection_blocked(self):
  a=self.ai.configure('key-one-long-enough');self.ai.configure('key-two-long-enough')
  with patch('hard_chat.urlopen') as call:
   with self.assertRaisesRegex(UserError,'connection changed'):Chat(self.ai).answer({'confirmed':True,'message':'hello','connection_id':a['connection_id'],'provider_config':{k:a[k] for k in ('provider','model','endpoint')}})
   call.assert_not_called()
