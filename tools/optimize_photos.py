#!/usr/bin/env python3
"""docs/photos 안의 사진을 웹용으로 정리합니다 (여러 번 실행해도 안전).

    python3 tools/optimize_photos.py

- 휴대폰 사진의 회전 정보를 반영해 똑바로 세웁니다.
- 긴 변이 2400px보다 크면 2400px로 줄입니다.
- 사진처럼 색이 많은 PNG는 JPG로 바꾸고, 도면처럼 단순한 PNG는 색 수를 줄입니다.
- 한글이 들어간 파일 이름은 숫자 이름으로 바꿉니다(순서 유지).
"""
import pathlib, re, subprocess, sys
from PIL import Image, ImageOps

ROOT = pathlib.Path(__file__).resolve().parent.parent
PHOTOS = ROOT / 'docs' / 'photos'
EXT = ('.jpg', '.jpeg', '.png')
MAX = 2400


def natural(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', name)]


def git(*a):
    subprocess.run(['git', *a], cwd=ROOT, capture_output=True)


def rename_korean(d):
    files = sorted((f for f in d.iterdir() if f.suffix.lower() in EXT), key=lambda f: natural(f.name))
    plain = [f for f in files if f.stem.isascii()]
    odd = [f for f in files if not f.stem.isascii()]
    nums = [int(m.group(1)) for f in plain for m in [re.fullmatch(r'(\d+)', f.stem)] if m]
    nxt = (max(nums) if nums else 0) + 1
    for f in odd:
        new = d / f'{nxt}{f.suffix.lower()}'
        git('mv', str(f), str(new)) if (ROOT / '.git').exists() else None
        if f.exists():
            f.rename(new)
        print(f'  이름 변경: {f.name} -> {new.name}')
        nxt += 1


def optimize(f):
    before = f.stat().st_size
    im = Image.open(f)
    orient = im.getexif().get(274, 1)
    im.load()
    changed = orient != 1
    if orient != 1:
        im = ImageOps.exif_transpose(im)
    if max(im.size) > MAX:
        r = MAX / max(im.size)
        im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
        changed = True
    suffix = f.suffix.lower()
    if suffix == '.png':
        rgb = im.convert('RGB')
        photo = rgb.getcolors(maxcolors=30000) is None
        has_alpha = im.mode in ('RGBA', 'LA') and im.getchannel('A').getextrema()[0] < 255
        if photo and not has_alpha:                              # 사진/렌더 -> JPG
            out = f.with_suffix('.jpg')
            if out.exists():
                print(f'  건너뜀(같은 이름 JPG 있음): {f.relative_to(PHOTOS)}'); return
            rgb.save(out, quality=85, optimize=True, progressive=True)
            git('rm', '-q', '-f', str(f)); f.unlink(missing_ok=True)
            print(f'  {f.relative_to(PHOTOS)} -> JPG  {before // 1024} -> {out.stat().st_size // 1024} KB'); return
        if before > 600 * 1024 and not has_alpha and im.mode != 'P':             # 도면 PNG: 색 수 줄이기
            rgb.quantize(256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(f, optimize=True)
            print(f'  {f.relative_to(PHOTOS)} 색 줄임  {before // 1024} -> {f.stat().st_size // 1024} KB')
        elif changed:
            im.save(f, optimize=True)
        return
    if changed or before > 1500 * 1024:
        im.convert('RGB').save(f, quality=85, optimize=True, progressive=True)
        print(f'  {f.relative_to(PHOTOS)}  {before // 1024} -> {f.stat().st_size // 1024} KB')


def main():
    for d in sorted(p for p in PHOTOS.rglob('*') if p.is_dir()):
        if any(f.suffix.lower() in EXT for f in d.iterdir()):
            rename_korean(d)
    for f in sorted(PHOTOS.rglob('*')):
        if f.is_file() and f.suffix.lower() in EXT:
            optimize(f)
    total = sum(f.stat().st_size for f in PHOTOS.rglob('*') if f.is_file()) // 1024 // 1024
    print(f'완료. 사진 전체 용량: {total}MB')


if __name__ == '__main__':
    main()
