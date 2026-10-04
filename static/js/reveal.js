// Scroll reveal for elements marked .rv. Resting state is already readable
// (see static/css/app.css: opacity never below 0.25 pre-reveal) so a failed
// or skipped observer never hides content. Respects prefers-reduced-motion.
export function initReveal(reducedMotion) {
  const items = document.querySelectorAll(".rv");
  if (reducedMotion || !("IntersectionObserver" in window)) {
    items.forEach((el) => el.classList.add("in"));
    return;
  }
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          io.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 },
  );
  items.forEach((el) => io.observe(el));
}
