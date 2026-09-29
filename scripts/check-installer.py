"""Exercise staged installation and failed-update rollback without touching the real installation."""
import os,shutil,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='hard-installer-test-') as tmp:
 base=Path(tmp);package=base/'package';package.mkdir()
 shutil.copytree(root/'release'/'HARD Assistant',package/'HARD Assistant')
 shutil.copy2(root/'Install-HARD.ps1',package/'Install-HARD.ps1')
 local=base/'local';data=local/'HARD Assistant'/'Data';data.mkdir(parents=True);(data/'sentinel.txt').write_text('Keep my workspace')
 env={**os.environ,'LOCALAPPDATA':str(local)}
 def install():return subprocess.run(['powershell.exe','-NoProfile','-File',str(package/'Install-HARD.ps1'),'-SkipShortcuts','-NonInteractive'],env=env,capture_output=True,text=True,timeout=120)
 r=install();assert r.returncode==0,r.stderr
 installed=local/'Programs'/'HARD Assistant'/'HARD Assistant.exe';original=installed.read_bytes()
 # A package that cannot start must restore the preceding application.
 (package/'HARD Assistant'/'HARD Assistant.exe').write_bytes(b'Invalid executable for rollback test')
 r=install();assert r.returncode!=0,'Broken update unexpectedly succeeded'
 assert installed.read_bytes()==original,'Previous executable was not restored'
 assert (data/'sentinel.txt').read_text()=='Keep my workspace'
 print('Installer fresh install, invalid-update rollback and workspace preservation passed.')
