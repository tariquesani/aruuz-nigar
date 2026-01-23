document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('a[href^="http"]').forEach(link => {
      if (!link.href.startsWith(location.origin)) {
        link.target = "_blank";
        link.rel = "noopener";
      }
    });
  });
  