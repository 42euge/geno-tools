(function () {
  var overlay = document.getElementById("splash-overlay");
  var faceEl = document.getElementById("geno-face");
  if (!overlay || !faceEl) return;

  // Hide ALL Material chrome
  document.querySelectorAll(".md-header, .md-tabs, .md-sidebar, .md-footer").forEach(function (el) {
    el.style.display = "none";
  });

  // Style overlay as full-screen splash
  overlay.style.cssText = "position:fixed;top:0;left:0;width:100vw;height:100vh;background:#0e0b14;z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;user-select:none;-webkit-user-select:none";

  // Move face into overlay
  overlay.appendChild(faceEl);
  faceEl.style.cssText = "width:min(65vmin,400px);height:min(65vmin,400px);z-index:1";

  // Title
  var title = document.createElement("div");
  title.innerHTML = 'geno-<span style="background:linear-gradient(135deg,#f0923a,#e8650a);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">tools</span>';
  title.style.cssText = "margin-top:2rem;font-size:clamp(1.8rem,5vw,3.2rem);font-weight:800;letter-spacing:-0.03em;color:#fff;font-family:Inter,-apple-system,system-ui,sans-serif;opacity:0;animation:splash-fade 1.5s ease 0.5s forwards;z-index:1";
  overlay.appendChild(title);

  // Subtitle
  var sub = document.createElement("div");
  sub.textContent = "the package manager for AI coding agent skillsets";
  sub.style.cssText = "margin-top:0.6rem;font-size:clamp(0.85rem,2vw,1.1rem);color:#8a7fa0;font-weight:400;font-family:Inter,-apple-system,system-ui,sans-serif;opacity:0;animation:splash-fade 1.5s ease 1s forwards;z-index:1";
  overlay.appendChild(sub);

  // Overview blurb
  var blurb = document.createElement("div");
  blurb.textContent = "Install, fork, experiment, and promote skillsets for Claude Code, geno-cli, Codex, Gemini CLI, and more — all from one CLI.";
  blurb.style.cssText = "margin-top:1.2rem;font-size:clamp(0.75rem,1.5vw,0.95rem);color:#5c5470;max-width:420px;text-align:center;line-height:1.5;font-family:Inter,-apple-system,system-ui,sans-serif;opacity:0;animation:splash-fade 1.5s ease 1.3s forwards;z-index:1";
  overlay.appendChild(blurb);

  // Buttons
  var btnWrap = document.createElement("div");
  btnWrap.style.cssText = "display:flex;gap:1rem;margin-top:2rem;flex-wrap:wrap;justify-content:center;opacity:0;animation:splash-fade 1.5s ease 1.6s forwards;z-index:1";

  var btnPrimary = document.createElement("a");
  btnPrimary.href = "getting-started/";
  btnPrimary.textContent = "Get Started";
  btnPrimary.style.cssText = "display:inline-block;padding:0.7rem 2rem;border-radius:2rem;font-weight:600;text-decoration:none;font-family:Inter,-apple-system,system-ui,sans-serif;font-size:0.95rem;background:linear-gradient(135deg,#e8650a,#f0923a);color:#fff;box-shadow:0 4px 15px #e8650a40;transition:all 0.2s ease";
  btnPrimary.onmouseenter = function(){this.style.transform="translateY(-2px)";this.style.boxShadow="0 6px 25px #e8650a60"};
  btnPrimary.onmouseleave = function(){this.style.transform="";this.style.boxShadow="0 4px 15px #e8650a40"};

  var btnSecondary = document.createElement("a");
  btnSecondary.href = "docs-home/";
  btnSecondary.textContent = "Docs Home";
  btnSecondary.style.cssText = "display:inline-block;padding:0.7rem 2rem;border-radius:2rem;font-weight:600;text-decoration:none;font-family:Inter,-apple-system,system-ui,sans-serif;font-size:0.95rem;border:2px solid #e8650a80;color:#f0923a;transition:all 0.2s ease";
  btnSecondary.onmouseenter = function(){this.style.background="#e8650a15";this.style.borderColor="#e8650a"};
  btnSecondary.onmouseleave = function(){this.style.background="";this.style.borderColor="#e8650a80"};

  btnWrap.appendChild(btnPrimary);
  btnWrap.appendChild(btnSecondary);
  overlay.appendChild(btnWrap);

  // Glow
  var glow = document.createElement("div");
  glow.style.cssText = "position:absolute;width:min(90vmin,550px);height:min(90vmin,550px);border-radius:50%;background:radial-gradient(circle,#2d105018 0%,transparent 70%);pointer-events:none;z-index:0";
  overlay.insertBefore(glow, faceEl);

  // Inject keyframes
  var style = document.createElement("style");
  style.textContent = "@keyframes splash-fade{to{opacity:1}}";
  document.head.appendChild(style);


  // --- Animated SVG Face ---
  var BG = "#0e0b14", EYE = "#e8650a", MOUTH = "#c4a8d8", ED = 55;
  var CYCLE = 8000, HOLD = 2000, AMP = 12;
  var L_INNER = [228, 158], R_INNER = [284, 158];
  var L_OX = 118, R_OX = 394, OY = 140;
  var L_PX = (L_OX + L_INNER[0]) / 2 + 8, L_PY = (OY + L_INNER[1]) / 2 + ED * 0.28;
  var R_PX = (R_OX + R_INNER[0]) / 2 - 8, R_PY = (OY + R_INNER[1]) / 2 + ED * 0.28;

  var gw = 356, gy = 220, curl = 58, ghw = gw / 2;
  var grin = "M" + (256-ghw) + " " + (gy-curl) +
    " C" + (256-ghw+8) + " " + (gy+10) + " " + (256-96) + " " + (gy+42) + " 256 " + (gy+44) +
    " C" + (256+96) + " " + (gy+42) + " " + (256+ghw-8) + " " + (gy+10) + " " + (256+ghw) + " " + (gy-curl) +
    " C" + (256+ghw-5) + " " + (gy+30) + " " + (256+80) + " " + (gy+95) + " 256 " + (gy+100) +
    " C" + (256-80) + " " + (gy+95) + " " + (256-ghw+5) + " " + (gy+30) + " " + (256-ghw) + " " + (gy-curl) + " Z";

  var teethXs = [148,183,218,256,294,329,364], tY1 = gy-curl-10, tY2 = gy+110;
  var ns = "http://www.w3.org/2000/svg";

  function svgEl(tag, attrs) {
    var e = document.createElementNS(ns, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }

  var svg = svgEl("svg", {viewBox:"0 0 512 512", width:"100%", height:"100%"});
  var defs = svgEl("defs",{}), cp = svgEl("clipPath",{id:"gc"});
  cp.appendChild(svgEl("path",{d:grin}));
  defs.appendChild(cp); svg.appendChild(defs);
  svg.appendChild(svgEl("rect",{width:512, height:512, fill:BG}));

  var leftEye = svgEl("path",{fill:EYE});
  var rightEye = svgEl("path",{fill:EYE});
  svg.appendChild(leftEye); svg.appendChild(rightEye);

  svg.appendChild(svgEl("ellipse",{cx:L_PX, cy:L_PY, rx:7, ry:8, fill:BG}));
  svg.appendChild(svgEl("circle",{cx:L_PX-2, cy:L_PY-3, r:2.5, fill:"#fff"}));
  svg.appendChild(svgEl("ellipse",{cx:R_PX, cy:R_PY, rx:6, ry:7, fill:BG}));
  svg.appendChild(svgEl("circle",{cx:R_PX-2, cy:R_PY-3, r:2, fill:"#fff"}));
  svg.appendChild(svgEl("path",{d:grin, fill:MOUTH, stroke:BG, "stroke-width":2}));

  var tg = svgEl("g",{"clip-path":"url(#gc)"});
  for (var i = 0; i < teethXs.length; i++) {
    tg.appendChild(svgEl("path",{
      d:"M"+teethXs[i]+" "+tY1+" L"+teethXs[i]+" "+tY2,
      stroke:BG,"stroke-width":3.5,"stroke-linecap":"round",fill:"none"
    }));
  }
  svg.appendChild(tg);
  faceEl.appendChild(svg);

  function eyePath(ox, oy, ix, iy) {
    var dx = ix - ox;
    return "M"+ox+" "+oy+" L"+ix+" "+iy+
      " C"+(ix-dx*0.25)+" "+(iy+ED*0.8)+" "+(ox+dx*0.25)+" "+(oy+ED*0.8)+" "+ox+" "+oy+" Z";
  }

  function animate(ts) {
    var t = (ts % CYCLE) / CYCLE, hf = HOLD/CYCLE, phase, phaseR;
    if (t < hf) { phase = 0; phaseR = 0; }
    else {
      var t2 = (t-hf)/(1-hf);
      phase = Math.sin(t2*2*Math.PI);
      phaseR = Math.sin(t2*2*Math.PI - 0.3);
    }
    leftEye.setAttribute("d", eyePath(L_OX, OY+phase*AMP, L_INNER[0], L_INNER[1]));
    rightEye.setAttribute("d", eyePath(R_OX, OY+phaseR*AMP, R_INNER[0], R_INNER[1]));
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
})();
