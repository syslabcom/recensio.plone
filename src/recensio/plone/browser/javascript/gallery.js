/* CSS-only gallery keyboard navigation */
(function () {
  "use strict";

  function activeOverlay() {
    var hash = location.hash;
    if (!hash || hash === "#_") return null;
    try {
      return document.querySelector(".review-gallery__overlay" + hash);
    } catch (e) {
      return null;
    }
  }

  function navigate(overlay, selector) {
    var link = overlay.querySelector(selector);
    if (link) location.hash = link.getAttribute("href").slice(1);
  }

  document.addEventListener("keydown", function (e) {
    var overlay = activeOverlay();
    if (!overlay) return;
        if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      location.hash = "_";
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      e.stopPropagation();
      navigate(overlay, ".review-gallery__prev");
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      e.stopPropagation();
      navigate(overlay, ".review-gallery__next");
    }
  });
})();
