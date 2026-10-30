#!/usr/bin/env python3
"""data/*.json 으로 docs/ 안의 모든 페이지(.html)를 다시 만듭니다.

    python3 tools/build.py

옵션(테스트용):  --manifest 이미지주소.json   --out 출력폴더
"""
import argparse, html, json, pathlib, re, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
EMAIL = 'dabisdab7919@gmail.com'
OWNER = 'Dabin Jeong'

# 그래프(메인)에 걸려 있는 프로젝트 순서. 데이터(JSON)가 없으면 '준비 중' 페이지가 만들어집니다.
PROJECTS = [
    ('communicate', 'Communicating House'),
    ('attract', 'Attract Center'),
    ('connect', 'Connect Office'),
    ('art-music', 'Art & Music Village'),
    ('hwamyeong', 'Hwamyeong Farm Therapy'),
    ('rewriting', 'Rewriting the House'),
]

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@800&family=Noto+Serif+KR:wght@400;600&display=swap">')

VIDEO_EXT = ('.mp4', '.webm', '.mov', '.m4v')


def sized(url, w):
    return re.sub(r'/w/\d+/', f'/w/{w}/', url) if re.search(r'/w/\d+/', url) else url


class Site:
    def __init__(self, manifest, out):
        self.out = out
        self.manifest = {}
        if manifest and pathlib.Path(manifest).exists():
            raw = json.loads(pathlib.Path(manifest).read_text(encoding='utf-8'))
            self.manifest = {k: (v['url'] if isinstance(v, dict) else v) for k, v in raw.items()}

    # ---- 이미지 ----
    def base_url(self, h):
        return self.manifest.get(h) or f'https://freight.cargo.site/w/1600/i/{h}/image.jpg'

    def img(self, h, alt, active=False, eager=False, border=False):
        base = self.base_url(h)
        src, full = sized(base, 1200), sized(base, 2400)
        a = [f'src="{html.escape(src)}"']
        if full != src:
            a.append(f'data-full="{html.escape(full)}"')
        a += [f'data-hash="{h}"', f'alt="{html.escape(alt)}"']
        if not (active or eager):
            a.append('loading="lazy"')
        cls = ' '.join(c for c, on in (('is-active', active), ('has-border', border)) if on)
        cls = f' class="{cls}"' if cls else ''
        return f'<img{cls} {" ".join(a)}><span class="ph">{h}</span>'

    def slideshow(self, images, alt, autoplay=None, nozoom=False, wide=False, borders=()):
        cls = 'nyt-ss' + (' nyt-wide' if wide else '') + (' nozoom' if nozoom else '')
        auto = f' data-autoplay="{autoplay:g}"' if autoplay else ''
        slides = ''.join(self.img(h, alt, active=(i == 0), eager=(wide and i < 2), border=(h in borders)) for i, h in enumerate(images))
        zoom = '' if nozoom else '<button class="ss-zoom" type="button" aria-label="이미지 크게 보기"></button>'
        nav = ('<button class="ss-nav ss-prev" type="button" aria-label="이전"><svg viewBox="0 0 24 24"><path d="M15 4l-8 8 8 8"/></svg></button>'
               '<button class="ss-nav ss-next" type="button" aria-label="다음"><svg viewBox="0 0 24 24"><path d="M9 4l8 8-8 8"/></svg></button>'
               '<span class="ss-count"></span>')
        return (f'<div class="{cls}"{auto}><div class="nyt-ss-in"><div class="ss-frame">{slides}{zoom}{nav}</div></div></div>')

    def fig(self, h):
        base = self.base_url(h)
        if base.lower().split('?')[0].endswith(VIDEO_EXT):
            return f'<video src="{html.escape(base)}" controls playsinline preload="metadata"></video>'
        return self.img_plain(h)

    def img_plain(self, h):
        base = self.base_url(h)
        return f'<img src="{html.escape(sized(base, 2000))}" data-hash="{h}" alt="" loading="lazy">'

    # ---- 공통 틀 ----
    def page(self, fname, title, body, desc='', current=''):
        head_cur = lambda name: ' aria-current="page"' if current == name else ''
        doc = f'''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc or 'Dabin Jeong — Architecture portfolio. Value through Connection.')}">
{FONTS}
<link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
<a class="skip" href="#main">본문으로 건너뛰기</a>
<header class="site-head wrap">
  <div class="head-row">
    <a class="head-link" href="index.html">{OWNER}</a>
    <a class="masthead" href="index.html">Value through Connection</a>
    <a class="head-link" href="mailto:{EMAIL}">Mail</a>
  </div>
  <div class="head-row2">
    <a class="head-link" href="info.html"{head_cur('info')}>Info</a>
    <a class="head-link" href="index.html#projects">Architecture portfolio</a>
  </div>
</header>
<main id="main" class="wrap">
{body}
</main>
<footer class="site-foot wrap">
  <span>© {OWNER}</span>
  <a href="mailto:{EMAIL}">{EMAIL}</a>
  <span data-clock>--:--:--</span>
</footer>
<script src="assets/js/site.js" defer></script>
</body>
</html>
'''
        (self.out / fname).write_text(doc, encoding='utf-8')

    # ---- 페이지 종류 ----
    def project(self, slug, d):
        title_plain = re.sub(r'<[^>]+>', '', html.unescape(d['title']))
        lead_alt = title_plain
        text = ''
        for i, sec in enumerate(d['sections']):
            if sec['label']:
                text += f'      <div class="nyt-lab{" nyt-sep" if i else ""}">{sec["label"]}</div>\n'
            for p in sec['paragraphs']:
                text += f'      <div class="nyt-p">{p}</div>\n'
        lead = d['lead']
        text_html = f'<div class="nyt-text">\n{text}      </div>' if d['sections'] else ''
        stories = ''
        for s in d['stories']:
            caps = s.get('slide_caps')
            cap_attr = f' data-caps="{html.escape(json.dumps(caps, ensure_ascii=False), quote=True)}"' if caps else ''
            cap_text = caps[0] if caps else s['cap']
            alt = title_plain + " — " + html.unescape(re.sub(r"<[^>]+>", "", s["kicker"]))
            stories += (f'    <div class="nyt-story">\n      <span class="nyt-k">{s["kicker"]}</span>\n'
                        f'      <div class="nyt-h2">{s["title"]}</div>\n'
                        f'      {self.slideshow(s["images"], alt, autoplay=s.get("autoplay"), nozoom=s.get("nozoom", False), borders=s.get("borders", ()))}\n'
                        f'      <div class="nyt-cap"{cap_attr}>{cap_text}</div>\n    </div>\n')
        deck_html = f'<div class="nyt-deck">{d["deck"]}</div>' if d.get('deck') else ''
        row = 'nyt-row nyt-4' if len(d['stories']) == 4 else 'nyt-row'
        notes = ''
        if d.get('notes'):
            ps = ''
            for p in d['notes']['paragraphs']:
                lab = f'<span class="nyt-lab">{p["label"]}</span>' if p['label'] else ''
                ps += f'      <div class="nyt-p">{lab}{p["text"]}</div>\n'
            notes = f'  <div class="nyt-notes">\n    <span class="nyt-k">{d["notes"]["kicker"]}</span>\n    <div class="nyt-cols">\n{ps}    </div>\n  </div>\n'
        fig = f'  <div class="nyt-fig">{self.fig(d["fig"]["hash"])}</div>\n' if d.get('fig') else ''
        body = f'''<article class="nyt">
  <div class="nyt-lead">
    <span class="nyt-k">{d["kicker"]}</span>
    <h1 class="nyt-h1">{d["title"]}</h1>
    {deck_html}
    <div class="nyt-by">{d["by"]}</div>
    <div class="nyt-lead-grid{" no-text" if not d["sections"] else ""}">
      {self.slideshow(lead["images"], lead_alt, autoplay=lead.get("autoplay"), wide=True)}
      {text_html}
    </div>
  </div>

  <div class="{row}">
{stories}  </div>
{notes}{fig}</article>'''
        self.page(f'{slug}.html', f'{title_plain} — {OWNER}', body, desc=re.sub(r'<[^>]+>', ' ', html.unescape(d['deck'])).strip(), current='')

    def soon(self, slug, name):
        body = f'''<section class="plain">
  <span class="nyt-k">Architecture · Coming soon</span>
  <h1>{html.escape(name)}</h1>
  <p>이 프로젝트 페이지는 곧 채워질 예정입니다.</p>
  <p><a class="mail" href="index.html#projects">← 프로젝트 목록으로</a></p>
</section>'''
        self.page(f'{slug}.html', f'{name} — {OWNER}', body)

    def info(self):
        body = f'''<section class="plain">
  <span class="nyt-k">Info</span>
  <h1>{OWNER}</h1>
  <p>홍익대학교 건축학과 학생입니다. 지금까지 진행한 설계 프로젝트를 “Value through Connection”이라는 주제로 정리한 아카이브입니다.</p>
  <p>연락: <a class="mail" href="mailto:{EMAIL}">{EMAIL}</a></p>
</section>'''
        self.page('info.html', f'Info — {OWNER}', body, current='info')

    def index(self):
        graph = (ROOT / 'docs' / 'partials' / 'graph.html').read_text(encoding='utf-8')
        body = f'''<section class="hero" aria-label="Value through Connection">
  <video autoplay muted loop playsinline preload="auto" disablepictureinpicture aria-hidden="true">
    <source src="assets/video/hero.mp4" type="video/mp4">
  </video>
  <div class="hero-text">
    <p class="vtc">Value through Connection:<br><br>An architectural archive <span class="vc-u">reinterpreted</span> through the lens of <span class="vc-u">valuation</span>—where design logic meets the <span class="vc-u">quantifiable worth</span> of space.</p>
  </div>
</section>
<section class="graph" id="projects" aria-label="Projects">
{graph}
</section>'''
        self.page('index.html', f'{OWNER} — Value through Connection', body)

    def build(self):
        self.out.mkdir(parents=True, exist_ok=True)
        self.index()
        self.info()
        made = []
        for slug, name in PROJECTS:
            f = ROOT / 'data' / f'{slug}.json'
            if f.exists():
                self.project(slug, json.loads(f.read_text(encoding='utf-8')))
                made.append(slug)
            else:
                self.soon(slug, name)
        return made


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default=str(ROOT / 'data' / 'images.json'))
    ap.add_argument('--out', default=str(ROOT / 'docs'))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    if out.resolve() != (ROOT / 'docs').resolve():          # 테스트 출력: 자산 복사
        shutil.copytree(ROOT / 'docs' / 'assets', out / 'assets', dirs_exist_ok=True)
    made = Site(a.manifest, out).build()
    print('만든 페이지:', ', '.join(['index', 'info'] + made), '| 준비 중:', ', '.join(s for s, _ in PROJECTS if s not in made) or '없음')
