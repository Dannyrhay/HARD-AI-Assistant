import io,json,tempfile,unittest
from unittest.mock import patch
from hard_models import ModelCatalog
from hard_ai import AIReview
from hard_core import Workspace,UserError
class ModelTests(unittest.TestCase):
 def response(self):return io.BytesIO(json.dumps({'data':[{'id':'a/text','name':'Text','architecture':{'output_modalities':['text'],'input_modalities':['text']},'pricing':{'prompt':'0','completion':'0'}},{'id':'a/vision','architecture':{'output_modalities':['text'],'input_modalities':['text','image']}},{'id':'a/image','architecture':{'output_modalities':['image']}},{'id':'<bad>','architecture':{'output_modalities':['text']}}]}).encode())
 def test_catalog_filter_cache_no_auth(self):
  c=ModelCatalog()
  with patch('hard_models.urlopen',return_value=self.response()) as request:
   r=c.list();self.assertEqual(len(r['models']),2);self.assertTrue(c.list()['cached']);request.assert_called_once();self.assertNotIn('Authorization',request.call_args.args[0].headers)
  with patch('hard_models.urlopen',side_effect=OSError()):self.assertTrue(c.list(True)['stale'])
 def test_first_failure(self):
  with patch('hard_models.urlopen',side_effect=OSError()):
   with self.assertRaises(UserError):ModelCatalog().list()
 def test_switch_keeps_key(self):
  with tempfile.TemporaryDirectory() as d:
   ai=AIReview(Workspace(d));a=ai.configure('fake-router-key-long','openrouter','a/text');ai.select_model(a['connection_id'],'a/vision');self.assertEqual(ai.key(),'fake-router-key-long');self.assertEqual(ai.config()['model'],'a/vision')
   with self.assertRaises(UserError):ai.select_model('other','a/text')
 def test_existing_custom_connection(self):
  with tempfile.TemporaryDirectory() as d:
   ai=AIReview(Workspace(d));a=ai.configure('fake-router-key-long','compatible','a/text','https://openrouter.ai/api/v1/chat/completions');ai.select_model(a['connection_id'],'a/vision');self.assertEqual(ai.config()['model'],'a/vision')
