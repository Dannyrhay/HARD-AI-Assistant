import unittest,tempfile,io,base64
from pathlib import Path
from unittest.mock import patch,Mock
from PIL import Image
from pypdf import PdfWriter
from docx import Document
from hard_core import Workspace,UserError
from hard_preview import preview
class PreviewConversionTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.w=Workspace(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def pdf(self):
  stream=io.BytesIO();p=PdfWriter();p.add_blank_page(width=100,height=100);p.write(stream);return self.w.import_document('source.pdf',stream.getvalue())
 def test_image_normalized_and_no_network(self):
  stream=io.BytesIO();Image.new('RGB',(40,30),'red').save(stream,format='PNG')
  result=preview(self.w,{'name':'image.png','data':base64.b64encode(stream.getvalue()).decode()})
  self.assertEqual(result['images'][0]['mime'],'image/jpeg');self.assertTrue(result['images'][0]['data'])
 def test_text_preview_is_data(self):
  d=self.w.import_document('note.txt',b'<script>alert(1)</script>')
  self.assertEqual(preview(self.w,{'document_id':d['id']})['text'],'<script>alert(1)</script>')
 def test_pdf_preview(self):
  d=self.pdf();result=preview(self.w,{'document_id':d['id']});self.assertEqual(len(result['images']),1)
 def test_invalid_preview(self):
  for name in ['bad.html','bad.png','bad.pdf']:
   with self.assertRaises(UserError):preview(self.w,{'name':name,'data':'YQ=='})
 def test_scanned_pdf_does_not_make_empty_word(self):
  d=self.pdf()
  with self.assertRaisesRegex(UserError,'OCR'):self.w.convert_to(d['id'],'docx')
 def test_pdf_to_word_separate_unapproved_copy(self):
  d=self.pdf();original=self.w.path(d['id']).read_bytes()
  with patch('hard_core.PdfReader',return_value=Mock(pages=[Mock(extract_text=lambda:'Project proposal\nWater supply')])):
   converted=self.w.convert_to(d['id'],'docx')
  self.assertIn('Water supply',converted['content']);self.assertFalse(converted['reviewed']);self.assertEqual(self.w.path(d['id']).read_bytes(),original)
 def test_direct_word_conversion_keeps_review_workflow(self):
  stream=io.BytesIO();doc=Document();doc.add_paragraph('Project proposal');doc.save(stream);d=self.w.import_document('test.docx',stream.getvalue())
  with self.assertRaisesRegex(UserError,'Approve'):self.w.convert(d['id'])
  with patch.object(self.w,'convert',return_value={'id':'result'}) as convert:
   self.w.convert_to(d['id'],'pdf');convert.assert_called_once_with(d['id'],require_review=False)
