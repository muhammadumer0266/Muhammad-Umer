// Ambient music (opt-in, default off, never autoplays): a generative lo-fi /
// chillhop loop synthesised live with Web Audio -- no audio files.
//
//   82 BPM, 16th-note scheduler with swing
//   keys:  warm electric-piano chords, Fmaj9 -> Em11 -> Dm9 -> Cmaj9
//   bass:  soft sine sub on the roots
//   drums: boom-bap kick, airy snare, swung hats
//   bells: sparse pentatonic sparkle notes, plus card-hover pings
//
// The chord bus ducks under each kick (sidechain feel), and the analyser
// feeds getSpike() so the 3D orb pulses on the beat. The AudioContext is only
// created inside a user-gesture click handler, per browser autoplay policy.

const BPM = 82;
const STEP = 60 / BPM / 4; // one 16th note, seconds
const SWING = 0.18; // fraction of a 16th that off-beat 16ths are delayed
const LOOKAHEAD = 0.12;
const TICK_MS = 25;

const midi = (n) => 440 * 2 ** ((n - 69) / 12);

// [bass root, chord voicing] per bar. Smooth voice leading, all diatonic to C.
const PROGRESSION = [
  [41, [57, 60, 64, 67]], // Fmaj9   (F | A C E G)
  [40, [55, 59, 62, 69]], // Em11    (E | G B D A)
  [38, [53, 57, 60, 64]], // Dm9     (D | F A C E)
  [36, [52, 55, 59, 62]], // Cmaj9   (C | E G B D)
];
// C major pentatonic, two octaves up: bells and hover pings.
const BELLS = [72, 74, 76, 79, 81, 84, 86, 88];

// 16-step patterns (1 = hit). Kick: 1, the "and" of 2, 3-and-a-bit.
const KICK = [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0];
const SNARE = [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0];
const HAT = [1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0];

