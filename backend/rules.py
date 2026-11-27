def _clamp(v):
    return max(0.0, min(1.0, v))


def score_traits(features: dict) -> dict:
    size = features["size"]["avg_height_ratio"]
    gap = features["spacing"]["avg_gap_ratio"]
    dev = features["baseline"]["deviation_ratio"]
    slant = -features["slant"]["avg_slant_degrees"]  # positive = leans right

    big = _clamp((size - 0.03) / 0.03)
    wide = _clamp((gap - 0.4) / 1.2)
    tight = 1 - wide
    messy = _clamp(dev / 0.8)
    neat = 1 - messy
    right = _clamp(slant / 20)
    left = _clamp(-slant / 20)
    upright = 1 - _clamp(abs(slant) / 20)

    scores = {
        "confident":   0.5 * big + 0.3 * neat + 0.2 * upright,
        "organized":   0.6 * neat + 0.2 * upright + 0.2 * (1 - abs(wide - 0.5) * 2),
        "warm":        0.6 * right + 0.2 * tight + 0.2 * big,
        "independent": 0.4 * left + 0.3 * wide + 0.3 * upright,
        "expressive":  0.4 * big + 0.3 * messy + 0.3 * right,
        "reserved":    0.4 * (1 - big) + 0.3 * tight + 0.3 * upright,
    }
    return {k: round(v, 3) for k, v in scores.items()}


def pick_trait(features: dict):
    scores = score_traits(features)
    top = max(scores, key=scores.get)
    return top, scores