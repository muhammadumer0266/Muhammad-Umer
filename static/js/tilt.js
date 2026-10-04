// Card tilt (max ~4deg) with a pointer-following sheen.
// section 7. Ignores touch input and respects prefers-reduced-motion.
//
// Deliberately does NOT use element.style.setProperty(): CSP's style-src
// (no 'unsafe-inline') blocks inline style
// mutation exactly like it blocks a static style="" attribute -- this was a
// real bug caught by testing in a real browser with CSP enabled, not by
// template inspection. Instead, one nonce'd <style> element is created
// once (the nonce makes *creating* it CSP-legal), and each card gets its
// own CSS rule inside it; updates mutate that rule's CSSOM (already-loaded
// stylesheet rule mutation is not gated by style-src, only the initial
// creation is).
function getNonce() {
  const meta = document.querySelector('meta[name="csp-nonce"]');
  return meta ? meta.content : "";
}

let sheet = null;
let ruleCounter = 0;

function ensureSheet() {
  if (sheet) return sheet;
  const styleEl = document.createElement("style");
  styleEl.nonce = getNonce();
  document.head.appendChild(styleEl);
  sheet = styleEl.sheet;
  return sheet;
}

function createRuleFor(node) {
  const id = `tilt-${ruleCounter++}`;
  node.dataset.tiltId = id;
  const index = ensureSheet().insertRule(
    `[data-tilt-id="${id}"] { --rx: 0deg; --ry: 0deg; --mx: 50%; --my: 50%; }`,
    sheet.cssRules.length,
  );
  return sheet.cssRules[index].style;
}

export function attachTilt(node, { ping, pingIndex = 0, reducedMotion } = {}) {
  const ruleStyle = createRuleFor(node);

  node.addEventListener("pointermove", (e) => {
    if (e.pointerType === "touch" || reducedMotion) return;
    const r = node.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width;
    const y = (e.clientY - r.top) / r.height;
    ruleStyle.setProperty("--ry", `${((x - 0.5) * 4).toFixed(2)}deg`);
    ruleStyle.setProperty("--rx", `${((0.5 - y) * 3).toFixed(2)}deg`);
    ruleStyle.setProperty("--mx", `${(x * 100).toFixed(1)}%`);
    ruleStyle.setProperty("--my", `${(y * 100).toFixed(1)}%`);
  });
  node.addEventListener("pointerleave", () => {
    ruleStyle.setProperty("--rx", "0deg");
    ruleStyle.setProperty("--ry", "0deg");
  });
  if (ping) {
    node.addEventListener("pointerenter", (e) => {
      if (e.pointerType !== "touch") ping(pingIndex);
    });
  }
}

export function attachTiltToAll(selector, options) {
  document.querySelectorAll(selector).forEach((node, i) => {
    attachTilt(node, { ...options, pingIndex: i % 5 });
  });
}
