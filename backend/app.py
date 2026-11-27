import os
import uuid
from flask import Flask, request, jsonify, send_from_directory

from cv_pipeline import preprocess_image
from feature_extraction import extract_features
from rules import pick_trait
from gemini_read import generate_read

BASE = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE, "uploads")
FRONTEND_DIR = os.path.join(BASE, "..", "frontend")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

ALLOWED = {".jpg", ".jpeg", ".png", ".webp"}

DOODLES = {
    "confident": "wink",
    "organized": "neat",
    "warm": "heart_eyes",
    "independent": "star_eyes",
    "expressive": "open_mouth",
    "reserved": "closed_smile",
}


@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("image") or request.files.get("file")
    if not file or not file.filename:
        return jsonify({"error": "No image uploaded."}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED:
        return jsonify({"error": "Please upload a JPG, PNG or WEBP photo."}), 400

    path = os.path.join(UPLOAD_DIR, uuid.uuid4().hex + ext)
    file.save(path)

    try:
        # --- optional: your input_validator check goes here (see note below) ---

        binary = preprocess_image(path)
        features = extract_features(binary)

        if features["meta"]["lines_detected"] == 0:
            return jsonify({"error": "Couldn't find handwriting in this photo. Try a clearer, well-lit shot."}), 422

        trait, scores = pick_trait(features)
        text, source = generate_read(trait, scores, features)

        return jsonify({
            "features": features,
            "trait": trait,
            "scores": scores,
            "personality_read": text,
            "doodle": DOODLES[trait],
            "source": source,
        })
    except Exception as e:
        print("analyze failed:", repr(e))
        return jsonify({"error": "Something went wrong analyzing that image."}), 500
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


if __name__ == "__main__":
    app.run(debug=True)