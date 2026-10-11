// Navbar enhancement layer ("liquid gold"). The server-rendered navbar is
// complete without this file; everything here is decoration + small UX:
//
// - a liquid indicator that flows between links on hover/focus and rests
//   on the current page,
// - a cursor spotlight on the glass and a gold scroll-progress thread,
// - a magnetic "Let's talk" button,
// - compact-on-scroll, and Escape / close-on-navigate for the phone menu.
//
// CSP: no element.style writes. Positions are CSS custom properties on one
// nonce'd <style> rule (same technique as tilt.js), updated via CSSOM.

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const finePointer = window.matchMedia("(pointer: fine)").matches;

function varRule(selector) {
  const meta = document.querySelector('meta[name="csp-nonce"]');
  const el = document.createElement("style");
  el.nonce = meta ? meta.content : "";
  document.head.appendChild(el);
  el.sheet.insertRule(`${selector} {}`, 0);
  return el.sheet.cssRules[0].style;
}

function deco(className, parent, before = null) {
  const el = document.createElement("span");
  el.className = className;
  el.setAttribute("aria-hidden", "true");
  parent.insertBefore(el, before);
  return el;
}

function rafThrottle(fn) {
  let queued = false;
  let lastArgs;
  return (...args) => {
    lastArgs = args;
    if (queued) return;
    queued = true;
    requestAnimationFrame(() => {
      queued = false;
      fn(...lastArgs);
    });
  };
}

function initHeader(header) {
  const capsule = header.querySelector("[data-capsule]");
  const nav = header.querySelector("[data-site-nav]");
  const vars = varRule("[data-site-header]");

  // --- liquid indicator -------------------------------------------------------
  if (nav) {
    const list = nav.querySelector("ul");
    deco("site-nav__liquid", nav, list);
    const links = [...nav.querySelectorAll("a")];
    const current = links.find((a) => a.getAttribute("aria-current") === "page") || null;

    const moveTo = (link) => {
      if (!link || link.offsetParent === null) {
        vars.setProperty("--liq-o", "0");
        return;
      }
      const navBox = nav.getBoundingClientRect();
      const box = link.getBoundingClientRect();
      vars.setProperty("--liq-x", `${(box.left - navBox.left).toFixed(1)}px`);
      vars.setProperty("--liq-w", `${box.width.toFixed(1)}px`);
      vars.setProperty("--liq-o", "1");
    };
    const rest = () => moveTo(current);

    links.forEach((link) => {
      link.addEventListener("pointerenter", () => moveTo(link));
      link.addEventListener("focus", () => moveTo(link));
    });
    nav.addEventListener("pointerleave", rest);
    nav.addEventListener("focusout", (e) => {
      if (!nav.contains(e.relatedTarget)) rest();
    });
    window.addEventListener("resize", rafThrottle(rest));
    // Bodoni loading changes link widths; re-measure once fonts settle, and
    // after the capsule's entrance animation finishes.
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(rest);
    capsule.addEventListener("animationend", rest);
    rest();
    header.classList.add("nav-ready");
  }

  // --- spotlight + scroll thread --------------------------------------------------
  // The spotlight is painted into the capsule's glass (CSS); only its
  // position/opacity variables are set here.
  deco("site-header__thread", capsule);

  if (finePointer && !reducedMotion) {
    const spot = rafThrottle((x, y) => {
      vars.setProperty("--spot-x", `${x.toFixed(0)}px`);
      vars.setProperty("--spot-y", `${y.toFixed(0)}px`);
    });
    capsule.addEventListener("pointermove", (e) => {
      const box = capsule.getBoundingClientRect();
      spot(e.clientX - box.left, e.clientY - box.top);
      vars.setProperty("--spot-o", "1");
    });
    capsule.addEventListener("pointerleave", () => vars.setProperty("--spot-o", "0"));
  }

  const onScroll = rafThrottle(() => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const progress = max > 0 ? Math.min(1, window.scrollY / max) : 0;
    vars.setProperty("--progress", progress.toFixed(4));
    header.classList.toggle("is-scrolled", window.scrollY > 24);
  });
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // --- magnetic CTA ------------------------------------------------------------
  if (finePointer && !reducedMotion) {
    header.querySelectorAll("[data-magnetic]").forEach((el) => {
      const mag = varRule(".nav-cta[data-magnetic]");
      const move = rafThrottle((dx, dy) => {
        mag.setProperty("--mx", `${dx.toFixed(1)}px`);
        mag.setProperty("--my", `${dy.toFixed(1)}px`);
      });
      el.addEventListener("pointermove", (e) => {
        const box = el.getBoundingClientRect();
        const dx = (e.clientX - (box.left + box.width / 2)) * 0.28;
        const dy = (e.clientY - (box.top + box.height / 2)) * 0.4;
        move(Math.max(-8, Math.min(8, dx)), Math.max(-5, Math.min(5, dy)));
      });
      el.addEventListener("pointerleave", () => move(0, 0));
    });
  }
}

// Phone menu is a <details> and already works without JS; this adds the
// expected extras: Escape closes it (focus back on the toggle), choosing a
// link closes it, and widening past the breakpoint closes it.
function initDrawer(drawer) {
  const toggle = drawer.querySelector("summary");
  const sync = () => toggle.setAttribute("aria-expanded", drawer.open ? "true" : "false");
  drawer.addEventListener("toggle", sync);
  sync();
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && drawer.open) {
      drawer.open = false;
      toggle.focus();
    }
  });
  drawer.querySelectorAll("a").forEach((a) => {
    a.addEventListener("click", () => {
      drawer.open = false;
    });
  });
  window.matchMedia("(min-width: 68.01rem)").addEventListener("change", (e) => {
    if (e.matches) drawer.open = false;
  });
}

const header = document.querySelector("[data-site-header]");
if (header) initHeader(header);
const drawer = document.querySelector("[data-nav-drawer]");
if (drawer) initDrawer(drawer);
