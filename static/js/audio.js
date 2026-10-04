// Ambient generative sound (opt-in, default off, never autoplays). Ported
// from reference/prototype.html. AudioContext is only ever created inside a
// user-gesture click handler, per browser autoplay policy.
const NOTES = [261.63, 329.63, 392, 523.25, 659.25];

export function createAudioController() {
  let actx = null;
  let master = null;
  let analyser = null;
  let fdata = null;
  let soundOn = false;
  let base = 0;
  let spike = 0;

  function ensureAudio() {
    if (actx) return true;
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return false;
    actx = new AudioCtx();
    master = actx.createGain();
    master.gain.value = 0;
    const lowpass = actx.createBiquadFilter();
    lowpass.type = "lowpass";
    lowpass.frequency.value = 720;
    lowpass.Q.value = 0.6;
    analyser = actx.createAnalyser();
    analyser.fftSize = 64;
    fdata = new Uint8Array(analyser.frequencyBinCount);
    [
      [55, "sine", 0.5],
      [82.41, "sine", 0.35],
      [110.3, "triangle", 0.16],
      [164.9, "sine", 0.12],
    ].forEach(([freq, type, gainValue]) => {
      const osc = actx.createOscillator();
      osc.type = type;
      osc.frequency.value = freq;
      const gain = actx.createGain();
      gain.gain.value = gainValue;
      osc.connect(gain);
      gain.connect(lowpass);
      osc.start();
    });
    const lfo = actx.createOscillator();
    lfo.frequency.value = 0.07;
    const lfoGain = actx.createGain();
    lfoGain.gain.value = 320;
    lfo.connect(lfoGain);
    lfoGain.connect(lowpass.frequency);
    lfo.start();
    lowpass.connect(master);
    master.connect(analyser);
    analyser.connect(actx.destination);
    return true;
  }

  function setSound(on, onStateChange) {
    if (on) {
      if (!ensureAudio()) return;
      actx.resume();
      master.gain.cancelScheduledValues(actx.currentTime);
      master.gain.setTargetAtTime(0.24, actx.currentTime, 0.9);
    } else if (actx) {
      master.gain.cancelScheduledValues(actx.currentTime);
      master.gain.setTargetAtTime(0, actx.currentTime, 0.25);
    }
    soundOn = on;
    if (onStateChange) onStateChange(on);
  }

  function ping(i) {
    if (!soundOn || !actx) return;
    const t = actx.currentTime;
    const osc = actx.createOscillator();
    osc.type = "sine";
    osc.frequency.value = NOTES[Math.abs(i) % NOTES.length];
    const gain = actx.createGain();
    gain.gain.setValueAtTime(0, t);
    gain.gain.linearRampToValueAtTime(0.09, t + 0.012);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 1.3);
    osc.connect(gain);
    gain.connect(analyser);
    osc.start(t);
    osc.stop(t + 1.4);
  }

  function getSpike() {
    if (!soundOn || !analyser) {
      spike *= 0.9;
      return spike;
    }
    analyser.getByteFrequencyData(fdata);
    let raw = 0;
    for (let i = 0; i < 8; i++) raw += fdata[i];
    raw /= 8 * 255;
    base += (raw - base) * 0.01;
    const sp = Math.max(0, raw - base) * 5;
    spike += (Math.min(sp, 1) - spike) * 0.25;
    return spike;
  }

  return { setSound, ping, getSpike, isOn: () => soundOn };
}
