from pathlib import Path
import html
root=Path(__file__).resolve().parent
source=root/'LBP实验结果与讲解稿.md'
lines=source.read_text(encoding='utf-8-sig').splitlines()
parts=[]
i=0
while i<len(lines):
    line=lines[i]
    if not line.strip():
        i+=1; continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].startswith('|'):
            rows.append([c.strip() for c in lines[i].strip('|').split('|')]); i+=1
        parts.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+html.escape(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>')
        for row in rows[2:]:
            parts.append('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>')
        parts.append('</tbody></table></div>'); continue
    if line.startswith('# '):
        parts.append('<h1>'+html.escape(line[2:])+'</h1>')
    elif line.startswith('## '):
        parts.append('<h2>'+html.escape(line[3:])+'</h2>')
    elif line.startswith('python ') or line.startswith('工作目录：') or line.startswith('数据指纹：'):
        parts.append('<pre>'+html.escape(line)+'</pre>')
    elif line.startswith('问 '):
        parts.append('<p class="question">'+html.escape(line)+'</p>')
    else:
        parts.append('<p>'+html.escape(line)+'</p>')
    i+=1
css='''body{margin:0;background:#f3f5f7;color:#17212b;font-family:"Microsoft YaHei","SimSun",sans-serif;font-size:16px;line-height:1.8}main{max-width:1000px;margin:32px auto;padding:44px 52px;background:white}h1{font-size:30px;color:#000;line-height:1.4;margin:0 0 24px}h2{color:#000;font-size:22px;margin:36px 0 14px;break-after:avoid}p{margin:12px 0}table{border-collapse:collapse;width:100%;font-size:15px;line-height:1.6}td,th{border:1px solid #d9d9d9;padding:10px 12px;vertical-align:middle}th{background:#dce8f2;color:#000}td:not(:first-child){text-align:center}tr:nth-child(even){background:#f8fafc}.table-wrap{margin:18px 0;overflow:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-family:Consolas,"Microsoft YaHei",monospace;background:#f4f5f6;padding:12px;font-size:14px;line-height:1.6}.question{font-weight:bold;margin-top:22px}.toolbar{max-width:1000px;margin:20px auto;text-align:right}button{font-size:16px;padding:10px 18px;border:1px solid #bbc8d5;border-radius:4px;background:white;cursor:pointer}@media(max-width:800px){main{margin:0;padding:22px}body{font-size:15px}}@media print{@page{size:A4;margin:18mm}body{background:white;font-size:10.5pt;line-height:1.6}main{margin:0;padding:0;max-width:none}.toolbar{display:none}h1{font-size:21pt}h2{font-size:14pt;margin-top:20pt}table{font-size:9pt}td,th{padding:6px 8px}tr{break-inside:avoid}thead{display:table-header-group}pre{font-size:9pt}.table-wrap{overflow:visible}}'''
doc='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LBP 人脸识别实验结果与现场讲解</title><style>'+css+'</style></head><body><div class="toolbar"><button onclick="window.print()">打印或保存为 PDF</button></div><main>'+''.join(parts)+'</main></body></html>'
output=root/'LBP实验结果与讲解稿.html'
output.write_text(doc,encoding='utf-8')
assert doc.count('<table>')==4
assert '24.5' in doc and '88.0%' in doc and '0.9826' in doc
print(output)

