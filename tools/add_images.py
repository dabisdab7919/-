#!/usr/bin/env python3
"""extract-images.js 로 얻은 목록(JSON)을 data/images.json 에 합칩니다.

    python3 tools/add_images.py 내려받은목록.json [더 있으면 계속...]
"""
import json, pathlib, sys

dst = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'images.json'
cur = json.loads(dst.read_text(encoding='utf-8')) if dst.exists() else {}
for f in sys.argv[1:]:
    new = json.loads(pathlib.Path(f).read_text(encoding='utf-8'))
    cur.update(new)
    print(f'{f}: {len(new)}개 추가')
dst.write_text(json.dumps(cur, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'images.json 전체 {len(cur)}개')
