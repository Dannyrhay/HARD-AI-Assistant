"""Local, bounded attachment previews. No external requests."""
import base64,io
from pathlib import Path
from hard_core import UserError,extract,safe_name
from hard_chat import image_part,MAX_BYTES
import pypdfium2 as pdfium

def preview(workspace,item):
    if item.get('document_id'):
        doc=workspace.document(item['document_id']);name=doc['name'];raw=workspace.path(doc['id']).read_bytes()
    else:
        name=safe_name(item.get('name'))
        try:raw=base64.b64decode(item.get('data',''),validate=True)
        except (ValueError,TypeError):raise UserError('The attachment could not be read.') from None
    if len(raw)>MAX_BYTES:raise UserError('Preview supports files up to 12 MB.')
    suffix=Path(name).suffix.lower();result={'name':name,'images':[],'text':'','note':''}
    if suffix in {'.png','.jpg','.jpeg','.webp'}:
        result['images']=[image_part(raw)]
    elif suffix=='.pdf':
        try:
            with pdfium.PdfDocument(raw) as pdf:
                result['note']=f'Preview of the first {min(3,len(pdf))} of {len(pdf)} pages.'
                for i in range(min(3,len(pdf))):
                    page=pdf[i];w,h=page.get_size();bitmap=page.render(scale=min(1.5,1000/max(w,h)))
                    try:
                        out=io.BytesIO();bitmap.to_pil().convert('RGB').save(out,format='JPEG',quality=80)
                        result['images'].append({'mime':'image/jpeg','data':base64.b64encode(out.getvalue()).decode()})
                    finally:bitmap.close();page.close()
        except Exception:raise UserError('This PDF could not be previewed. It may be damaged or password protected.') from None
    elif suffix in {'.docx','.txt'}:
        content,_=extract(raw,suffix);result['text']=content[:18000];result['note']='Text preview; original formatting is not reproduced.'+(' Showing the first 18,000 characters.' if len(content)>18000 else '')
    else:raise UserError('Preview supports Word, PDF, text and PNG/JPEG/WebP images.')
    return result
