import unittest,tempfile,base64
from unittest.mock import patch
from hard_core import Workspace,UserError
from hard_mail import Mail
class DeliveryNoticeTests(unittest.TestCase):
 def test_structured_reason_excludes_original_message(self):
  raw=b'MIME-Version: 1.0\r\nContent-Type: multipart/report; boundary=x; report-type=delivery-status\r\n\r\n--x\r\nContent-Type: text/plain\r\n\r\nPrivate original content\r\n--x\r\nContent-Type: message/delivery-status\r\n\r\nReporting-MTA: dns; example.com\r\n\r\nFinal-Recipient: rfc822; wrong@example.com\r\nAction: failed\r\nStatus: 5.1.3\r\nDiagnostic-Code: smtp; Mailbox does not exist\r\n\r\n--x--\r\n'
  with tempfile.TemporaryDirectory() as tmp:
   mail=Mail(Workspace(tmp),'http://127.0.0.1:5188')
   with patch.object(mail,'access',return_value={'access_token':'test'}),patch('hard_mail.request_json',return_value={'raw':base64.urlsafe_b64encode(raw).decode()}):
    result=mail.notice_details('gmail','abc123');self.assertEqual(result['diagnostics'][0]['status'],'5.1.3');self.assertNotIn('Private original',str(result))
   for provider,id in [('outlook','abc'),('gmail','../bad')]:
    with self.assertRaises(UserError):mail.notice_details(provider,id)

 def test_handled_survives_restart_and_new_notices_still_alert(self):
  with tempfile.TemporaryDirectory() as tmp:
   w=Workspace(tmp);mail=Mail(w,'http://127.0.0.1:5188');accounts={'gmail':{'connected':True,'address':'one@example.com'}}
   notices=[{'id':'abc','subject':'Failure','date':'old'}]
   with patch.object(mail,'status',return_value=accounts),patch.object(mail,'failures',return_value={'messages':notices}):
    first=mail.delivery_status();key=first['messages'][0]['key'];handled=mail.handle_notice(key,True);self.assertEqual(handled['messages'],[]);self.assertEqual(len(handled['handled']),1)
   restarted=Mail(w,'http://127.0.0.1:5188');notices.append({'id':'def','subject':'Failure','date':'new'})
   with patch.object(restarted,'status',return_value=accounts),patch.object(restarted,'failures',return_value={'messages':notices}):
    result=restarted.delivery_status();self.assertEqual([n['id'] for n in result['messages']],['def']);self.assertEqual(len(result['handled']),1)
    self.assertEqual(len(restarted.handle_notice(key,False)['messages']),2)
   with patch.object(restarted,'status',return_value={'gmail':{'connected':True,'address':'other@example.com'}}),patch.object(restarted,'failures',return_value={'messages':[]}):
    self.assertEqual(restarted.delivery_status(force=True)['messages'],[])
    with self.assertRaises(UserError):restarted.handle_notice(key,True)
 def test_restore_old_handled_notice_outside_scan_window(self):
  with tempfile.TemporaryDirectory() as tmp:
   mail=Mail(Workspace(tmp),'http://127.0.0.1:5188')
   with patch.object(mail,'status',return_value={'gmail':{'connected':True,'address':'one@example.com'}}),patch.object(mail,'failures',return_value={'messages':[{'id':'abc','subject':'Failure'}]}) as fetch:
    key=mail.delivery_status()['messages'][0]['key'];mail.handle_notice(key,True);fetch.return_value={'messages':[]};mail.delivery_status(force=True)
    self.assertEqual(mail.handle_notice(key,False)['messages'][0]['id'],'abc')