export function createAudioController() {
  let actx = null;
  let master = null;
  let analyser = null;
  let fdata = null;
  let keysBus = null;
  let duck = null;
  let drumBus = null;
  let reverbSend = null;
  let noise = null;
  let timer = null;
  let suspendTimer = null;
  let nextTime = 0;
  let step = 0;
  let soundOn = false;
  let base = 0;
  let spike = 0;

  function makeImpulse(seconds, decay) {
    const length = Math.floor(actx.sampleRate * seconds);
    const buffer = actx.createBuffer(2, length, actx.sampleRate);
    for (let ch = 0; ch < 2; ch++) {
      const data = buffer.getChannelData(ch);
      for (let i = 0; i < length; i++) {
        data[i] = (Math.random() * 2 - 1) * (1 - i / length) ** decay;
      }
    }
    return buffer;
  }

  function makeNoise() {
    const buffer = actx.createBuffer(1, actx.sampleRate, actx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
    return buffer;
  }

  function ensureAudio() {
    if (actx) return true;
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return false;
    actx = new AudioCtx();

    master = actx.createGain();
    master.gain.value = 0;
    const comp = actx.createDynamicsCompressor();
    comp.threshold.value = -20;
    comp.ratio.value = 3;
    comp.attack.value = 0.01;
    comp.release.value = 0.25;
    const warmth = actx.createBiquadFilter();
    warmth.type = "lowpass";
    warmth.frequency.value = 9000;
    analyser = actx.createAnalyser();
    analyser.fftSize = 64;
    fdata = new Uint8Array(analyser.frequencyBinCount);

    comp.connect(warmth);
    warmth.connect(master);
    master.connect(analyser);
    analyser.connect(actx.destination);

    const reverb = actx.createConvolver();
    reverb.buffer = makeImpulse(2.8, 2.6);
    const reverbReturn = actx.createGain();
    reverbReturn.gain.value = 0.38;
    reverbSend = actx.createGain();
    reverbSend.connect(reverb);
    reverb.connect(reverbReturn);
    reverbReturn.connect(comp);

    // Keys go through a gentle lowpass and the sidechain "duck" gain.
    const keysTone = actx.createBiquadFilter();
    keysTone.type = "lowpass";
    keysTone.frequency.value = 2400;
    keysTone.Q.value = 0.3;
    duck = actx.createGain();
    keysBus = actx.createGain();
    keysBus.gain.value = 0.9;
    keysBus.connect(keysTone);
    keysTone.connect(duck);
    duck.connect(comp);
    duck.connect(reverbSend);

    drumBus = actx.createGain();
    drumBus.gain.value = 0.85;
    drumBus.connect(comp);

    noise = makeNoise();
    return true;
  }

  // --- instruments ------------------------------------------------------------

  function epiano(note, t, velocity, length) {
    const f = midi(note);
    const out = actx.createGain();
    const peak = 0.055 * velocity;
    out.gain.setValueAtTime(0, t);
    out.gain.linearRampToValueAtTime(peak, t + 0.012);
    out.gain.exponentialRampToValueAtTime(peak * 0.35, t + 0.9);
    out.gain.setTargetAtTime(0.0001, t + length, 0.35);
    // Fundamental + soft bell-like partial = classic Rhodes colour.
    [
      [f, "sine", 1],
      [f * 2, "triangle", 0.18],
      [f * 3.01, "sine", 0.06],
    ].forEach(([freq, type, gain]) => {
      const osc = actx.createOscillator();
      osc.type = type;
      osc.frequency.value = freq;
      osc.detune.value = (Math.random() - 0.5) * 6; // slight analogue drift
      const g = actx.createGain();
      g.gain.value = gain;
      osc.connect(g);
      g.connect(out);
      osc.start(t);
      osc.stop(t + length + 2);
    });
    // Gentle tremolo, the electric-piano shimmer.
    const trem = actx.createOscillator();
    trem.frequency.value = 4.2;
    const tremDepth = actx.createGain();
    tremDepth.gain.value = peak * 0.12;
    trem.connect(tremDepth);
    tremDepth.connect(out.gain);
    trem.start(t);
    trem.stop(t + length + 2);
    out.connect(keysBus);
  }

  function bass(note, t, length) {
    const osc = actx.createOscillator();
    osc.type = "sine";
    osc.frequency.value = midi(note);
    const g = actx.createGain();
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(0.22, t + 0.02);
    g.gain.setTargetAtTime(0.0001, t + length * 0.8, 0.12);
    osc.connect(g);
    g.connect(drumBus);
    osc.start(t);
    osc.stop(t + length + 1);
  }

  function kick(t) {
    const osc = actx.createOscillator();
    osc.type = "sine";
    osc.frequency.setValueAtTime(130, t);
    osc.frequency.exponentialRampToValueAtTime(42, t + 0.14);
    const g = actx.createGain();
    g.gain.setValueAtTime(0.55, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.45);
    osc.connect(g);
    g.connect(drumBus);
    osc.start(t);
    osc.stop(t + 0.5);
    // Sidechain: keys dip under the kick and swell back.
    duck.gain.cancelScheduledValues(t);
    duck.gain.setValueAtTime(0.45, t);
    duck.gain.setTargetAtTime(1, t + 0.02, 0.12);
  }

  function noiseHit(t, { type, freq, q, gain, decay }) {
    const src = actx.createBufferSource();
    src.buffer = noise;
    const filter = actx.createBiquadFilter();
    filter.type = type;
    filter.frequency.value = freq;
    filter.Q.value = q;
    const g = actx.createGain();
    g.gain.setValueAtTime(gain, t);
    g.gain.exponentialRampToValueAtTime(0.0001, t + decay);
    src.connect(filter);
    filter.connect(g);
    g.connect(drumBus);
    src.start(t, Math.random() * 0.5);
    src.stop(t + decay + 0.05);
    return g;
  }

  function snare(t) {
    const g = noiseHit(t, { type: "bandpass", freq: 1900, q: 0.8, gain: 0.16, decay: 0.22 });
    g.connect(reverbSend);
    const body = actx.createOscillator();
    body.type = "triangle";
    body.frequency.setValueAtTime(190, t);
    body.frequency.exponentialRampToValueAtTime(140, t + 0.08);
    const bg = actx.createGain();
    bg.gain.setValueAtTime(0.07, t);
    bg.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);
    body.connect(bg);
    bg.connect(drumBus);
    body.start(t);
    body.stop(t + 0.15);
  }

  function hat(t, velocity) {
    noiseHit(t, { type: "highpass", freq: 7500, q: 0.5, gain: 0.035 * velocity, decay: 0.05 });
  }

  function bell(note, t, gainValue = 0.05) {
    const f = midi(note);
    const out = actx.createGain();
    out.gain.setValueAtTime(0, t);
    out.gain.linearRampToValueAtTime(gainValue, t + 0.008);
    out.gain.exponentialRampToValueAtTime(0.0001, t + 1.6);
    [
      [f, 1],
      [f * 2.76, 0.25],
    ].forEach(([freq, gain]) => {
      const osc = actx.createOscillator();
      osc.type = "sine";
      osc.frequency.value = freq;
      const g = actx.createGain();
      g.gain.value = gain;
      osc.connect(g);
      g.connect(out);
      osc.start(t);
      osc.stop(t + 1.7);
    });
    out.connect(reverbSend);
    out.connect(keysBus);
  }

  // --- sequencer ----------------------------------------------------------------

  function scheduleStep(s, t) {
    const inBar = s % 16;
    const bar = Math.floor(s / 16);
    const [root, chord] = PROGRESSION[bar % PROGRESSION.length];
    const barLength = STEP * 16;

    if (inBar === 0) {
      chord.forEach((n, i) => epiano(n, t + i * 0.012, 0.9, barLength * 0.55)); // soft strum
      bass(root, t, STEP * 6);
    }
    // Syncopated re-strike of the upper voices on the "and" of 3 (every other bar).
    if (inBar === 10 && bar % 2 === 1) {
      chord.slice(1).forEach((n, i) => epiano(n, t + i * 0.01, 0.55, STEP * 5));
    }
    if (inBar === 10) bass(root + 7, t, STEP * 3); // walk up to the fifth

    if (KICK[inBar]) kick(t);
    if (SNARE[inBar]) snare(t);
    if (HAT[inBar]) hat(t, inBar % 4 === 0 ? 1 : 0.6 + Math.random() * 0.3);

    // Sparse melody: about one bell every bar or two, on off-beats.
    if (inBar % 4 === 2 && Math.random() < 0.18) {
      bell(BELLS[Math.floor(Math.random() * BELLS.length)], t, 0.035);
    }
  }

  function tick() {
    while (nextTime < actx.currentTime + LOOKAHEAD) {
      const swing = step % 2 === 1 ? STEP * SWING : 0;
      scheduleStep(step, nextTime + swing);
      nextTime += STEP;
      step += 1;
    }
  }

  function startSequencer() {
    if (timer) return;
    nextTime = actx.currentTime + 0.08;
    step = 0;
    timer = setInterval(tick, TICK_MS);
  }

  function stopSequencer() {
    clearInterval(timer);
    timer = null;
  }

  // --- public API ----------------------------------------------------------------

  function setSound(on, onStateChange) {
    if (on) {
      if (!ensureAudio()) return;
      clearTimeout(suspendTimer);
      actx.resume();
      startSequencer();
      master.gain.cancelScheduledValues(actx.currentTime);
      master.gain.setTargetAtTime(0.42, actx.currentTime, 0.6);
    } else if (actx) {
      master.gain.cancelScheduledValues(actx.currentTime);
      master.gain.setTargetAtTime(0, actx.currentTime, 0.2);
      // Stop scheduling and free the CPU once the fade-out has finished.
      suspendTimer = setTimeout(() => {
        stopSequencer();
        actx.suspend();
      }, 1200);
    }
    soundOn = on;
    if (onStateChange) onStateChange(on);
  }

  function ping(i) {
    if (!soundOn || !actx) return;
    bell(BELLS[Math.abs(i) % BELLS.length], actx.currentTime, 0.06);
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
