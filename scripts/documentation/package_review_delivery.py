"""Package the completely checked native documentation, with per-file hashes."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/professional-delivery'
audit=json.loads((OUT/'10-专家审核与修订/本轮综合复核结果.json').read_text())
assert audit['passed'] is True and audit['product_release_approved'] is False
manifest=OUT/'00-阅读入口与复核/文件校验清单.json'
files=sorted(p for p in OUT.rglob('*') if p.is_file())
assert not any(p.suffix=='.md' for p in files)
data={'date':'2026-11-02','scope':'审核修订文档包全部文件；清单本身排除以避免循环哈希','excluded_self':str(manifest.relative_to(OUT)),'files':[{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files if p!=manifest]}
manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2))
dest=ROOT/'docs/cashflow-reviewed-docs-v0.6.4-2026-11-02.zip'
with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:
        info=zipfile.ZipInfo(str(p.relative_to(OUT)),date_time=(2026,11,2,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
        z.writestr(info,p.read_bytes())
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(files)
    for f in data['files']:
        b=z.read(f['path']);assert len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256']
    assert set(z.namelist())=={f['path'] for f in data['files']}|{data['excluded_self']}
digest=hashlib.sha256(dest.read_bytes()).hexdigest()
dest.with_suffix('.zip.sha256').write_text(digest+'  '+dest.name+'\n')
print(json.dumps({'archive':str(dest),'files':len(files),'bytes':dest.stat().st_size,'sha256':digest,'verified':True},ensure_ascii=False))
