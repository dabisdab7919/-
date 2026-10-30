/* 시계 · 슬라이드쇼 · 확대 보기 (외부 라이브러리 없음) */
(function(){
  'use strict';
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 푸터 시계 ---------- */
  var clock = document.querySelector('[data-clock]');
  if(clock){
    var pad = function(n){ return (n < 10 ? '0' : '') + n; };
    var tick = function(){ var d = new Date(); clock.textContent = pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds()); };
    tick(); setInterval(tick, 1000);
  }

  /* ---------- 확대 보기 ---------- */
  var lb, stage, lbCount, lbCap, list = [], idx = 0, lbOpen = false;

  function buildLB(){
    if(lb) return;
    lb = document.createElement('div'); lb.className = 'nyt-lb';
    lb.setAttribute('role', 'dialog'); lb.setAttribute('aria-modal', 'true');
    lb.innerHTML = '<span class="lb-count"></span><button class="lb-close" aria-label="닫기">&times;</button>' +
      '<button class="lb-nav lb-prev" aria-label="이전"><svg viewBox="0 0 24 24"><path d="M15 4l-8 8 8 8"/></svg></button>' +
      '<div class="lb-stage"></div>' +
      '<button class="lb-nav lb-next" aria-label="다음"><svg viewBox="0 0 24 24"><path d="M9 4l8 8-8 8"/></svg></button>' +
      '<div class="lb-cap"></div>';
    document.body.appendChild(lb);
    stage = lb.querySelector('.lb-stage'); lbCount = lb.querySelector('.lb-count'); lbCap = lb.querySelector('.lb-cap');
    lb.addEventListener('click', function(e){
      var t = e.target;
      if(t.closest('.lb-prev')) return lbGo(idx - 1);
      if(t.closest('.lb-next')) return lbGo(idx + 1);
      if(t.closest('.lb-close') || t === lb || t === stage) lbClose();
    });
    var sx = null;
    lb.addEventListener('touchstart', function(e){ sx = e.touches[0].clientX; }, {passive:true});
    lb.addEventListener('touchend', function(e){
      if(sx === null) return;
      var dx = e.changedTouches[0].clientX - sx; sx = null;
      if(Math.abs(dx) > 40) lbGo(idx + (dx < 0 ? 1 : -1));
    }, {passive:true});
  }
  function lbShow(){
    var im = list.imgs[idx], node = document.createElement('img');
    stage.innerHTML = '';
    node.alt = im.alt || '';
    var full = im.getAttribute('data-full'), orig = im.currentSrc || im.src;
    if(full && full !== orig){ node.onerror = function(){ node.onerror = null; node.src = orig; }; node.src = full; }
    else node.src = orig;
    stage.appendChild(node);
    lbCount.textContent = (idx + 1) + ' / ' + list.imgs.length;
    lbCap.textContent = list.cap || '';
    lb.classList.toggle('single', list.imgs.length < 2);
  }
  function lbGo(n){ idx = (n + list.imgs.length) % list.imgs.length; lbShow(); if(list.sync) list.sync(idx); }
  function lbOpenAt(imgs, i, cap, sync){
    buildLB(); list = {imgs: imgs, cap: cap, sync: sync}; idx = i; lbShow();
    lb.classList.add('open'); lbOpen = true;
    document.documentElement.style.overflow = 'hidden';
  }
  function lbClose(){
    if(!lb) return;
    lb.classList.remove('open'); lbOpen = false;
    document.documentElement.style.overflow = '';
  }
  document.addEventListener('keydown', function(e){
    if(!lbOpen) return;
    if(e.key === 'Escape') lbClose();
    else if(e.key === 'ArrowLeft') lbGo(idx - 1);
    else if(e.key === 'ArrowRight') lbGo(idx + 1);
  });

  /* ---------- 슬라이드쇼 ---------- */
  function initSlideshow(ss){
    var frame = ss.querySelector('.ss-frame');
    var imgs = [].slice.call(frame.querySelectorAll('img'));
    var count = ss.querySelector('.ss-count');
    var zoom = ss.querySelector('.ss-zoom');
    var delay = parseFloat(ss.getAttribute('data-autoplay')) || 0;
    var cur = 0, timer = null;
    if(imgs.length < 2) ss.classList.add('single');

    function ratio(im){
      if(im.naturalWidth) frame.style.setProperty('--ar', im.naturalWidth + ' / ' + im.naturalHeight);
    }
    imgs.forEach(function(im, i){
      im.addEventListener('load', function(){ if(i === cur) ratio(im); });
      im.addEventListener('error', function(){
        if(im.getAttribute('data-tried')) return im.classList.add('is-broken');
        im.setAttribute('data-tried', '1');                      /* 추측 주소가 틀렸을 때 확장자를 바꿔 한 번 더 시도 */
        var alt = im.getAttribute('data-alt-src');
        if(alt){ im.src = alt; } else im.classList.add('is-broken');
      });
      if(im.complete && im.naturalWidth && i === cur) ratio(im);
    });

    function paint(){
      if(count) count.textContent = (cur + 1) + ' / ' + imgs.length;
    }
    function show(n, fromLB){
      imgs[cur].classList.remove('is-active');
      cur = (n + imgs.length) % imgs.length;
      imgs[cur].classList.add('is-active');
      if(imgs[cur].loading === 'lazy') imgs[cur].loading = 'eager';
      ratio(imgs[cur]); paint();
    }
    ss.querySelector('.ss-prev') && ss.querySelector('.ss-prev').addEventListener('click', function(e){ e.stopPropagation(); show(cur - 1); restart(); });
    ss.querySelector('.ss-next') && ss.querySelector('.ss-next').addEventListener('click', function(e){ e.stopPropagation(); show(cur + 1); restart(); });
    if(zoom && !ss.classList.contains('nozoom')){
      zoom.addEventListener('click', function(){
        stop();
        lbOpenAt(imgs, cur, (ss.parentNode.querySelector('.nyt-cap') || {}).textContent, function(i){ show(i); });
      });
    }
    var sx = null;
    frame.addEventListener('touchstart', function(e){ sx = e.touches[0].clientX; }, {passive:true});
    frame.addEventListener('touchend', function(e){
      if(sx === null) return;
      var dx = e.changedTouches[0].clientX - sx; sx = null;
      if(Math.abs(dx) > 40){ show(cur + (dx < 0 ? 1 : -1)); restart(); }
    }, {passive:true});

    function start(){ if(delay && !reduce && imgs.length > 1 && !timer) timer = setInterval(function(){ if(!lbOpen) show(cur + 1); }, delay * 1000); }
    function stop(){ if(timer){ clearInterval(timer); timer = null; } }
    function restart(){ stop(); }
    ss.addEventListener('mouseleave', function(){ if(!lbOpen) start(); });
    ss.addEventListener('mouseenter', stop);
    document.addEventListener('visibilitychange', function(){ document.hidden ? stop() : start(); });
    paint(); start();
  }
  [].forEach.call(document.querySelectorAll('.nyt-ss'), initSlideshow);

  /* ---------- 전체 폭 미디어(이미지/영상) 실패 시 표시 ---------- */
  [].forEach.call(document.querySelectorAll('.nyt-fig img'), function(im){
    im.addEventListener('error', function(){
      var alt = im.getAttribute('data-alt-src');
      if(alt && !im.getAttribute('data-tried')){ im.setAttribute('data-tried', '1'); im.src = alt; return; }
      im.style.minHeight = '12rem'; im.alt = im.getAttribute('data-hash') || '';
    });
  });
})();
