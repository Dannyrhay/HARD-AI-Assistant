import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from hard_core import Workspace, UserError
from hard_ai import AIReview

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.w=Workspace(Path(self.tmp.name)/'data');self.ai=AIReview(self.w)
        self.doc=self.w.import_document('test.txt',b'Water proposal. Work starts June 1.')
        self.key=patch.object(self.ai,'key',return_value='fake-key');self.key.start()
    def tearDown(self):self.key.stop();self.tmp.cleanup()
    def response(self,quote='Work starts June 1.'):
        data={'summary':'Confirm the start date.','findings':[{'category':'Dates','quote':quote,'concern':'Year is absent.','suggestion':'Confirm the intended year.'}]}
        return io.BytesIO(json.dumps({'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(data)}]}]}).encode())
    def test_consent_before_network(self):
        with patch('hard_ai.urlopen') as call:
            with self.assertRaises(UserError):self.ai.review(self.doc['id'],False)
            call.assert_not_called()
    def test_saved_review_and_no_document_changes(self):
        before=self.w.path(self.doc['id']).read_bytes()
        with patch('hard_ai.urlopen',return_value=self.response()) as call:
            self.ai.review(self.doc['id'],True);self.ai.review(self.doc['id'],True)
            call.assert_called_once()
            payload=json.loads(call.call_args.args[0].data)
            self.assertFalse(payload['store']);self.assertNotIn('tools',payload)
        self.assertEqual(before,self.w.path(self.doc['id']).read_bytes())
        self.assertFalse(self.w.document(self.doc['id'])['reviewed'])
        self.assertIsNotNone(AIReview(self.w).saved(self.doc['id']))
    def test_unanchored_quote_rejected(self):
        with patch('hard_ai.urlopen',return_value=self.response('Invented passage')):
            with self.assertRaises(UserError):self.ai.review(self.doc['id'],True)
        self.assertIsNone(self.ai.saved(self.doc['id']))
    def test_refusal_rejected(self):
        with patch('hard_ai.urlopen',return_value=io.BytesIO(b'{"status":"completed","output":[]}')):
            with self.assertRaises(UserError):self.ai.review(self.doc['id'],True)
    def test_long_document_not_sent(self):
        doc=self.w.import_document('long.txt',b'a'*60001)
        with patch('hard_ai.urlopen') as call:
            with self.assertRaises(UserError):self.ai.review(doc['id'],True)
            call.assert_not_called()
    def test_http_error_does_not_expose_secrets(self):
        with patch('hard_ai.urlopen',side_effect=HTTPError('https://api.openai.com',401,'secret detail',{},None)):
            with self.assertRaises(UserError) as e:self.ai.review(self.doc['id'],True)
        self.assertNotIn('secret detail',str(e.exception))
    def test_configuration_encrypted_and_status_redacted(self):
        self.key.stop()
        with patch.dict('os.environ',{},clear=True):
            self.ai.configure('sk-'+'fake'*10)
            self.assertNotIn(b'fake',(self.w.directory/'ai.key').read_bytes())
            self.assertNotIn('sk-',json.dumps(self.ai.status()))
    def test_generic_gemini_model_rejected(self):
        with self.assertRaises(UserError):self.ai.configure('fake-key-long-enough','gemini','Gemini')
    def test_busy_provider_error_is_actionable(self):
        with patch('hard_ai.urlopen',side_effect=HTTPError('https://example.com',503,'busy',{},io.BytesIO(b'{"error":{"message":"high demand"}}'))):
            with self.assertRaisesRegex(UserError,'temporarily busy'):self.ai.review(self.doc['id'],True)
    def test_invalid_model_error_is_actionable(self):
        with patch('hard_ai.urlopen',side_effect=HTTPError('https://example.com',400,'bad',{},io.BytesIO(b'[{"error":{"message":"unexpected model name format"}}]'))):
            with self.assertRaisesRegex(UserError,'exact model identifier'):self.ai.review(self.doc['id'],True)
    def test_busy_review_rejected(self):
        self.ai.lock.acquire()
        try:
            with self.assertRaises(UserError):self.ai.review(self.doc['id'],True)
        finally:self.ai.lock.release()

if __name__=='__main__':unittest.main(verbosity=2)
