document.addEventListener("DOMContentLoaded", function () {
  var search = document.getElementById("skill-search");
  var noResults = document.getElementById("no-results");
  if (!search) return;

  var categories = document.querySelectorAll(".catalog-category");
  var allSkillsSection = document.querySelector(".catalog-all-skills");
  var filterBtns = document.querySelectorAll(".filter-btn");
  var activeCat = "all";

  filterBtns.forEach(function (btn) {
    btn.addEventListener("click", function () {
      filterBtns.forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      activeCat = btn.getAttribute("data-cat");
      applyFilters();
    });
  });

  search.addEventListener("input", function () {
    applyFilters();
  });

  function applyFilters() {
    var query = search.value.toLowerCase().trim();
    var anyVisible = false;

    categories.forEach(function (cat) {
      var catKey = cat.getAttribute("data-cat");
      var catMatch = activeCat === "all" || catKey === activeCat;

      if (!catMatch) {
        cat.style.display = "none";
        return;
      }

      var cards = cat.querySelectorAll(".feature-card");
      var catHasVisible = false;

      cards.forEach(function (card) {
        var text = card.textContent.toLowerCase();
        var skills = (card.getAttribute("data-skills") || "").toLowerCase();
        var match = !query || text.indexOf(query) !== -1 || skills.indexOf(query) !== -1;
        card.style.display = match ? "" : "none";
        if (match) catHasVisible = true;
      });

      cat.style.display = catHasVisible ? "" : "none";
      if (catHasVisible) anyVisible = true;
    });

    if (allSkillsSection) {
      var rows = allSkillsSection.querySelectorAll("tbody tr");
      rows.forEach(function (row) {
        var text = row.textContent.toLowerCase();
        var match = !query || text.indexOf(query) !== -1;
        row.style.display = match ? "" : "none";
      });
    }

    if (noResults) {
      noResults.style.display = anyVisible ? "none" : "block";
    }
  }
});
