"""
md_to_pdf.py — Render report/report.md to a print-styled HTML page and print it to PDF with headless
Google Chrome (same source as the Word version built by md_to_docx.py).

Usage: python src/md_to_pdf.py report/report.md report/Report.pdf
"""
import base64, os, re, subprocess, sys, tempfile
import markdown

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src, dst = sys.argv[1], os.path.abspath(sys.argv[2])
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

text = open(src, encoding='utf-8').read()

# images: ![caption](path){width=6.3} -> embedded <figure>
def fig(m):
    cap, path, width = m.group(1), m.group(2), m.group(4)
    full = path if os.path.isabs(path) else os.path.join(ROOT, path)
    if not os.path.exists(full):
        return ''
    b64 = base64.b64encode(open(full, 'rb').read()).decode()
    w = f'{min(100, float(width) / 6.5 * 100):.0f}%' if width else '100%'
    return f'\n<figure><img src="data:image/png;base64,{b64}" style="width:{w}"><figcaption>{cap}</figcaption></figure>\n'
text = re.sub(r'^!\[(.*?)\]\((.*?)\)(\{width=([\d.]+)\})?\s*$', fig, text, flags=re.M)
# '---' on its own line = page break (as in the Word builder)
text = re.sub(r'^---\s*$', '\n<div class="pb"></div>\n', text, flags=re.M)
# table captions ("Table N. ...") get their own style
text = re.sub(r'^(Table \d+\..*)$', r'<p class="tcap">\1</p>', text, flags=re.M)

body = markdown.markdown(text, extensions=['tables', 'sane_lists'])
css = """
@page { size: Letter; margin: 0.7in 0.8in; }
body { font-family: Calibri, 'Helvetica Neue', Arial, sans-serif; font-size: 10pt; line-height: 1.3; color: #1a1a1a; }
h1 { font-size: 17pt; color: #1f3a5f; margin: 0 0 6pt; }
h2 { font-size: 13pt; color: #1f3a5f; margin: 16pt 0 5pt; border-bottom: 1px solid #c9d3e0; padding-bottom: 2pt; }
h3 { font-size: 11.5pt; color: #1f3a5f; margin: 12pt 0 4pt; }
h2, h3 { page-break-after: avoid; }
p { margin: 0 0 6pt; text-align: justify; }
li { margin-bottom: 3pt; }
table { border-collapse: collapse; width: 100%; font-size: 8.6pt; margin: 6pt 0 2pt; page-break-inside: avoid; }
th, td { border: 1px solid #b7c4d6; padding: 2.5pt 4pt; text-align: left; vertical-align: top; }
th { background: #dce6f1; }
td:first-child { white-space: nowrap; }
tr:nth-child(even) td { background: #f5f8fc; }
.tcap { font-size: 9pt; font-style: italic; color: #444; margin-bottom: 10pt; text-align: left; }
figure { margin: 6pt 0; text-align: center; page-break-inside: avoid; }
figure img { max-width: 100%; }
figcaption { font-size: 9pt; font-style: italic; color: #444; margin-top: 3pt; }
blockquote { margin: 6pt 0 6pt 18pt; color: #444; font-size: 9.5pt; }
code { font-family: Menlo, Consolas, monospace; font-size: 8.8pt; background: #f2f2f2; padding: 0 2px; }
.pb { page-break-after: always; }
"""
html = f'<!doctype html><html><head><meta charset="utf-8"><title>Report</title><style>{css}</style></head><body>{body}</body></html>'
with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
    f.write(html); tmp = f.name
subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={dst}', f'file://{tmp}'],
               check=True, capture_output=True, timeout=180)
os.remove(tmp)
print('saved', dst)
