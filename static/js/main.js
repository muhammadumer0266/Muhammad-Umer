// Progressive-enhancement entry point. The page is fully usable without any
// of this: everything here only adds motion, sound
// and tilt on top of already-readable, already-navigable server HTML.
import { createAudioController } from "./audio.js";
import { initReveal } from "./reveal.js";
import { attachTiltToAll } from "./tilt.js";

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const audio = createAudioController();

initReveal(reducedMotion);
attachTiltToAll(".entry-card", { ping: audio.ping, reducedMotion });

function wireSoundToggle(button) {
  if (!button) return;
  button.addEventListener("click", () => {
    audio.setSound(!audio.isOn(), (on) => {
      button.setAttribute("aria-pressed", on ? "true" : "false");
      const label = button.querySelector("[data-sound-label]");
      if (label) label.textContent = on ? "Sound on" : "Sound off";
    });
    audio.ping(0);
  });
}
wireSoundToggle(document.getElementById("sound-toggle"));

const enterSoundButton = document.getElementById("enter-sound");
if (enterSoundButton) {
  enterSoundButton.addEventListener("click", () => {
    audio.setSound(true, (on) => {
      const headerToggle = document.getElementById("sound-toggle");
      if (headerToggle) {
        headerToggle.setAttribute("aria-pressed", on ? "true" : "false");
        const label = headerToggle.querySelector("[data-sound-label]");
        if (label) label.textContent = on ? "Sound on" : "Sound off";
      }
    });
    audio.ping(3);
  });
}

function shouldSkip3D() {
  const connection = navigator.connection;
  if (connection && connection.saveData) return true;
  if (navigator.deviceMemory && navigator.deviceMemory <= 2) return true;
  if (!window.WebGLRenderingContext) return true;
  return false;
}

function loadStage() {
  const canvas = document.getElementById("gl");
  if (!canvas || shouldSkip3D()) {
    document.documentElement.classList.add("nogl");
    return;
  }
  import("./stage.js")
    .then(({ initStage }) => {
      const stage = initStage(canvas, { reducedMotion, getAudioSpike: audio.getSpike });
      if (!stage) document.documentElement.classList.add("nogl");
    })
    .catch(() => {
      document.documentElement.classList.add("nogl");
    });
}

function deferLoadStage() {
  if ("requestIdleCallback" in window) {
    window.requestIdleCallback(loadStage, { timeout: 2000 });
  } else {
    setTimeout(loadStage, 200);
  }
}

if (document.readyState === "complete") {
  deferLoadStage();
} else {
  window.addEventListener("load", deferLoadStage, { once: true });
}

if (new URLSearchParams(window.location.search).has("debug")) {
  const footer = document.querySelector(".site-footer__inner");
  if (footer) {
    const readout = document.createElement("span");
    readout.id = "fps-readout";
    readout.className = "label";
    footer.appendChild(readout);
  }
}
