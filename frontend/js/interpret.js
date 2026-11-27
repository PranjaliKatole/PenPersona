/* ============================================
   Turns the raw numbers in `features` (from feature_extraction.py)
   into the label + percentage each Feature Analysis row shows.

   The 0–1 normalizations below are deliberately copied from
   rules.py's score_traits() so the % shown here agrees with the
   numbers actually driving the trait scores, instead of using a
   second, disconnected scale.

   ALL THRESHOLDS ARE TUNABLE — your own build notes already flag
   these as educated guesses from a single test photo. Adjust the
   cutoffs below once you've tested on more handwriting samples.
   ============================================ */

function clamp01(v) {
  return Math.max(0, Math.min(1, v));
}

function interpretFeatures(features) {
  const size = features.size.avg_height_ratio;
  const gap = features.spacing.avg_gap_ratio;
  const dev = features.baseline.deviation_ratio;
  const rawSlant = features.slant.avg_slant_degrees;

  // --- Size --------------------------------------------------
  // mirrors rules.py: big = clamp((size - 0.03) / 0.03)
  const big = clamp01((size - 0.03) / 0.03);
  let sizeLabel;
  if (big > 0.66) sizeLabel = "Large";
  else if (big > 0.3) sizeLabel = "Medium to large";
  else sizeLabel = "Compact";

  // --- Spacing -------------------------------------------------
  // mirrors rules.py: wide = clamp((gap - 0.4) / 1.2)
  const wide = clamp01((gap - 0.4) / 1.2);
  let spacingLabel, spacingPct;
  if (wide > 0.62) { spacingLabel = "Wide spacing"; spacingPct = wide; }
  else if (wide < 0.38) { spacingLabel = "Tight spacing"; spacingPct = 1 - wide; }
  else { spacingLabel = "Moderate spacing"; spacingPct = 0.5 + Math.abs(wide - 0.5); }

  // --- Baseline (steadiness) ------------------------------------
  // mirrors rules.py: messy = clamp(dev / 0.8), neat = 1 - messy
  const messy = clamp01(dev / 0.8);
  const neat = 1 - messy;
  let baselineLabel;
  if (neat > 0.7) baselineLabel = "Generally steady";
  else if (neat > 0.4) baselineLabel = "Somewhat wavering";
  else baselineLabel = "Uneven";

  // --- Slant -----------------------------------------------------
  // rules.py negates the raw value: positive = leans right.
  const rightLean = -rawSlant;
  const rightScore = clamp01(rightLean / 20);
  const leftScore = clamp01(-rightLean / 20);
  const uprightScore = 1 - clamp01(Math.abs(rightLean) / 20);

  let slantLabel, slantPct;
  if (rightLean > 15) { slantLabel = "Strongly right leaning"; slantPct = rightScore; }
  else if (rightLean > 5) { slantLabel = "Slightly right leaning"; slantPct = rightScore; }
  else if (rightLean < -15) { slantLabel = "Strongly left leaning"; slantPct = leftScore; }
  else if (rightLean < -5) { slantLabel = "Slightly left leaning"; slantPct = leftScore; }
  else { slantLabel = "Upright"; slantPct = uprightScore; }

  return {
    slant:    { label: slantLabel, pct: Math.round(slantPct * 100) },
    spacing:  { label: spacingLabel, pct: Math.round(spacingPct * 100) },
    size:     { label: sizeLabel, pct: Math.round(big * 100) },
    baseline: { label: baselineLabel, pct: Math.round(neat * 100) },
  };
}

const TRAIT_ORDER = ["confident", "organized", "warm", "independent", "expressive", "reserved"];

function traitLabel(key) {
  return key.charAt(0).toUpperCase() + key.slice(1);
}