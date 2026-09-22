import ctypes,os,unittest
from unittest.mock import Mock,patch
from hard_core import UserError
from hard_voice import start_voice_typing,Input
class VoiceTests(unittest.TestCase):
 def user(self,pid):
  user=Mock();user.GetForegroundWindow.return_value=123
  def owner(window,ptr):ptr._obj.value=pid
  user.GetWindowThreadProcessId.side_effect=owner;user.SendInput.return_value=4
  return user
 def test_keyboard_sequence_and_structure(self):
  user=self.user(os.getpid())
  with patch('hard_voice.ctypes.WinDLL',return_value=user):self.assertTrue(start_voice_typing()['requested'])
  count,events,size=user.SendInput.call_args.args
  self.assertEqual(count,4);self.assertEqual(size,40 if ctypes.sizeof(ctypes.c_void_p)==8 else 28)
  self.assertEqual([(x.value.keyboard.vk,x.value.keyboard.flags) for x in events],[(91,0),(72,0),(72,2),(91,2)])
 def test_other_window_rejected(self):
  user=self.user(os.getpid()+1)
  with patch('hard_voice.ctypes.WinDLL',return_value=user):
   with self.assertRaisesRegex(UserError,'Bring HARD'):start_voice_typing()
  user.SendInput.assert_not_called()
 def test_failed_input_releases_keys(self):
  user=self.user(os.getpid());user.SendInput.return_value=0
  with patch('hard_voice.ctypes.WinDLL',return_value=user):
   with self.assertRaisesRegex(UserError,'Windows could not'):start_voice_typing()
  self.assertEqual(user.SendInput.call_count,2)
