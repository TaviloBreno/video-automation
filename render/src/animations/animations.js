// render/src/animations/animations.js
// Mapeia data-animation para receitas GSAP oficiais do HyperFrames.

window.HF_ANIMATIONS = {
  "fade-in": (el, tl, at) => {
    tl.from(el, { opacity: 0, duration: 0.4, ease: "power2.out" }, at);
  },

  "slide-up": (el, tl, at) => {
    tl.from(el, { y: 150, opacity: 0, ease: "power4.out", duration: 0.6 }, at);
  },

  "slide-left": (el, tl, at) => {
    tl.from(el, { x: -200, opacity: 0, ease: "power4.out", duration: 0.6 }, at);
  },

  "scale-in": (el, tl, at) => {
    tl.from(el, { scale: 0, opacity: 0, duration: 0.6, ease: "power2.out" }, at);
  },

  "typewriter": (el, tl, at) => {
    // Typewriter simples via clip-path width (sem SplitText para evitar dependência)
    el.style.overflow = "hidden";
    el.style.whiteSpace = "nowrap";
    tl.from(el, { width: 0, duration: 1.2, ease: "steps(20)" }, at);
  },
};