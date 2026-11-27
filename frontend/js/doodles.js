/* ============================================
   PenPersona trait images
   Maps each of the 6 traits straight to its illustrated card image,
   matching the exact filenames currently sitting in frontend/images/.
   (Mixed case + one .jpeg is fine on Windows, but if this ever moves to
   a Linux/Mac server, rename these to be consistent — case matters there.)
   ============================================ */

const TRAIT_IMAGES = {
  confident: "images/Confident.png",
  organized: "images/Organized.png",
  warm: "images/Warm.png",
  independent: "images/Independent.png",
  expressive: "images/Expressive.png",
  reserved: "images/reserved.jpeg",
};

// Backend's `doodle` id (wink, neat, heart_eyes, star_eyes, open_mouth,
// closed_smile) still maps 1:1 to a trait — kept so main.js can go
// doodle-id -> trait -> image without needing app.py changes.
const DOODLE_TO_TRAIT = {
  wink: "confident",
  neat: "organized",
  heart_eyes: "warm",
  star_eyes: "independent",
  open_mouth: "expressive",
  closed_smile: "reserved",
};