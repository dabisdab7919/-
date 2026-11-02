#!/usr/bin/env python3
"""data/images.json 에 있는 Cargo 이미지/영상을 docs/assets/images/ 로 내려받아
사이트가 Cargo 서버 없이도 보이도록 주소를 바꿉니다. (본인 컴퓨터에서 실행하세요)

    python3 tools/download_images.py
    python3 tools/build.py

원본(/t/original/)을 먼저 시도하고, 안 되면 JSON에 적힌 주소를 사용합니다.
"""
import json, pathlib, re, shutil, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
MANI = ROOT / 'data' / 'images.json'
OUT = ROOT / 'docs' / 'assets' / 'images'
OUT.mkdir(parents=True, exist_ok=True)

def fetch(url, dest):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, 'wb') as f:
        shutil.copyfileobj(r, f)

data = json.loads(MANI.read_text(encoding='utf-8'))
backup = ROOT / 'data' / 'images.cargo.json'
if not backup.exists():
    backup.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
src_map = json.loads(backup.read_text(encoding='utf-8'))      # 항상 Cargo 원본 주소 기준

new, fail = {}, []
for i, (h, url) in enumerate(src_map.items(), 1):
    ext = pathlib.Path(urllib.parse.urlparse(url).path).suffix.lower() or '.jpg'
    dest = OUT / f'{h}{ext}'
    if dest.exists() and dest.stat().st_size > 0:
        new[h] = f'assets/images/{dest.name}'; continue
    tries = [re.sub(r'/w/\d+/', '/t/original/', url), re.sub(r'/w/\d+/', '/w/2400/', url), url]
    for t in dict.fromkeys(tries):
        try:
            fetch(t, dest); new[h] = f'assets/images/{dest.name}'; break
        except Exception as e:
            dest.unlink(missing_ok=True)
    else:
        fail.append(h); new[h] = url
    print(f'[{i}/{len(src_map)}] {h} {"OK" if h in new and new[h].startswith("assets") else "실패"}')

MANI.write_text(json.dumps(new, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'\n완료. 실패 {len(fail)}개', fail or '')
