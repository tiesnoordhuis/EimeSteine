/*
 * Eime Steine — small progressive enhancements.
 *
 * Everything on the site works without this file. It adds the photo viewer,
 * keeps the mobile menu button's aria-expanded state in sync, and provides a
 * fallback for browsers without the popover API.
 */

(() => {
  "use strict";

  /* Mobile menu ---------------------------------------------------------- */

  const menu = document.querySelector("#site-menu");
  const menuButton = document.querySelector(".menu-button");

  if (menu && menuButton) {
    const sync = () => {
      const open = menu.matches(":popover-open");
      menuButton.setAttribute("aria-expanded", String(open));
    };

    if ("showPopover" in HTMLElement.prototype) {
      menu.addEventListener("toggle", sync);
      sync();
    } else {
      // Older browsers ignore the popover attribute. The stylesheet hides the
      // menu in that case; this keeps the button working.
      menuButton.addEventListener("click", () => {
        const open = menu.classList.toggle("is-open");
        menuButton.setAttribute("aria-expanded", String(open));
      });
    }
  }

  /* Photo viewer --------------------------------------------------------- */

  const dialog = document.querySelector("#lightbox");
  if (!dialog) return;

  const image = dialog.querySelector("#lb-img");
  const webp = dialog.querySelector("#lb-webp");
  const caption = dialog.querySelector("#lb-caption");
  const links = Array.from(document.querySelectorAll(".gallery a[data-src]"));
  if (!links.length) return;

  let index = 0;
  let lastFocus = null;

  const render = (next) => {
    index = (next + links.length) % links.length;
    const link = links[index];

    webp.srcset = link.dataset.webpSrcset || "";
    image.src = link.dataset.src;
    image.srcset = link.dataset.srcset || "";
    image.sizes = "(min-width: 900px) 80vw, 94vw";
    image.alt = link.dataset.alt || "";
    image.width = Number(link.dataset.width) || 1400;
    image.height = Number(link.dataset.height) || 1050;
    caption.textContent = link.dataset.caption || "";
  };

  const open = (i, trigger) => {
    lastFocus = trigger;
    render(i);
    dialog.showModal();
    document.documentElement.classList.add("no-scroll");
  };

  links.forEach((link, i) => {
    link.addEventListener("click", (event) => {
      // Leave modified clicks alone so "open in new tab" still works.
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      open(i, link);
    });
  });

  dialog.addEventListener("close", () => {
    document.documentElement.classList.remove("no-scroll");
    webp.removeAttribute("srcset");
    image.removeAttribute("srcset");
    image.removeAttribute("src");
    if (lastFocus) lastFocus.focus();
  });

  // Clicking the dark area around the photo closes the viewer.
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  dialog.querySelector(".lb-close").addEventListener("click", () => dialog.close());
  dialog.querySelector(".lb-prev").addEventListener("click", () => render(index - 1));
  dialog.querySelector(".lb-next").addEventListener("click", () => render(index + 1));

  dialog.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      render(index - 1);
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      render(index + 1);
    }
  });

  // Basic horizontal swipe on touch screens.
  const stage = dialog.querySelector(".lb-stage");
  let startX = 0;
  let startY = 0;
  let tracking = false;

  stage.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "mouse") return;
    tracking = true;
    startX = event.clientX;
    startY = event.clientY;
  });

  stage.addEventListener("pointerup", (event) => {
    if (!tracking) return;
    tracking = false;
    const dx = event.clientX - startX;
    const dy = event.clientY - startY;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
      render(index + (dx < 0 ? 1 : -1));
    }
  });

  stage.addEventListener("pointercancel", () => {
    tracking = false;
  });
})();
