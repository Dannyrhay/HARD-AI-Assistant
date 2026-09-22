"""HARD Windows shell. Private per-user data; embedded UI, external OAuth sign-in."""
import ctypes
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
from hard_core import Workspace
from hard_mail import Mail
from server import handler_factory

def data_directory():
    return Path(os.environ['LOCALAPPDATA'])/'HARD Assistant'/'Data'

def service(directory,port=5188):
    workspace=Workspace(directory)
    server=ThreadingHTTPServer(('127.0.0.1',port),lambda *args:None)
    origin=f'http://127.0.0.1:{server.server_port}'
    server.RequestHandlerClass=handler_factory(workspace,Mail(workspace,origin),origin,desktop=True)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    return server,thread,origin

def smoke_test(window_test=False):
    with tempfile.TemporaryDirectory() as directory:
        server,thread,origin=service(directory,0)
        try:
            with urlopen(origin+'/api/state') as r:state=json.load(r)
            assert state['desktop'] and not state['documents']
            assert not any(a['connected'] for a in state['accounts'].values())
            with urlopen(origin+'/') as r:assert b'HARD' in r.read()
            assert (Path(__file__).parent/'word-export.ps1').exists()
            if window_test:
                import webview
                loaded=threading.Event()
                window=webview.create_window('HARD startup check',origin,hidden=True)
                def ready():
                    loaded.set()
                    window.destroy()
                window.events.loaded += ready
                timer=threading.Timer(30,window.destroy);timer.daemon=True;timer.start()
                try:webview.start(gui='edgechromium',debug=False)
                finally:timer.cancel()
                assert loaded.is_set(), 'Desktop window did not load'

        finally:server.shutdown();server.server_close();thread.join()
    return 0

def main():
    if '--smoke-test' in sys.argv:return smoke_test()
    if '--window-smoke' in sys.argv:return smoke_test(True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateMutexW.restype=ctypes.c_void_p
    kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p]
    handle=kernel.CreateMutexW(None,False,'Local\\HARD-Assistant-Desktop')
    if ctypes.get_last_error()==183:
        ctypes.windll.user32.MessageBoxW(None,'HARD is already open. Switch to its window.','HARD Assistant',64)
        return 0
    server=None
    try:
        import webview
        directory=data_directory();directory.mkdir(parents=True,exist_ok=True)
        server,thread,origin=service(directory)
        webview.settings['ALLOW_DOWNLOADS']=True
        webview.settings['ALLOW_FILE_URLS']=False
        webview.create_window('HARD Assistant',origin,width=1100,height=820,min_size=(520,600),background_color='#f7f8f5',text_select=True,zoomable=True,confirm_close=True)
        webview.start(gui='edgechromium',private_mode=False,storage_path=str(directory.parent/'Browser'),debug=False)
        return 0
    except OSError:
        ctypes.windll.user32.MessageBoxW(None,'HARD could not start. Close any development copy using port 5188, then try again. Check that your Windows user folder is writable.','HARD Assistant',16)
        return 1
    except Exception:
        ctypes.windll.user32.MessageBoxW(None,'HARD could not open its window. Install Microsoft Edge WebView2 Runtime, then restart HARD. See DESKTOP-README.txt.','HARD Assistant',16)
        return 1
    finally:
        if server:server.shutdown();server.server_close();thread.join()
        if handle:
            kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.CloseHandle(handle)

if __name__=='__main__':
    import multiprocessing
    multiprocessing.freeze_support()
    sys.exit(main())
