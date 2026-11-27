"""
input_validator.py
PenPersona — lightweight "is this even a handwriting photo" gate.

Honest scope: this does NOT detect AI-generated handwriting vs real
human handwriting — that's a genuinely hard research problem, not
solvable reliably in this project's timeframe, and this file doesn't
pretend to. What it DOES catch: someone uploading a screenshot of
typed/digital text, a random photo, or a blank page.

Not wired into Flask yet — exposes one function, validate_input(),
to be called before cv_pipeline.preprocess_image() once you ask for it.
"""

import cv2
import numpy as np


def _background_lightness_ratio(gray: np.ndarray) -> float:
    _, split = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    background_ratio = np.sum(split == 255) / split.size
    return background_ratio


def _color_saturation_score(bgr: np.ndarray) -> float:
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    return float(np.mean(saturation)) / 255.0


def _stroke_width_uniformity(gray: np.ndarray) -> float:
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    dist = cv2.distanceTransform(binary, cv2.DIST_L2, 5)
    ink_distances = dist[dist > 0]

    if ink_distances.size < 50:
        return 1.0

    mean_val = np.mean(ink_distances)
    std_val = np.std(ink_distances)
    if mean_val == 0:
        return 1.0
    coefficient_of_variation = std_val / mean_val
    return float(coefficient_of_variation)


def validate_input(image_path: str) -> dict:
    """
    Runs 3 cheap checks and returns a verdict + individual scores.
    """
    bgr = cv2.imread(image_path)
    if bgr is None:
        return {
            "is_valid": False,
            "reason": "Could not read image file.",
            "scores": {},
        }

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    bg_ratio = _background_lightness_ratio(gray)
    saturation = _color_saturation_score(bgr)
    stroke_cv = _stroke_width_uniformity(gray)

    scores = {
        "background_lightness": round(bg_ratio, 3),
        "saturation": round(saturation, 3),
        "stroke_uniformity": round(stroke_cv, 3),
    }

    if bg_ratio < 0.20:
        return {
            "is_valid": False,
            "reason": "Image doesn't look like a photo of paper — too little "
                      "light background. Please upload a clear photo of "
                      "handwriting on paper.",
            "scores": scores,
        }

    if saturation > 0.25:
        return {
            "is_valid": False,
            "reason": "Image looks too colorful to be handwriting on paper "
                      "(e.g. a selfie or photo of a scene). Please upload a "
                      "photo of handwriting instead.",
            "scores": scores,
        }

    if stroke_cv < 0.15:
        return {
            "is_valid": False,
            "reason": "This looks like printed or digital text rather than "
                      "handwriting (stroke width is too uniform). Please "
                      "upload a photo of actual handwriting.",
            "scores": scores,
        }

    return {
        "is_valid": True,
        "reason": "Looks like a handwriting photo.",
        "scores": scores,
    }