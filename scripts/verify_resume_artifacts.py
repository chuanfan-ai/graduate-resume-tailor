#!/usr/bin/env python3
import argparse
import json
import re
import os
from html.parser import HTMLParser
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

BAD_TERMS = ['求职说明', '投递关键词', '匹配策略', '匹配：', 'JD 反推', 'ATS', '缺口分析', '建议补充', '不虚构', '目前缺少', 'CONTACT']

class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {'style', 'script'}:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in {'style', 'script'} and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            data = data.strip()
            if data:
                self.parts.append(data)


def norm(text):
    text = re.sub(r'\s+', '', str(text or ''))
    return text.replace('→', '->').replace('|', '｜').replace('&gt;', '>')


def html_text(path):
    parser = VisibleHTML()
    parser.feed(Path(path).read_text(encoding='utf-8'))
    return '\n'.join(parser.parts)


def docx_text(path):
    with ZipFile(path) as zf:
        root = ET.fromstring(zf.read('word/document.xml'))
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    return '\n'.join(node.text or '' for node in root.findall('.//w:t', ns))


def pdf_text(path):
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise SystemExit(f'pypdf unavailable: {exc}')
    reader = PdfReader(str(path))
    return '\n'.join(page.extract_text() or '' for page in reader.pages)


def pdf_page_count(path):
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise SystemExit(f'pypdf unavailable: {exc}')
    return len(PdfReader(str(path)).pages)


def expected_fragments(data):
    out = []
    basics = data.get('basics', {})
    target = data.get('target', {})
    out.extend([basics.get('name'), basics.get('phone'), basics.get('email'), basics.get('location')])
    out.extend([target.get('role') or basics.get('title'), target.get('company'), target.get('industry')])
    out.extend(data.get('summary') or [])
    for section in data.get('sections') or []:
        out.append(section.get('title'))
        for item in section.get('items') or []:
            out.append(item.get('heading'))
            if item.get('meta'):
                out.append(str(item['meta']).replace('→', '->'))
            out.extend(item.get('bullets') or [])
    out.extend(data.get('keywords') or [])
    out.append('联系方式')
    return [x for x in out if x]


def main():
    parser = argparse.ArgumentParser(description='Verify generated resume HTML/DOCX/PDF consistency.')
    parser.add_argument('resume_json')
    parser.add_argument('--out-dir', required=True)
    parser.add_argument('--formats', default='html,docx,pdf', help='Comma-separated formats to verify.')
    parser.add_argument('--strict-pdf-text', action='store_true', help='Require every JSON fragment to be extractable from the PDF text layer.')
    parser.add_argument('--mtime-window', type=float, default=120.0, help='Maximum allowed modification time drift across artifacts in seconds.')
    args = parser.parse_args()

    data = json.loads(Path(args.resume_json).read_text(encoding='utf-8'))
    basics = data.get('basics', {})
    target = data.get('target', {})
    stem = '-'.join(x for x in [basics.get('name'), target.get('role') or basics.get('title'), '简历'] if x)
    out_dir = Path(args.out_dir)
    requested = {x.strip().lower() for x in args.formats.split(',') if x.strip()}
    paths_all = {
        'html': out_dir / f'{stem}.html',
        'docx': out_dir / f'{stem}.docx',
        'pdf': out_dir / f'{stem}.pdf',
    }
    paths = {fmt: path for fmt, path in paths_all.items() if fmt in requested}
    missing_files = [str(p) for p in paths.values() if not p.exists()]
    if missing_files:
        raise SystemExit('missing files: ' + ', '.join(missing_files))

    mtimes = {fmt: path.stat().st_mtime for fmt, path in paths.items()}
    drift = max(mtimes.values()) - min(mtimes.values())
    if drift > args.mtime_window:
        stamps = ', '.join(f'{fmt}={mtimes[fmt]:.0f}' for fmt in sorted(mtimes))
        raise SystemExit(f'artifact modification times drift too much: {drift:.1f}s ({stamps})')

    texts = {}
    if 'html' in paths:
        texts['html'] = html_text(paths['html'])
    if 'docx' in paths:
        texts['docx'] = docx_text(paths['docx'])
    if 'pdf' in paths:
        texts['pdf'] = pdf_text(paths['pdf'])
    fragments = expected_fragments(data)
    failed = False
    for fmt, text in texts.items():
        ntext = norm(text)
        missing = [frag for frag in fragments if norm(frag) not in ntext]
        bad = [term for term in BAD_TERMS if term in text]
        print(f'{fmt}: chars={len(text)} missing={len(missing)} bad={bad}')
        if fmt == 'pdf' and missing and not args.strict_pdf_text:
            basics_ok = norm(basics.get('name')) in ntext and (not basics.get('phone') or norm(basics.get('phone')) in ntext)
            pages = pdf_page_count(paths['pdf'])
            if not basics_ok or pages < 1:
                failed = True
                print('  missing sample:', '; '.join(missing[:8]))
            else:
                print(f'  note: PDF text extraction is loose; visual PDF has {pages} page(s), basic identity fields are readable.')
        elif missing:
            failed = True
            print('  missing sample:', '; '.join(missing[:8]))
        if bad:
            failed = True
    if failed:
        raise SystemExit(1)
    print(f'OK: resume artifacts are text-consistent. mtime_drift={drift:.1f}s')


if __name__ == '__main__':
    main()
