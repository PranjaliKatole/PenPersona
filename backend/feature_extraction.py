import cv2
import numpy as np

MIN_BLOB_AREA = 40        # ignore specks
RIGHT_TRIM_RATIO = 0.85   # cut spiral-binding strip on the right
MIN_BLOBS_PER_LINE = 6    # a "line" with fewer letters = noise, dropped


def _crop_binding(binary):
    h, w = binary.shape[:2]
    return binary[:, :int(w * RIGHT_TRIM_RATIO)]


def _get_letter_blobs(binary):
    img_h = binary.shape[0]
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        if cv2.contourArea(c) < MIN_BLOB_AREA:
            continue
        x, y, w, h = cv2.boundingRect(c)
        if h > img_h * 0.12:
            continue
        aspect = h / w if w > 0 else 999
        if aspect > 6 or aspect < 0.12:
            continue
        boxes.append((x, y, w, h))
    return boxes


def _group_into_lines(boxes, binary=None):
    """Histogram of letter y-centers -> each text line is one peak."""
    if not boxes:
        return []

    med_h = float(np.median([b[3] for b in boxes]))
    boxes = [b for b in boxes if 0.4 * med_h <= b[3] <= 2.5 * med_h]
    if not boxes:
        return []

    centers = np.array([y + h / 2 for (x, y, w, h) in boxes])

    hist = np.zeros(int(centers.max()) + 2)
    for c in centers:
        hist[int(c)] += 1
    sigma = max(3.0, 0.3 * med_h)
    k = np.arange(-int(3 * sigma), int(3 * sigma) + 1)
    smooth = np.convolve(hist, np.exp(-0.5 * (k / sigma) ** 2), mode="same")

    # pick peaks, at least 1.5 letter-heights apart
    min_dist = 1.5 * med_h
    peaks = []
    for idx in np.argsort(smooth)[::-1]:
        if smooth[idx] < 0.15 * smooth.max():
            break
        if all(abs(idx - p) >= min_dist for p in peaks):
            peaks.append(int(idx))
    peaks.sort()

    groups = {p: [] for p in peaks}
    for box, c in zip(boxes, centers):
        nearest = min(peaks, key=lambda p: abs(c - p))
        groups[nearest].append(box)

    lines = [g for g in groups.values() if len(g) >= MIN_BLOBS_PER_LINE]
    for line in lines:
        line.sort(key=lambda b: b[0])
    lines.sort(key=lambda l: np.mean([b[1] for b in l]))
    return lines


def _compute_size(boxes, image_height):
    if not boxes:
        return {"avg_height_px": 0.0, "avg_height_ratio": 0.0}
    avg = float(np.mean([b[3] for b in boxes]))
    return {"avg_height_px": round(avg, 2),
            "avg_height_ratio": round(avg / image_height, 4)}


def _compute_spacing(lines, avg_h):
    gaps = []
    for line in lines:
        for i in range(len(line) - 1):
            x, _, w, _ = line[i]
            gap = line[i + 1][0] - (x + w)
            if gap > 0:
                gaps.append(gap)
    if not gaps:
        return {"avg_gap_px": 0.0, "avg_gap_ratio": 0.0}
    avg = float(np.mean(gaps))
    return {"avg_gap_px": round(avg, 2),
            "avg_gap_ratio": round(avg / avg_h if avg_h else 0.0, 3)}


def _compute_baseline(lines, avg_h):
    devs = []
    for line in lines:
        if len(line) < 2:
            continue
        bottoms = [y + h for (x, y, w, h) in line]
        med = np.median(bottoms)
        devs.extend(abs(b - med) for b in bottoms)
    if not devs:
        return {"deviation_px": 0.0, "deviation_ratio": 0.0}
    avg = float(np.median(devs))
    return {"deviation_px": round(avg, 2),
            "deviation_ratio": round(avg / avg_h if avg_h else 0.0, 3)}


def _compute_slant(binary, boxes):
    # Only look inside detected letters, so the margin line / ruled lines
    # can't skew the angle.
    mask = np.zeros_like(binary)
    for (x, y, w, h) in boxes:
        mask[y:y + h, x:x + w] = 255
    letters_only = cv2.bitwise_and(binary, mask)

    segments = cv2.HoughLinesP(letters_only, rho=1, theta=np.pi / 180,
                               threshold=15, minLineLength=15, maxLineGap=3)
    if segments is None:
        return {"avg_slant_degrees": 0.0, "segments_used": 0}

    angles = []
    for seg in segments:
        x1, y1, x2, y2 = seg.reshape(-1)
        if y2 < y1:
            x1, y1, x2, y2 = x2, y2, x1, y1
        dy = y2 - y1
        if dy == 0:
            continue
        a = np.degrees(np.arctan2(x2 - x1, dy))
        if abs(a) <= 45:
            angles.append(a)

    if not angles:
        return {"avg_slant_degrees": 0.0, "segments_used": 0}
    return {"avg_slant_degrees": round(float(np.mean(angles)), 2),
            "segments_used": len(angles)}


def extract_features(binary):
    binary = _crop_binding(binary)
    image_height = binary.shape[0]

    all_boxes = _get_letter_blobs(binary)
    lines = _group_into_lines(all_boxes)
    boxes = [b for line in lines for b in line]   # only real-line letters
    avg_h = float(np.mean([b[3] for b in boxes])) if boxes else 0.0

    return {
        "size": _compute_size(boxes, image_height),
        "spacing": _compute_spacing(lines, avg_h),
        "baseline": _compute_baseline(lines, avg_h),
        "slant": _compute_slant(binary, boxes),
        "meta": {"letters_detected": len(boxes), "lines_detected": len(lines)},
    }