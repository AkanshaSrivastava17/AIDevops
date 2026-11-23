import subprocess
import os

browsers = [
    (r'C:\Program Files\Google\Chrome\Application\chrome.exe', 'Chrome'),
    (r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', 'Edge')
]

test_html = r'e:\aidevops prj\project\paper\test.html'
test_pdf = r'e:\aidevops prj\project\paper\test.pdf'

with open(test_html, 'w', encoding='utf-8') as f:
    f.write('''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Test</title></head>
<body><h1>History-RAG Test</h1></body>
</html>''')

for path, name in browsers:
    if os.path.exists(path):
        if os.path.exists(test_pdf):
            try:
                os.remove(test_pdf)
            except:
                pass
        cmd = [
            path,
            '--headless',
            '--no-sandbox',
            '--disable-gpu',
            '--disable-software-rasterizer',
            f'--print-to-pdf={test_pdf}',
            test_html
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            print(f'{name} return code: {res.returncode}')
            print(f'{name} PDF generated: {os.path.exists(test_pdf)}')
            if os.path.exists(test_pdf):
                print(f'{name} PDF size: {os.path.getsize(test_pdf)} bytes')
        except Exception as e:
            print(f'{name} error: {e}')

if os.path.exists(test_pdf):
    os.remove(test_pdf)
if os.path.exists(test_html):
    os.remove(test_html)
