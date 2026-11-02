/* Cargo 사이트(공개 주소)의 한 페이지에서 이미지/영상의 실제 주소를 뽑아내는 코드입니다.
 *
 * 사용법
 *  1) 크롬으로 https://workingdab.cargo.site/communicate 처럼 "공개된" 페이지를 엽니다. (편집 화면 X)
 *  2) F12 → Console 탭을 열고 이 파일 전체를 붙여넣은 뒤 Enter.
 *  3) 잠시 후 나오는 { ... } 목록을 복사해서 Claude에게 보내거나, 파일로 저장하세요.
 *  4) 프로젝트 페이지마다 반복합니다. (communicate, attract, connect, art-music, hwamyeong, rewriting)
 */
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo(0, y); await sleep(250); }
  window.scrollTo(0, 0); await sleep(600);

  const out = {}, missing = [];
  document.querySelectorAll('media-item[hash]').forEach(mi => {
    const h = mi.getAttribute('hash');
    const r = mi.shadowRoot;
    const el = (r && (r.querySelector('video') || r.querySelector('img'))) || mi.querySelector('video,img');
    let url = '';
    if (el) {
      if (el.tagName === 'VIDEO') {
        url = el.currentSrc || el.src || ((el.querySelector('source') || {}).src) || '';
      } else {
        let best = '', bw = 0;
        (el.getAttribute('srcset') || '').split(',').forEach(p => {
          p = p.trim().split(/\s+/); const w = parseFloat(p[1]) || 0;
          if (p[0] && w >= bw) { bw = w; best = p[0]; }
        });
        url = best || el.currentSrc || el.src || '';
      }
    }
    if (url) out[h] = url; else missing.push(h);
  });

  const json = JSON.stringify(out, null, 1);
  console.log('찾은 이미지: ' + Object.keys(out).length + '개 / 못 찾은 이미지: ' + missing.length + '개', missing);
  try { await navigator.clipboard.writeText(json); console.log('→ 클립보드에 복사했습니다. 그대로 붙여넣기 하세요.'); }
  catch (e) { console.log('→ 아래 내용을 직접 복사하세요.\n' + json); }
  return out;
})();
