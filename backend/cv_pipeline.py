"""
cv_pipeline.py
PenPersona — Step 4: OpenCV Preprocessing

Scope (deliberately limited to exactly 3 steps):
  1. Deskew            — straighten a tilted photo
  2. Adaptive threshold — clean ink vs paper despite uneven lighting
  3. Denoise            — remove small specks/grain without eroding real strokes

This file does NOT do feature extraction, trait logic, or Gemini calls.
It exposes one function, preprocess_image(), that later gets imported into app.py.
Not wired into Flask yet — that happens only when explicitly requested.
"""

import cv2
import numpy as np


def deskew(gray: np.ndarray) -> np.ndarray:
    """
    Straightens a tilted handwriting photo.

    Why: photos are rarely perfectly flat/straight relative to the camera.
    If we don't fix this, later "slant" measurements (Step 5) would be
    polluted by camera/photo tilt instead of reflecting the writer's
    actual handwriting angle.

    How: threshold roughly to find ink pixels, find the minimum-area
    bounding rectangle around all that ink, read its angle, and rotate
    the whole image to cancel that angle out.
    """
    _, rough_bin = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    coords = np.column_stack(np.where(rough_bin > 0))
    if coords.shape[0] < 20:
        return gray

    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = 90 + angle
    if abs(angle) > 15:
        return gray

    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        gray,
        rotation_matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated


def adaptive_threshold(gray: np.ndarray) -> np.ndarray:
    """
    Converts grayscale to clean black-ink-on-white-paper binary,
    even when lighting is uneven across the page.
    """
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=25,
        C=10,
    )
    return binary


def denoise(binary: np.ndarray) -> np.ndarray:
    """
    Removes small specks/grain that survive thresholding as isolated
    white pixels/blobs, via mild morphological opening.
    """
    kernel = np.ones((2, 2), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    return cleaned


def remove_ruled_lines(binary: np.ndarray) -> np.ndarray:
    """
    Removes horizontal notebook ruling lines while preserving handwriting.
    """
    h, w = binary.shape[:2]

    detect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    line_segments = cv2.morphologyEx(
        binary, cv2.MORPH_OPEN, detect_kernel, iterations=1
    )

    bridge_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (w // 20, 1))
    reconnected_lines = cv2.dilate(line_segments, bridge_kernel, iterations=1)

    line_free = cv2.subtract(binary, reconnected_lines)
    return line_free


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Full Step 4 pipeline, in order: deskew -> adaptive threshold -> denoise -> remove ruled lines.
    Returns the cleaned binary image (ink = white/255, paper = black/0).
    """
    original = cv2.imread(image_path)
    if original is None:
        raise ValueError(f"Could not read image at: {image_path}")

    gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)

    straightened = deskew(gray)
    binary = adaptive_threshold(straightened)
    cleaned = denoise(binary)
    line_free = remove_ruled_lines(cleaned)

    return line_free