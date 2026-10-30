# Dabin Jeong — Value through Connection (포트폴리오 사이트)

Cargo 없이 어디서나 열리는 **정적 웹사이트**입니다. 완성된 사이트는 `docs/` 폴더입니다.

## 미리보기
- `docs/index.html` 을 더블클릭하면 브라우저에서 열립니다.
- 또는 터미널에서 `python3 -m http.server -d docs 8000` → http://localhost:8000

## 올리기(배포)
- **GitHub Pages**: 저장소 Settings → Pages → Branch 를 선택하고 폴더를 `/docs` 로 지정.
- **Netlify / Vercel / Cloudflare Pages**: `docs` 폴더를 통째로 끌어다 놓기(또는 Publish directory = `docs`).

## 폴더
```
docs/                 완성된 사이트 (HTML, CSS, JS, 폰트, 영상)
  assets/css/style.css  디자인 전체
  assets/js/site.js     슬라이드쇼 · 확대 보기 · 시계
  assets/images/        내려받은 이미지(아래 참고)
data/*.json           프로젝트 페이지의 내용 (글, 제목, 이미지 목록)
data/images.json      이미지 ID → 실제 이미지 주소
tools/                만들기·변환 도구
```

## 페이지 내용 고치기
글/제목/이미지 순서는 `data/<프로젝트>.json` 에서 고치고 `python3 tools/build.py` 를 실행하면 `docs/` 가 다시 만들어집니다.
(Claude에게 “이 문구를 바꿔줘”라고 요청해도 됩니다.)

## Cargo에서 페이지 가져오기
Cargo 코드 보기(`</>`)의 HTML을 파일로 저장한 뒤:
```
python3 tools/import_cargo_page.py 저장한파일.html hwamyeong
python3 tools/build.py
```

## 이미지가 보이게 하기 (중요)
Cargo의 `<media-item hash="…">` 는 Cargo 서버에서만 풀리는 ID라서, 실제 이미지 주소가 필요합니다.
1. 공개된 Cargo 페이지(예: `…cargo.site/communicate`)를 크롬으로 열고, F12 → Console 에 `tools/extract-images.js` 내용을 붙여넣기 → 나온 목록 복사.
2. `python3 tools/add_images.py 목록.json` 으로 `data/images.json` 에 합치기 (프로젝트마다 반복).
3. `python3 tools/build.py` → 이미지가 연결됩니다.
4. **Cargo를 해지해도 이미지가 남도록** 본인 컴퓨터에서 `python3 tools/download_images.py` 로 이미지를 `docs/assets/images/` 에 내려받고 다시 `python3 tools/build.py`.

## 글꼴
Cheltenham, English Towne, Georgia 는 `docs/assets/fonts/` 에 들어 있습니다. Cargo 전용 글꼴(ROM, Gaisyr, Diatype)은 가져올 수 없어
Barlow Condensed(Google Fonts)와 시스템 글꼴로 대체했습니다.
