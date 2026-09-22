import json
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import Request,urlopen
from desktop import service,smoke_test

class DesktopTests(unittest.TestCase):
    def test_fresh_workspace(self):self.assertEqual(smoke_test(),0)
    def test_oauth_opens_external_browser(self):
        with tempfile.TemporaryDirectory() as directory:
            server,thread,origin=service(directory,0)
            try:
                with urlopen(origin+'/api/state') as r:state=json.load(r)
                with patch('hard_mail.Mail.begin',return_value={'url':'https://accounts.google.com/test'}),patch('webbrowser.open',return_value=True) as opened:
                    req=Request(origin+'/api/connect',data=b'{"provider":"gmail"}',headers={'Origin':origin,'Content-Type':'application/json','X-HARD-CSRF':state['csrf']})
                    with urlopen(req) as r:self.assertEqual(json.load(r),{'external':True})
                    opened.assert_called_once_with('https://accounts.google.com/test')
            finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
