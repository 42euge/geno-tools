document.addEventListener("DOMContentLoaded", function () {
  var sections = document.querySelectorAll(".zoom-section");
  if (!sections.length) return;

  var indicator = document.createElement("div");
  indicator.className = "zoom-indicator";
  indicator.innerHTML =
    '<span class="zi-dot zi-active" data-level="2">L2</span>' +
    '<span class="zi-dot" data-level="3">L3</span>' +
    '<span class="zi-dot" data-level="4">L4</span>' +
    '<span class="zi-dot" data-level="5">L5</span>';
  document.body.appendChild(indicator);

  var dots = indicator.querySelectorAll(".zi-dot");

  function updateIndicator() {
    var scrollY = window.scrollY + window.innerHeight * 0.4;
    var current = 2;

    sections.forEach(function (sec) {
      var rect = sec.getBoundingClientRect();
      var top = rect.top + window.scrollY;
      if (scrollY >= top) {
        if (sec.classList.contains("zoom-section-3")) current = 3;
        else if (sec.classList.contains("zoom-section-4")) current = 4;
        else if (sec.classList.contains("zoom-section-5")) current = 5;
      }
    });

    dots.forEach(function (dot) {
      var level = parseInt(dot.getAttribute("data-level"));
      dot.classList.toggle("zi-active", level <= current);
    });
  }

  var ticking = false;
  window.addEventListener("scroll", function () {
    if (!ticking) {
      requestAnimationFrame(function () {
        updateIndicator();
        ticking = false;
      });
      ticking = true;
    }
  });

  updateIndicator();
});
