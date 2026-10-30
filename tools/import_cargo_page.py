#!/usr/bin/env python3
"""Cargo에서 복사한 'NYT 스타일 프로젝트 페이지' HTML을 data/<slug>.json 으로 바꿉니다.

사용법:
    python3 tools/import_cargo_page.py 붙여넣은파일.html <slug>
    예) python3 tools/import_cargo_page.py source/hwamyeong.html hwamyeong

(붙여넣은 HTML 안의 <script>는 무시됩니다.)
"""
import json, re, sys, pathlib

def attrs_of(s):
    return dict(re.findall(r'([\w:-]+)="([^"]*)"', s))

def block(src, cls, start=0):
    """class에 cls가 들어 있는 첫 <div>를 짝이 맞는 </div>까지 잘라 돌려줌"""
    m = re.compile(r'<div class="[^"]*\b' + re.escape(cls) + r'\b[^"]*">').search(src, start)
    if not m:
        return None
    return balanced(src, m.start())

def balanced(src, start):
    depth = 0
    for m in re.finditer(r'<div\b|</div>', src[start:]):
        if m.group(0).startswith('<div'):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return src[start:start + m.end()]
    raise ValueError('닫히지 않은 <div>')

def inner(div):
    return re.sub(r'^<div[^>]*>', '', div, count=1, flags=re.S)[:-len('</div>')]

def slideshow(div):
    m = re.search(r'<gallery-slideshow([^>]*)>(.*?)</gallery-slideshow>', div, re.S)
    if not m:
        return {'images': []}
    sattrs = attrs_of(m.group(1))
    images, nozoom = [], False
    for mm in re.finditer(r'<media-item\b([^>]*)>', m.group(2)):
        a = attrs_of(mm.group(1))
        if 'hash' in a:
            images.append(a['hash'])
            if a.get('disable-zoom') == 'true':
                nozoom = True
    out = {'images': images}
    delay = sattrs.get('autoplay-delay')
    if delay and delay != 'false':
        out['autoplay'] = float(delay)
    if nozoom:
        out['nozoom'] = True
    return out

def parse(src):
    src = re.sub(r'<script>.*?</script>', '', src, flags=re.S)
    d = {}
    lead = block(src, 'nyt-lead')
    d['kicker'] = re.search(r'<span class="nyt-k">(.*?)</span>', lead, re.S).group(1)
    d['title'] = inner(block(lead, 'nyt-h1')).strip()
    d['deck'] = inner(block(lead, 'nyt-deck')).strip()
    d['by'] = inner(block(lead, 'nyt-by')).strip()
    d['lead'] = slideshow(block(lead, 'nyt-ss'))
    sections, cur = [], None
    for m in re.finditer(r'<div class="(nyt-lab(?: nyt-sep)?|nyt-p)">(.*?)</div>', inner(block(lead, 'nyt-text')), re.S):
        if m.group(1).startswith('nyt-lab'):
            cur = {'label': m.group(2).strip(), 'paragraphs': []}
            sections.append(cur)
        else:
            if cur is None:
                cur = {'label': '', 'paragraphs': []}; sections.append(cur)
            cur['paragraphs'].append(m.group(2).strip())
    d['sections'] = sections
    stories, pos = [], 0
    for m in re.finditer(r'<div class="nyt-story">', src):
        b = balanced(src, m.start())
        s = {
            'kicker': re.search(r'<span class="nyt-k">(.*?)</span>', b, re.S).group(1),
            'title': inner(block(b, 'nyt-h2')).strip(),
            'cap': inner(block(b, 'nyt-cap')).strip(),
        }
        s.update(slideshow(b))
        stories.append(s)
    d['stories'] = stories
    notes = block(src, 'nyt-notes')
    if notes:
        paras = []
        for m in re.finditer(r'<div class="nyt-p">(.*?)</div>', notes, re.S):
            t = m.group(1).strip()
            lm = re.match(r'<span class="nyt-lab">(.*?)</span>(.*)', t, re.S)
            paras.append({'label': lm.group(1), 'text': lm.group(2).strip()} if lm else {'label': '', 'text': t})
        d['notes'] = {'kicker': re.search(r'<span class="nyt-k">(.*?)</span>', notes, re.S).group(1), 'paragraphs': paras}
    fig = block(src, 'nyt-fig')
    if fig:
        a = attrs_of(re.search(r'<media-item\b([^>]*)>', fig).group(1))
        d['fig'] = {'hash': a['hash']}
    return d

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    data = parse(pathlib.Path(sys.argv[1]).read_text(encoding='utf-8'))
    out = pathlib.Path(__file__).resolve().parent.parent / 'data' / (sys.argv[2] + '.json')
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    n = len(data['lead']['images']) + sum(len(s['images']) for s in data['stories'])
    print(f'{out.name}: 슬라이드 {len(data["stories"])}개, 이미지 {n}장')
