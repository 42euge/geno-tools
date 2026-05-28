document.addEventListener("DOMContentLoaded", function () {
  var depth = document.querySelector(".zoom-depth");
  if (!depth) return;

  var article = document.querySelector(".md-content__inner");
  if (!article) return;

  var landingNodes = [];
  var node = article.firstChild;
  while (node && node !== depth) {
    landingNodes.push(node);
    node = node.nextSibling;
  }

  var sections = depth.querySelectorAll(".zoom-section");
  if (!sections.length) return;

  var levels = [
    { label: "What", icon: "⌘" },
  ];
  sections.forEach(function (sec) {
    if (sec.classList.contains("zoom-section-3"))
      levels.push({ label: "When", icon: "◎", el: sec });
    else if (sec.classList.contains("zoom-section-4"))
      levels.push({ label: "How", icon: "⚙", el: sec });
    else if (sec.classList.contains("zoom-section-5"))
      levels.push({ label: "Why", icon: "◇", el: sec });
  });

  var viewer = document.createElement("div");
  viewer.className = "zoom-viewer";

  // Breadcrumb-style nav
  var bar = document.createElement("div");
  bar.className = "zv-bar";
  levels.forEach(function (lv, i) {
    if (i > 0) {
      var sep = document.createElement("span");
      sep.className = "zv-sep";
      sep.textContent = "›";
      bar.appendChild(sep);
    }
    var btn = document.createElement("button");
    btn.className = "zv-step";
    btn.innerHTML = '<span class="zv-step-icon">' + lv.icon + '</span>' + lv.label;
    btn.addEventListener("click", function () { goTo(i); });
    bar.appendChild(btn);
  });
  viewer.appendChild(bar);

  var pane = document.createElement("div");
  pane.className = "zv-pane";
  viewer.appendChild(pane);

  var canvas = document.createElement("canvas");
  canvas.className = "zv-canvas";
  pane.appendChild(canvas);
  var ctx = canvas.getContext("2d");

  // Frames
  var frames = [];

  var f0 = document.createElement("div");
  f0.className = "zv-frame zv-frame-active";
  landingNodes.forEach(function (n) { f0.appendChild(n.cloneNode(true)); });
  pane.appendChild(f0);
  frames.push(f0);

  levels.slice(1).forEach(function (lv) {
    var frame = document.createElement("div");
    frame.className = "zv-frame";
    var clone = lv.el.cloneNode(true);
    if (lv.label === "How") {
      truncateFrame(clone, 600);
      var more = document.createElement("a");
      more.className = "zv-read-more";
      more.textContent = "Read full definition →";
      more.href = "#";
      more.addEventListener("click", function (e) { e.preventDefault(); exitViewer(); });
      clone.appendChild(more);
    }
    var ch = clone.children;
    for (var i = 0; i < ch.length; i++) frame.appendChild(ch[i].cloneNode(true));
    pane.appendChild(frame);
    frames.push(frame);
  });

  var hint = document.createElement("div");
  hint.className = "zv-hint";
  hint.textContent = "scroll to go deeper";
  viewer.appendChild(hint);

  article.style.display = "none";
  article.parentNode.insertBefore(viewer, article);

  var current = 0, animating = false, mouseX = 0, mouseY = 0;
  updateNav();

  viewer.addEventListener("mousemove", function (e) {
    var r = pane.getBoundingClientRect();
    mouseX = e.clientX - r.left;
    mouseY = e.clientY - r.top;
  });

  function exitViewer() {
    viewer.style.display = "none";
    article.style.display = "";
  }

  function truncateFrame(el, max) {
    var count = 0;
    var walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, null, false);
    var nodes = [], tn;
    while ((tn = walker.nextNode())) nodes.push(tn);
    for (var i = 0; i < nodes.length; i++) {
      count += nodes[i].textContent.length;
      if (count > max) {
        nodes[i].textContent = nodes[i].textContent.substring(0, nodes[i].textContent.length - (count - max)) + "…";
        var p = nodes[i].parentNode;
        while (p && p !== el) { while (p.nextSibling) p.parentNode.removeChild(p.nextSibling); p = p.parentNode; }
        break;
      }
    }
  }

  // Particles
  function samplePositions(frame, count) {
    var rect = pane.getBoundingClientRect(), positions = [], texts = [];
    var w = document.createTreeWalker(frame, NodeFilter.SHOW_TEXT, null, false);
    var t; while ((t = w.nextNode())) { if (t.textContent.trim()) texts.push(t); }
    if (!texts.length) {
      for (var i = 0; i < count; i++) positions.push({ x: Math.random() * rect.width, y: Math.random() * 300 });
      return positions;
    }
    for (var i = 0; i < count; i++) {
      var t = texts[Math.floor(Math.random() * texts.length)];
      var range = document.createRange();
      var ci = Math.floor(Math.random() * t.textContent.length);
      range.setStart(t, ci); range.setEnd(t, Math.min(ci + 1, t.textContent.length));
      var cr = range.getBoundingClientRect();
      if (cr.width > 0 && cr.height > 0) positions.push({ x: cr.left - rect.left + Math.random() * cr.width, y: cr.top - rect.top + Math.random() * cr.height });
      else positions.push({ x: Math.random() * rect.width, y: Math.random() * 300 });
    }
    return positions;
  }

  function animateTransition(fromFrame, toFrame, cb) {
    var rect = pane.getBoundingClientRect();
    canvas.width = rect.width * devicePixelRatio;
    canvas.height = rect.height * devicePixelRatio;
    canvas.style.width = rect.width + "px";
    canvas.style.height = rect.height + "px";
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);

    fromFrame.style.cssText = "position:relative;opacity:1;pointer-events:none";
    var fromP = samplePositions(fromFrame, 300);
    fromFrame.style.cssText = ""; fromFrame.classList.remove("zv-frame-active");

    toFrame.style.cssText = "position:relative;opacity:1;pointer-events:none";
    var toP = samplePositions(toFrame, 300);
    toFrame.style.cssText = "";

    canvas.style.display = "block";
    toFrame.classList.add("zv-frame-active");
    toFrame.style.opacity = "0";

    var cx = mouseX || rect.width / 2, cy = mouseY || 150;
    var particles = [];
    for (var i = 0; i < 300; i++) {
      var f = fromP[i], t = toP[i];
      var a = Math.atan2(f.y - cy, f.x - cx) + (Math.random() - 0.5) * 1.2;
      var d = 50 + Math.random() * 120;
      particles.push({ sx: f.x, sy: f.y, mx: cx + Math.cos(a) * d, my: cy + Math.sin(a) * d, ex: t.x, ey: t.y, r: Math.random() * 2 + 0.5, c: Math.random() > 0.4 ? [232, 101, 10] : [45, 27, 78], dl: Math.random() * 0.1 });
    }

    var dur = 600, start = performance.now();
    function draw(now) {
      var t = Math.min((now - start) / dur, 1);
      ctx.clearRect(0, 0, rect.width, rect.height);
      toFrame.style.opacity = String(t < 0.45 ? 0 : (t - 0.45) / 0.55);

      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        var pt = Math.max(0, Math.min(1, (t - p.dl) / (1 - p.dl)));
        var x, y, al;
        if (pt < 0.4) { var e = pt / 0.4; e = e * (2 - e); x = p.sx + (p.mx - p.sx) * e; y = p.sy + (p.my - p.sy) * e; al = 1 - e * 0.5; }
        else { var e = (pt - 0.4) / 0.6; e = e * e * (3 - 2 * e); x = p.mx + (p.ex - p.mx) * e; y = p.my + (p.ey - p.my) * e; al = 0.5 + e * 0.5; }
        ctx.globalAlpha = al;
        ctx.fillStyle = "rgb(" + p.c[0] + "," + p.c[1] + "," + p.c[2] + ")";
        ctx.beginPath(); ctx.arc(x, y, p.r, 0, Math.PI * 2); ctx.fill();
      }
      if (t < 1) requestAnimationFrame(draw);
      else { ctx.clearRect(0, 0, rect.width, rect.height); canvas.style.display = "none"; toFrame.style.opacity = "1"; cb(); }
    }
    requestAnimationFrame(draw);
  }

  function goTo(idx) { if (idx !== current) transition(idx); }

  function transition(idx) {
    if (idx < 0 || idx >= frames.length || idx === current || animating) return;
    animating = true; hint.style.opacity = "0";
    var old = frames[current]; current = idx; updateNav();
    animateTransition(old, frames[idx], function () { animating = false; });
  }

  function updateNav() {
    bar.querySelectorAll(".zv-step").forEach(function (s, i) {
      s.classList.toggle("zv-step-active", i === current);
      s.classList.toggle("zv-step-past", i < current);
    });
    bar.querySelectorAll(".zv-sep").forEach(function (s, i) {
      s.classList.toggle("zv-sep-past", i < current);
    });
  }

  var cooldown = false;
  viewer.addEventListener("wheel", function (e) {
    e.preventDefault();
    if (cooldown || animating) return; cooldown = true;
    if (e.deltaY > 0 && current < frames.length - 1) transition(current + 1);
    else if (e.deltaY < 0 && current > 0) transition(current - 1);
    setTimeout(function () { cooldown = false; }, 700);
  }, { passive: false });

  document.addEventListener("keydown", function (e) {
    if (!viewer.offsetParent) return;
    if (e.key === "ArrowDown" || e.key === "j") { e.preventDefault(); if (current < frames.length - 1) transition(current + 1); }
    else if (e.key === "ArrowUp" || e.key === "k") { e.preventDefault(); if (current > 0) transition(current - 1); }
    else if (e.key === "Escape") exitViewer();
  });

  var touchY = 0;
  viewer.addEventListener("touchstart", function (e) { touchY = e.touches[0].clientY; }, { passive: true });
  viewer.addEventListener("touchend", function (e) {
    var dy = touchY - e.changedTouches[0].clientY;
    if (Math.abs(dy) < 30) return;
    if (dy > 0 && current < frames.length - 1) transition(current + 1);
    else if (dy < 0 && current > 0) transition(current - 1);
  }, { passive: true });
});
