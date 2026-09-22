"""Public OpenRouter catalog: no keys, messages or attachments are sent."""
import json,threading,time,re
from hard_ai import Request,urlopen
from hard_core import UserError
URL='https://openrouter.ai/api/v1/models'
class ModelCatalog:
 def __init__(self):self.rows=[];self.loaded=0;self.lock=threading.Lock()
 def list(self,refresh=False):
  with self.lock:
   if self.rows and not refresh and time.time()-self.loaded<900:return {'models':self.rows,'cached':True,'stale':False}
   try:
    with urlopen(Request(URL,headers={'Accept':'application/json'}),timeout=20) as r:raw=r.read(6000001)
    if len(raw)>6000000:raise ValueError()
    data=json.loads(raw)['data']
    if not isinstance(data,list):raise ValueError()
    rows={}
    for m in data[:10000]:
     if not isinstance(m,dict):continue
     ident=m.get('id','');arch=m.get('architecture') or {};outputs=arch.get('output_modalities',[])
     if not isinstance(ident,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:@-]{0,149}',ident) or 'text' not in outputs:continue
     pricing=m.get('pricing') or {}
     rows[ident]={'id':ident,'name':str(m.get('name') or ident)[:200],'vision':'image' in arch.get('input_modalities',[]),'free':str(pricing.get('prompt'))=='0' and str(pricing.get('completion'))=='0'}
    if not rows:raise ValueError()
    self.rows=sorted(rows.values(),key=lambda x:x['name'].lower());self.loaded=time.time()
    return {'models':self.rows,'cached':False,'stale':False}
   except Exception:
    if self.rows:return {'models':self.rows,'cached':True,'stale':True}
    raise UserError('OpenRouter models could not be loaded. Check your internet connection and try again. Your current model is unchanged; you can still enter a model ID manually.') from None
