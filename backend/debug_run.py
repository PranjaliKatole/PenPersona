import traceback
import cv2
from cv_pipeline import preprocess_image
from feature_extraction import extract_features, _get_letter_blobs, _group_into_lines, _crop_binding
from rules import pick_trait
from gemini_read import generate_read

IMAGE_PATH = r"C:\Users\katol\Downloads\WhatsApp Image 2026-09-23 at 7.30.59 PM.jpeg"

try:
    binary = preprocess_image(IMAGE_PATH)
    print("preprocess_image OK, shape:", binary.shape)

    # 1) features
    features = extract_features(binary)
    print("\nFEATURES:", features)

    # 2) rule table -> trait
    trait, scores = pick_trait(features)
    print("\nTOP TRAIT:", trait)
    for name, val in sorted(scores.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {name:12s} {val}")

    # 3) Gemini personality read
    text, source = generate_read(trait, scores, features)
    print("\nSOURCE:", source, "\n")
    print(text)

    # 4) debug image of detected lines
    binary_cropped = _crop_binding(binary)
    boxes = _get_letter_blobs(binary_cropped)
    lines = _group_into_lines(boxes, binary_cropped)

    vis = cv2.cvtColor(binary_cropped, cv2.COLOR_GRAY2BGR)
    for line in lines:
        ys = [y for (x, y, w, h) in line] + [y + h for (x, y, w, h) in line]
        cv2.line(vis, (0, min(ys)), (vis.shape[1], min(ys)), (0, 0, 255), 2)
        cv2.line(vis, (0, max(ys)), (vis.shape[1], max(ys)), (0, 255, 0), 2)
    cv2.imwrite("debug_lines.png", vis)
    print("\nSaved debug_lines.png -", len(lines), "bands drawn")

except Exception:
    traceback.print_exc()