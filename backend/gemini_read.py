import os
import time
import random

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from google import genai
from google.genai import types

MODELS = ["gemini-flash-lite-latest", "gemini-3.8-flash", "gemini-flash-latest"]   # tried in order
RETRIES = 3

# Flash-Lite gets a much bigger free daily quota (~500-1000 requests/day)
# than gemini-3.8-flash (~20/day as of Sept 2026), so it's listed first
# here for everyday testing. gemini-3.8-flash stays as a fallback for
# when you want the stronger model, e.g. right before your actual demo —
# swap the list order then if you want it as the primary.

# Lower = more consistent/predictable wording across generations.
# Higher = more variety, but quality/structure swings more (this was the
# behaviour you saw: two very different-feeling reads for the same trait).
# 0.75 keeps the structure steady but stops it from being clipped/terse.
TEMPERATURE = 0.75

STYLE_EXAMPLE = """You're someone who needs to talk it out. You feel things deeply, but you also need to understand them with your mind. You like deep conversations, shared jokes, and people who really listen. You get bored with surface-level talk and fake vibes. When someone gives you their full attention, you open up fast. You're good at reading the room, and you notice what people don't say. Words matter to you, more than people know."""


def _describe(features):
    size = features["size"]["avg_height_ratio"]
    gap = features["spacing"]["avg_gap_ratio"]
    dev = features["baseline"]["deviation_ratio"]
    slant = -features["slant"]["avg_slant_degrees"]

    return {
        "letter size": "large" if size > 0.05 else "small" if size < 0.035 else "medium",
        "spacing between letters": "wide" if gap > 0.8 else "tight" if gap < 0.4 else "balanced",
        "line steadiness": "wobbly" if dev > 0.5 else "very steady" if dev < 0.2 else "mostly steady",
        "slant": "leans right" if slant > 7 else "leans left" if slant < -7 else "upright",
    }


def _prompt(trait, scores, features):
    top3 = sorted(scores, key=scores.get, reverse=True)[:3]
    traits = ", ".join(top3)
    desc = "\n".join(f"- {k}: {v}" for k, v in _describe(features).items())
    return f"""Write a personality read for someone, based on their handwriting.

Dominant trait: {trait}
Supporting traits (in order): {traits}
Handwriting observations:
{desc}

STYLE (copy this voice exactly, but write completely NEW content):
\"\"\"{STYLE_EXAMPLE}\"\"\"

Follow this exact 5-beat structure, in order, as ONE flowing paragraph
(no line breaks, no numbering in the output). Give each beat exactly
1-2 sentences — enough to feel specific and unhurried, but do not pad
or add extra examples beyond what's needed:
1. Open with a concrete behaviour that shows the dominant trait in action
   (something they DO, not a description of what they're like).
2. A detail about their habits, space, or how they handle their day-to-day.
3. A line about how they act specifically around other people.
4. One small internal tension: something they want but also guard against
   (e.g. "you want X but also Y").
5. Close with one short, punchy sentence (under 10 words) that lands.

RULES:
- Second person ("You..."), STRICTLY 150-190 words total. This is a hard
  ceiling: count as you write and stop within range — going over 190
  words or under 150 is a failure just like missing a beat.
- Plain sentences. Casual, warm, like a close friend who notices things —
  not a rambling monologue.
- Feel specific: describe behaviours and habits, not adjectives like "you are warm".
- NEVER mention handwriting, graphology, numbers, scores, "traits", or AI.
- No lists, no headings, no emojis, no generic horoscope lines.
- Output only the paragraph, nothing else."""


FALLBACKS = [
    "You notice more than you say. You like things to make sense, and you get uneasy when they don't. Around people you trust, you loosen up fast and it surprises them. You have a way of doing things that works for you, and you don't need anyone to approve of it. Underneath, you care more than you let on. That's just how you are.",
    "You think before you speak, and when you do speak, it means something. You like your own space and your own pace. People find you calm, but your mind is rarely quiet. You want to be understood without having to explain everything. The right person gets all of you.",
]


def generate_read(trait, scores, features):
    """Returns (text, source). Never raises: retries, tries backup model, then template."""

    # Dev switch: put SKIP_GEMINI=1 in .env to save quota while building the frontend
    if os.environ.get("SKIP_GEMINI") == "1":
        return random.choice(FALLBACKS), "skipped"

    prompt = _prompt(trait, scores, features)
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    except Exception as e:
        print("Gemini client failed:", e)
        return random.choice(FALLBACKS), "fallback"

    config = types.GenerateContentConfig(temperature=TEMPERATURE)

    for model in MODELS:
        for attempt in range(RETRIES):
            try:
                resp = client.models.generate_content(
                    model=model, contents=prompt, config=config
                )
                text = (resp.text or "").strip()
                # Flash-Lite tends to write shorter than the bigger models
                # even when asked for 150-190 words — that's normal for a
                # smaller model, not a broken response. 400 chars (~80
                # words) is just a sanity floor to catch truly empty/broken
                # replies, not a way to force Flash-Lite's natural length.
                if len(text) < 400:
                    raise ValueError("response too short")
                return text, "gemini"
            except Exception as e:
                msg = str(e)
                print(f"[{model}] attempt {attempt + 1} failed: {msg[:120]}")
                if "404" in msg or "NOT_FOUND" in msg:
                    break                      # wrong model name, skip to next model
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    break                      # quota gone, retrying won't help
                time.sleep(2 * (attempt + 1))  # 503: wait 2s, 4s, 6s

    return random.choice(FALLBACKS), "fallback"