import io,json,tempfile,unittest
from unittest.mock import patch,Mock
from hard_core import Workspace,UserError
from hard_ai import AIReview,ENDPOINTS
from hard_chat import Chat
from hard_conversations import Conversations

class WebTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.w=Workspace(self.tmp.name);self.ai=AIReview(self.w)
  self.config={'provider':'openrouter','model':'test-model','endpoint':ENDPOINTS['openrouter']}
  self.ai.config=lambda:self.config;self.ai.key=lambda:'fake';self.chat=Chat(self.ai)
  self.body={'message':'Current news','confirmed':True,'provider_config':dict(self.config),'web_search':True}
 def tearDown(self):self.tmp.cleanup()
 def response(self):
  return {'choices':[{'finish_reason':'stop','message':{'content':'Answer','annotations':[{'type':'url_citation','url_citation':{'url':u,'title':'Source'}} for u in ['https://example.com/source','javascript:alert(1)','https://example.com/source','https://user:pass@example.com/']]}}]}
 def test_tool_caps_and_citations(self):
  with patch('hard_chat.urlopen',return_value=io.BytesIO(json.dumps(self.response()).encode())) as call:
   r=self.chat.answer(self.body);p=json.loads(call.call_args.args[0].data)
  self.assertEqual(p['max_tool_calls'],2);self.assertEqual(p['tools'][0]['parameters']['max_uses'],2)
  self.assertNotIn('no live web access',p['messages'][0]['content']);self.assertEqual(len(r['web']['sources']),1)
 def test_off_has_no_tools(self):
  with patch('hard_chat.urlopen',return_value=io.BytesIO(json.dumps(self.response()).encode())) as call:
   r=self.chat.answer({**self.body,'web_search':False})
  self.assertNotIn('tools',json.loads(call.call_args.args[0].data));self.assertFalse(r['web']['enabled']);self.assertEqual(r['web']['sources'],[])
 def test_unsupported_rejected_before_network(self):
  self.config.update(provider='gemini',endpoint=ENDPOINTS['gemini'])
  with patch('hard_chat.urlopen') as call:
   with self.assertRaisesRegex(UserError,'OpenRouter'):self.chat.answer({**self.body,'provider_config':dict(self.config)})
   call.assert_not_called()
 def test_missing_annotations_not_claimed(self):
  response=self.response();del response['choices'][0]['message']['annotations']
  with patch('hard_chat.urlopen',return_value=io.BytesIO(json.dumps(response).encode())):
   self.assertEqual(self.chat.answer(self.body)['web']['sources'],[])
 def test_retry_and_restart_preserve_web(self):
  chat=Mock();chat.answer.side_effect=UserError('Offline');store=Conversations(self.w,chat)
  c=store.send({**self.body,'request_id':'web1'})['conversation']
  self.assertTrue(c['messages'][-1]['web']['enabled'])
  evidence={'enabled':True,'sources':[{'url':'https://example.com/','title':'Example'}]}
  chat.answer.side_effect=None;chat.answer.return_value={'answer':'Answer','attachments':[],'web':evidence}
  store.retry({'turn_id':'web1','conversation_id':c['id'],'confirmed':True,'web_search':False})
  self.assertTrue(chat.answer.call_args.args[0]['web_search'])
  restored=Conversations(self.w,chat).get(c['id']);self.assertEqual(restored['messages'][-1]['web'],evidence)
 def test_legacy_schema_migration(self):
  with self.w.db() as db:
   db.execute("CREATE TABLE chat_turns(id TEXT PRIMARY KEY,conversation_id TEXT,question TEXT,answer TEXT,error TEXT,status TEXT,sources TEXT DEFAULT '[]',files TEXT DEFAULT '[]',created REAL)")
   db.execute("INSERT INTO chat_turns VALUES('old','c','Question','Answer',NULL,'complete','[]','[]',1)")
  store=Conversations(self.w,Mock())
  with self.w.db() as db:
   self.assertEqual(db.execute("SELECT web FROM chat_turns WHERE id='old'").fetchone()[0],'{}')
