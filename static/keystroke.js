// keystroke.js
// Captures per-key press/release timings and stores them into a hidden input (#timings).
// Works with register & login forms which include <input data-keystroke="true"> and a hidden #timings input.

(function () {
  // internal state
  let keystrokes = [];
  let keyDownStacks = {}; // key -> stack of press times (handles repeated same-key presses)
  let lastReleaseTime = null;
  let composing = false; // IME composition flag

  const IGNORE_KEYS = new Set([
    "Shift", "Control", "Alt", "Meta", "CapsLock", "Tab", "Escape",
    "ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End",
    "PageUp","PageDown","Insert", "ContextMenu"
  ]);

  function isTargetPasswordInput() {
    const el = document.activeElement;
    return el && (el.type === 'password' || el.dataset.keystroke === "true");
  }

  // handle composition (IME) to avoid noisy events
  document.addEventListener('compositionstart', () => { composing = true; });
  document.addEventListener('compositionend', () => { composing = false; });

  // block paste into password field (optional but often desired)
  document.addEventListener('paste', (e) => {
    const el = document.activeElement;
    if (el && (el.type === 'password' || el.dataset.keystroke === "true")) {
      e.preventDefault();
      console.warn("Paste blocked in password field for keystroke capture.");
    }
  });

  document.addEventListener('keydown', (e) => {
    if (composing) return;
    if (IGNORE_KEYS.has(e.key)) return;
    if (!isTargetPasswordInput()) return;

    const now = performance.now();

    // Using stack to support same key pressed repeatedly before release
    if (!keyDownStacks[e.key]) keyDownStacks[e.key] = [];
    keyDownStacks[e.key].push(now);
  }, true); // capture phase to reliably get keydown

  document.addEventListener('keyup', (e) => {
    if (composing) return;
    if (IGNORE_KEYS.has(e.key)) return;
    if (!isTargetPasswordInput()) return;

    const now = performance.now();
    const stack = keyDownStacks[e.key];
    const press_time = (stack && stack.length) ? stack.pop() : now;
    const release_time = now;
    const duration = Math.max(0, release_time - press_time);
    const flight_time = lastReleaseTime ? Math.max(0, press_time - lastReleaseTime) : 0;

    // push a keystroke record
    keystrokes.push({
      key: e.key,
      press_time: Math.round(press_time),      // rounded to ms
      release_time: Math.round(release_time),
      duration: Math.round(duration),
      flight_time: Math.round(flight_time),
      timestamp: new Date().toISOString()
    });

    lastReleaseTime = release_time;

    // small debug log (remove or comment out in final demo if noisy)
    // console.debug("Keystroke captured:", keystrokes[keystrokes.length - 1]);
  }, true);

  // Called from form onsubmit to serialize keystrokes into hidden input
  window.prepareKeystrokesForSubmit = function () {
    const el = document.getElementById('timings');
    if (!el) {
      console.error("prepareKeystrokesForSubmit: hidden input #timings not found.");
      return true; // don't block submit, but backend will see empty timings
    }
    el.value = JSON.stringify(keystrokes);
    console.info("Keystrokes packaged for submit:", keystrokes.length, "events");
    return true; // allow form submission
  };

  // Reset captured keystrokes (useful between attempts)
  window.resetKeystrokes = function () {
    keystrokes = [];
    keyDownStacks = {};
    lastReleaseTime = null;
    console.info("Keystroke buffer reset.");
  };

  // Optional helper: expose a function to get captured keystrokes (for debugging)
  window._getCapturedKeystrokes = function () {
    return keystrokes.slice(); // return a shallow copy
  };

})();
