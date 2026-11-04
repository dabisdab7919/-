#!/usr/bin/env python3
"""data/*.json 으로 docs/ 안의 모든 페이지(.html)를 다시 만듭니다.

    python3 tools/build.py

옵션(테스트용):  --manifest 이미지주소.json   --out 출력폴더
"""
import argparse, html, json, pathlib, re, shutil, urllib.parse

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
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;600&display=swap">')

VIDEO_EXT = ('.mp4', '.webm', '.mov', '.m4v')
PHOTO_EXT = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif')


def natural(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', name)]


def folder_key(kicker):
    """'Research & Diagram' -> 'research-diagram'"""
    plain = html.unescape(re.sub(r'<[^>]+>', '', kicker)).lower()
    return re.sub(r'[^a-z0-9]+', '-', plain).strip('-')


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
    def photos(self, slug, key):
        """docs/photos/<프로젝트>/<칸>/ 안의 사진을 파일 이름 순서로 돌려줌"""
        d = ROOT / 'docs' / 'photos' / slug / key
        if not d.is_dir():
            return []
        files = sorted((p for p in d.iterdir() if p.is_file() and p.suffix.lower() in PHOTO_EXT), key=lambda p: natural(p.name))
        if files:
            print(f'  사진 {len(files)}장: photos/{slug}/{key}/')
        return [f'photos/{slug}/{key}/{p.name}' for p in files]

    def base_url(self, h):
        return self.manifest.get(h) or f'https://freight.cargo.site/w/1600/i/{h}/image.jpg'

    def img(self, h, alt, active=False, eager=False, border=False):
        local = '/' in h                                   # 'photos/...' 처럼 폴더 경로면 내 사진
        if local:
            src = full = urllib.parse.quote(h)
            label = h.rsplit('/', 1)[-1]
        else:
            base = self.base_url(h)
            src, full = sized(base, 1200), sized(base, 2400)
            label = h
        a = [f'src="{html.escape(src)}"']
        if full != src:
            a.append(f'data-full="{html.escape(full)}"')
        a += [f'data-hash="{html.escape(label)}"', f'alt="{html.escape(alt)}"']
        if not (active or eager):
            a.append('loading="lazy"')
        cls = ' '.join(c for c, on in (('is-active', active), ('has-border', border)) if on)
        cls = f' class="{cls}"' if cls else ''
        return f'<img{cls} {" ".join(a)}><span class="ph">{html.escape(label)}</span>'

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

    def youtube(self, vid, title):
        """유튜브 영상: 썸네일 + 재생 버튼을 먼저 보여주고, 누르면 영상으로 바뀝니다."""
        t = html.escape(title, quote=True)
        return (f'<div class="nyt-yt" data-yt="{vid}"><img src="https://i.ytimg.com/vi/{vid}/maxresdefault.jpg" alt="{t}" loading="lazy">'
                f'<button type="button" class="yt-play" aria-label="영상 재생: {t}"><svg viewBox="0 0 68 48" aria-hidden="true"><path d="M66.5 7.7a8.5 8.5 0 0 0-6-6C55.2.2 34 .2 34 .2S12.8.2 7.5 1.7a8.5 8.5 0 0 0-6 6C0 13 0 24 0 24s0 11 1.5 16.3a8.5 8.5 0 0 0 6 6C12.8 47.8 34 47.8 34 47.8s21.2 0 26.5-1.5a8.5 8.5 0 0 0 6-6C68 35 68 24 68 24s0-11-1.5-16.3z" fill="#f00"/><path d="M45 24 27 14v20z" fill="#fff"/></svg></button></div>'
                f'<div class="nyt-cap"><a class="yt-link" href="https://youtu.be/{vid}" target="_blank" rel="noopener">YouTube에서 보기 \u2197</a></div>')

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
    <span class="head-link">2026</span>
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
            imgs = self.photos(slug, folder_key(s["kicker"])) or s["images"]
            summary = f'      <p class="nyt-sum">{s["summary"]}</p>\n' if s.get('summary') else ''
            stories += (f'    <div class="nyt-story">\n      <span class="nyt-k">{s["kicker"]}</span>\n'
                        f'      <div class="nyt-h2">{s["title"]}</div>\n'
                        f'      {self.slideshow(imgs, alt, autoplay=s.get("autoplay"), nozoom=s.get("nozoom", False), borders=s.get("borders", ()))}\n'
                        f'      <div class="nyt-cap"{cap_attr}>{cap_text}</div>\n{summary}    </div>\n')
        deck_html = f'<div class="nyt-deck">{d["deck"]}</div>' if d.get('deck') else ''
        row = 'nyt-row nyt-4' if len(d['stories']) == 4 else 'nyt-row'
        notes = ''
        if d.get('notes'):
            ps = ''
            for p in d['notes']['paragraphs']:
                lab = f'<span class="nyt-lab">{p["label"]}</span>' if p['label'] else ''
                ps += f'      <div class="nyt-p">{lab}{p["text"]}</div>\n'
            notes = f'  <div class="nyt-notes">\n    <span class="nyt-k">{d["notes"]["kicker"]}</span>\n    <div class="nyt-cols">\n{ps}    </div>\n  </div>\n'
        fig = (f'  <div class="nyt-fig">{self.youtube(d["fig"]["youtube"], d["title"])}</div>\n' if d.get('fig', {}).get('youtube')
               else f'  <div class="nyt-fig">{self.fig(d["fig"]["hash"])}</div>\n' if d.get('fig') else '')
        body = f'''<article class="nyt">
  <div class="nyt-lead">
    <span class="nyt-k">{d["kicker"]}</span>
    <h1 class="nyt-h1">{d["title"]}</h1>
    {deck_html}
    <div class="nyt-by">{d["by"]}</div>
    <div class="nyt-lead-grid{" no-text" if not d["sections"] else ""}">
      {self.slideshow(self.photos(slug, "lead") or lead["images"], lead_alt, autoplay=lead.get("autoplay"), wide=True)}
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
        f = ROOT / 'data' / 'info.json'
        d = json.loads(f.read_text(encoding='utf-8')) if f.exists() else {'title': OWNER, 'paragraphs': []}
        paras = ''.join(f'  <p>{p}</p>\n' for p in d.get('paragraphs', []))
        body = f'''<section class="plain">
  <span class="nyt-k">{d.get("kicker", "Info")}</span>
  <h1>{d.get("title", OWNER)}</h1>
{paras}  <p>연락: <a class="mail" href="mailto:{EMAIL}">{EMAIL}</a></p>
</section>'''
        self.page('info.html', f'Info — {OWNER}', body, current='info')

    def graph(self):
        """메인 그래프: 프로젝트 6개를 잇는 신문 차트 스타일. 점에 마우스를 올리면 value creation 막대, 가치 단어, 프로젝트 유형이 나타납니다."""
        W, H, L, R, T, B = 1000, 460, 70, 970, 40, 390
        k = (B - T - 40) / 355                              # 기존 그래프(높이 355 = 최고점)를 이 차트 크기로 줄이는 비율
        # (학기, 점 높이, value creation 막대 높이, 가치 단어, 프로젝트 유형) — 기존 Cargo 그래프의 값
        DATA = [('2 \u2013 1', 139, 48.95, 'Trend', 'Residence'),
                ('2 \u2013 2', 189, 82.77, 'Attraction', 'Community Service Center'),
                ('3 \u2013 1', 355, 99.69, 'Synergy', 'Office'),
                ('3 \u2013 2', 289, 132.62, 'Cluster', 'Cultural Center'),
                ('4 \u2013 1', 223, 181.57, 'Commons', 'School Renovation'),
                ('Graduation', 239, 214.5, 'Sustainability', 'Senior-Residence')]
        step = (R - L) / len(PROJECTS)
        pts = [(L + (i + .5) * step, B - d[1] * k) for i, d in enumerate(DATA)]
        line = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
        grid = ''.join(f'<line class="g-grid" x1="{L}" x2="{R}" y1="{T + j * (B - T) / 5:.1f}" y2="{T + j * (B - T) / 5:.1f}"/>' for j in range(5))
        stems = ''.join(f'<line class="g-stem" x1="{x:.1f}" x2="{x:.1f}" y1="{y:.1f}" y2="{B}"/>' for x, y in pts)
        ticks = ''.join(f'<line class="g-tk" x1="{x:.1f}" x2="{x:.1f}" y1="{B}" y2="{B + 6}"/><text class="g-x" x="{x:.1f}" y="{B + 26}" text-anchor="middle">{d[0]}</text>'
                        for (x, y), d in zip(pts, DATA))
        dots = ''
        for i, ((x, y), d, (slug, name)) in enumerate(zip(pts, DATA, PROJECTS)):
            bh = d[2] * k
            dots += (f'<a href="{slug}.html" class="g-dot" aria-label="{html.escape(name)} \u2014 {d[3]}, {d[4]}"><title>{html.escape(name)}</title>'
                     f'<g class="g-bar"><rect x="{x - 8:.1f}" y="{y - bh / 2:.1f}" width="16" height="{bh:.1f}" fill="url(#g-grad)"/>'
                     f'<text class="g-v" x="{x:.1f}" y="{y - bh / 2 - 9:.1f}" text-anchor="middle">{d[3]}</text>'
                     f'<text class="g-k" x="{x:.1f}" y="{y + bh / 2 + 18:.1f}" text-anchor="middle">{d[4]}</text></g>'
                     f'<circle class="g-hit" cx="{x:.1f}" cy="{y:.1f}" r="28"/><circle class="g-c" cx="{x:.1f}" cy="{y:.1f}" r="5.5"/></a>')
        defs = ('<defs><radialGradient id="g-grad" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#190c09"/><stop offset="1" stop-color="#ededed"/></radialGradient>'
                '<linearGradient id="g-leg"><stop offset="0" stop-color="#ededed"/><stop offset=".5" stop-color="#190c09"/><stop offset="1" stop-color="#ededed"/></linearGradient></defs>')
        legend = (f'<g class="g-leg"><rect x="{L + 14}" y="{T + 10}" width="96" height="14" fill="url(#g-leg)"/>'
                  f'<text x="{L + 120}" y="{T + 22}">value creation</text></g>')
        svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Six projects plotted over time; the curve rises and falls with the scale of value created" class="g-svg">{defs}'
               f'{grid}<line class="g-base" x1="{L}" x2="{R}" y1="{B}" y2="{B}"/>{ticks}{stems}'
               f'<polygon class="g-area" points="{pts[0][0]:.1f},{B} {line} {pts[-1][0]:.1f},{B}"/>'
               f'<polyline class="g-line" points="{line}"/>{legend}{dots}'
               f'<text class="g-ax" x="{L}" y="{T - 14}">Scale</text>'
               f'<text class="g-ax" x="{R}" y="{B + 50}" text-anchor="end">Time \u2192</text></svg>')
        cols = ''.join(
            f'<li><a href="{slug}.html"><span class="nyt-k">Project {i + 1:02d}</span><span class="g-t">{html.escape(name)}</span><span class="g-m"><i>{d[3]}</i> \u00b7 {d[4]}</span></a></li>'
            for i, ((slug, name), d) in enumerate(zip(PROJECTS, DATA)))
        return (f'<div class="g-head"><span class="nyt-k">Value Creation</span><h2>My Project Timeline</h2></div>'
                f'<div class="g-chart">{svg}</div><ol class="g-cols">{cols}</ol>')

    def index(self):
        graph = self.graph()
        body = f'''<section class="hero" aria-label="Value through Connection">
  <video autoplay muted loop playsinline preload="auto" disablepictureinpicture aria-hidden="true">
    <source src="assets/video/hero.mp4" type="video/mp4">
  </video>
  <div class="hero-text">
    <span class="nyt-k">Design Vision</span>
    <h1 class="vtc-h">Value through Connection</h1>
    <p class="vtc">Across six projects, I <span class="vc-u">connect</span> people, programs and places to design spaces whose worth can be felt \u2014 and measured. I read architecture through the lens of <span class="vc-u">valuation</span>, where design logic meets the <span class="vc-u">quantifiable worth</span> of space.</p>
    <span class="by">By Dabin Jeong \u00b7 Hongik University, Architecture</span>
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
        if (ROOT / 'docs' / 'photos').exists():
            shutil.copytree(ROOT / 'docs' / 'photos', out / 'photos', dirs_exist_ok=True)
    made = Site(a.manifest, out).build()
    print('만든 페이지:', ', '.join(['index', 'info'] + made), '| 준비 중:', ', '.join(s for s, _ in PROJECTS if s not in made) or '없음')
