"""Open Windows voice typing only while HARD owns the foreground window."""
import ctypes
from ctypes import wintypes
import os
from hard_core import UserError

class KeyboardInput(ctypes.Structure):
    _fields_=[('vk',wintypes.WORD),('scan',wintypes.WORD),('flags',wintypes.DWORD),('time',wintypes.DWORD),('extra',ctypes.c_size_t)]
class MouseInput(ctypes.Structure):
    _fields_=[('dx',wintypes.LONG),('dy',wintypes.LONG),('data',wintypes.DWORD),('flags',wintypes.DWORD),('time',wintypes.DWORD),('extra',ctypes.c_size_t)]
class InputUnion(ctypes.Union):
    _fields_=[('keyboard',KeyboardInput),('mouse',MouseInput)]
class Input(ctypes.Structure):
    _fields_=[('type',wintypes.DWORD),('value',InputUnion)]

def start_voice_typing():
    if os.name!='nt':raise UserError('Windows voice typing is available in the Windows desktop app.')
    user=ctypes.WinDLL('user32',use_last_error=True)
    user.GetForegroundWindow.restype=wintypes.HWND
    user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    pid=wintypes.DWORD();window=user.GetForegroundWindow()
    user.GetWindowThreadProcessId(window,ctypes.byref(pid))
    if pid.value!=os.getpid():raise UserError('Bring HARD to the front, click your message, then choose Dictate again. You can also press Windows + H.')
    user.SendInput.argtypes=[wintypes.UINT,ctypes.POINTER(Input),ctypes.c_int]
    user.SendInput.restype=wintypes.UINT
    events=(Input*4)(*[Input(1,InputUnion(keyboard=KeyboardInput(key,0,flags,0,0))) for key,flags in [(0x5b,0),(0x48,0),(0x48,2),(0x5b,2)]])
    if user.SendInput(4,events,ctypes.sizeof(Input))!=4:
        release=(Input*2)(events[2],events[3]);user.SendInput(2,release,ctypes.sizeof(Input))
        raise UserError('Windows could not open voice typing. Click your message and press Windows + H.')
    return {'requested':True}
