"""Package the current reviewable preview without claiming original equivalence."""
from pathlib import Path
import hashlib,json,subprocess,sys,zipfile
root=Path(__file__).resolve().parent.parent
version=json.loads((root/'package.json').read_text())['version']
subprocess.run([sys.executable,str(root/'scripts/build-offline.py')],check=True)
out=root/'dist'
notes=f'''现金流网页游戏 v{version} 测试版

快速开始（无需安装）：
解压后，用 Chrome 或 Edge 打开 cashflow-offline.html。
支持单人及同屏轮流，浏览器保存进度。

不同设备联机：
安装 Node.js 18 或更新版，在本文件所在文件夹打开终端，执行：
node scripts/serve.cjs --host 0.0.0.0 --port 3000
本机访问 http://localhost:3000；其他设备通过本机可访问的 IP 和 3000 端口进入同一服务。
联机房间保存在 .cashflow/rooms.json，请保留该文件。

当前范围：12 职业、182 张机制卡、内外圈、23 个梦想、借还款、股票与房产、
私人联机房间、聊天、存档恢复、专用快车道报表及两种胜利条件。

已知差异：尚未完成全部页面、卡牌文字、美术及特殊分支的一致性核验。
官网黄金出售存在金额差异，本版按 10 单位 × 600 = 6,000 结算。
本包是阶段测试版，不是已验收的完整原版复刻。详见 VERSION.json、audit/README.md。

测试：348 项自动测试和三套浏览器回归通过；解压后的服务启动与联机开局通过。
单文件已在关闭接口的本地 HTTP 测试中验证开局、存档恢复及掷骰；
测试环境的浏览器策略禁止 file://，未验证直接双击 HTML 的入口。
'''
(out/'开始游戏.txt').write_text(notes)
manifest={'version':version,'channel':'preview','complete_original_equivalence':False,'features':['offline_same_device','server_authoritative_rooms','persistent_sessions','fast_track_statement','dream_and_cashflow_victories'],'validation':'audit/validation-latest.json'}
(out/'VERSION.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
files=[p for p in root.iterdir() if p.is_file() and (p.suffix in {'.js','.cjs','.css','.html','.md'} or p.name in {'package.json','.gitignore','reference-manifest.json'})]
for folder in ['scripts','audit']:
 files.extend(p for p in (root/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
package=out/f'cashflow-preview-v{version}.zip'
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(files):z.write(p,p.relative_to(root))
 for name in ['cashflow-offline.html','开始游戏.txt','VERSION.json']:z.write(out/name,name)
sha=hashlib.sha256(package.read_bytes()).hexdigest()
(out/(package.name+'.sha256')).write_text(sha+'  '+package.name+'\n')
print(f'Built {package.name} ({package.stat().st_size} bytes), SHA-256 {sha}')
