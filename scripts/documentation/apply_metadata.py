"""Normalize document control metadata without destroying Excel formula caches."""
from pathlib import Path
import zipfile,xml.etree.ElementTree as ET,datetime,io,sys
import fitz
ROOT=Path(__file__).resolve().parents[2]/'docs/professional-delivery'
ns={'cp':'http://schemas.openxmlformats.org/package/2006/metadata/core-properties','dc':'http://purl.org/dc/elements/1.1/','dcterms':'http://purl.org/dc/terms/','xsi':'http://www.w3.org/2001/XMLSchema-instance'}
for prefix,uri in ns.items():ET.register_namespace(prefix,uri)
paths=[Path(x) for x in sys.argv[1:]] if len(sys.argv)>1 else list(ROOT.rglob('*'))
now=datetime.datetime.now(datetime.timezone.utc);stamp=now.strftime('%Y-%m-%dT%H:%M:%SZ')
for p in paths:
 if p.suffix in ['.docx','.xlsx','.pptx']:
  stream=io.BytesIO()
  with zipfile.ZipFile(p) as original,zipfile.ZipFile(stream,'w') as updated:
   for info in original.infolist():
    data=original.read(info.filename)
    if info.filename=='docProps/core.xml':
     xml=ET.fromstring(data)
     for tag,value in [('dc:title',p.stem),('dc:subject','Cashflow v0.6.4 development review draft'),('dc:creator','Cashflow documentation pipeline'),('cp:lastModifiedBy','Automated documentation review; not approval'),('dc:description','Review baseline; approvals and UAT remain unsigned.'),('cp:revision','1'),('dcterms:created',stamp),('dcterms:modified',stamp)]:
      prefix,name=tag.split(':');qualified='{'+ns[prefix]+'}'+name;node=xml.find(qualified)
      if node is None:node=ET.SubElement(xml,qualified)
      node.text=value
      if prefix=='dcterms':node.set('{'+ns['xsi']+'}type','dcterms:W3CDTF')
     data=ET.tostring(xml,encoding='utf-8',xml_declaration=True)
    updated.writestr(info,data)
  p.write_bytes(stream.getvalue())
 elif p.suffix=='.pdf':
  with fitz.open(p) as pdf:
   meta=pdf.metadata;meta.update(title=p.stem,author='Cashflow documentation pipeline',subject='Review draft / v0.6.4 / no approvals implied');pdf.set_metadata(meta);pdf.saveIncr()
print('Normalized Office/PDF control metadata; Excel XML formulas and cached values retained.')
