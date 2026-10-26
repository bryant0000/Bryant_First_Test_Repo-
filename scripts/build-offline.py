"""Produce a self-contained offline HTML and a downloadable ZIP, no dependencies."""
from pathlib import Path
import re,zipfile,base64,json,argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);options=parser.parse_args()
root=Path(__file__).resolve().parent.parent
version=json.loads((root/'package.json').read_text())['version']
html=(root/'index.html').read_text().replace('<html lang="zh-CN">','<html lang="zh-CN" data-standalone="true">')
css=(root/'style.css').read_text()+'\n'+(root/'classic-stage.css').read_text()
html=html.replace('<link rel="stylesheet" href="classic-stage.css">','')
font=root/'assets/reference/GrantAvenue-Regular.otf'
if font.exists():css=css.replace('assets/reference/GrantAvenue-Regular.otf','data:font/otf;base64,'+base64.b64encode(font.read_bytes()).decode())
html=html.replace('<link rel="stylesheet" href="style.css">','<style>\n'+css+'\n</style>')
for name in ['reference-data.js','reference-layout-data.js','reference-art-data.js','engine.js','table.js','local-rooms.js','app.js','online.js','interaction.js','reference-ui.js','reference-art.js','classic-stage.js','scene-canvas.js','classic-log.js']:
 source=(root/name).read_text()
 if name=='reference-art-data.js':
  for asset in (root/'assets/reference').glob('*.png'):
   source=source.replace(str(asset.relative_to(root)),'data:image/png;base64,'+base64.b64encode(asset.read_bytes()).decode())
 source=re.sub(r'</script',r'<\\/script',source,flags=re.I)
 html=html.replace(f'<script src="{name}"></script>','<script>\n'+source+'\n</script>')
# Contextual explanations are visible even when this file is opened from the ZIP.
html=html.replace('href="SOURCES.md"','href="https://github.com/dadish/cashflow/tree/2edcdbc15785ac2141f3d1fe544b14e0de2775b4/src/assets/data"')
output=options.output or root/'dist';output.mkdir(parents=True,exist_ok=True)
(output/'cashflow-offline.html').write_text(html)
instructions=f'现金流网页游戏 v{version} 测试版（尚未完成原版一致性验收）\n\n先解压压缩包，然后用 Chrome、Edge 或 Firefox 打开 cashflow-offline.html。\n不需要安装 Node.js、Python 或依赖，也不需要在聊天的可视化面板内打开。\n浏览器若禁止本地文件存储，游戏仍可运行，但无法跨刷新保留存档。\n离线文件仅支持单人／同屏轮流；不同设备联机需要完整版中的 Node.js 服务。角色、卡牌及版本差异见 SOURCES.md。\n'
(output/'打开游戏.txt').write_text(instructions)
with zipfile.ZipFile(output/'cashflow-offline.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
 for name in ['cashflow-offline.html','打开游戏.txt']:z.write(output/name,name)
 z.write(root/'SOURCES.md','SOURCES.md')
print('Built',output/'cashflow-offline.html','and',output/'cashflow-offline.zip')
