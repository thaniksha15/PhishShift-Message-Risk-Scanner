from pathlib import Path
from datetime import datetime
from threading import Lock
import re

import joblib
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "phishshift_model.pkl"

# Configuration
ABSTAIN_THRESHOLD = 65.0
MAX_HISTORY = 100

# Load trained model
if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Trained model not found: {MODEL_PATH}\n"
        "Make sure models/phishshift_model.pkl exists."
    )

model = joblib.load(MODEL_PATH)

# Temporary prediction history
prediction_history = []
history_lock = Lock()


def normalize_prediction(value):
    """Convert model labels to standard application labels."""
    label = str(value).strip().lower()

    if label in {"spam", "1", "phishing", "phish"}:
        return "spam"

    if label in {"uncertain", "unknown"}:
        return "uncertain"

    return "legitimate"


def get_confidence(message, model_prediction):
    """Return the probability of the model's predicted class."""
    if not hasattr(model, "predict_proba"):
        return 0.0

    probabilities = model.predict_proba([message])[0]
    classes = list(model.classes_)

    predicted_index = next(
        (
            index
            for index, label in enumerate(classes)
            if normalize_prediction(label) == model_prediction
        ),
        None,
    )

    if predicted_index is None:
        return 0.0

    return round(float(probabilities[predicted_index]) * 100, 2)


def normalize_text(text):
    """Normalize punctuation and spacing for phrase matching."""
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contains_phrase(text, phrase):
    """Check for a complete phrase."""
    normalized_phrase = normalize_text(phrase)
    return f" {normalized_phrase} " in f" {text} "


def find_suspicious_cues(message):
    """Identify suspicious wording for additional review."""
    text = normalize_text(message)
    detected = []

    suspicious_phrases = {
        "free prize": ["free prize", "free gift"],
        "claim your reward": ["claim your reward", "claim reward"],
        "claim your prize": [
            "claim your prize",
            "claim prize",
            "claim your price",
            "claim price",
        ],
        "click here": ["click here"],
        "you have won": ["you have won", "you won"],
        "congratulations": ["congratulations"],
        "verify your account": [
            "verify your account",
            "verify account",
        ],
        "account is suspended": [
            "account is suspended",
            "account has been suspended",
            "account suspended",
        ],
        "urgent action required": [
            "urgent action required",
            "immediate action required",
        ],
        "limited time": ["limited time", "limited time offer"],
        "share your OTP": [
            "send otp",
            "share your otp",
            "share otp",
            "provide your otp",
        ],
        "enter your password": [
            "enter your password",
            "provide your password",
            "share your password",
        ],
        "bank account": ["bank account"],
        "cash prize": ["cash prize"],
    }

    for display_phrase, variations in suspicious_phrases.items():
        if any(
            contains_phrase(text, phrase)
            for phrase in variations
        ):
            detected.append(display_phrase)

    link_instructions = [
        "click the link",
        "click this link",
        "open the link",
        "follow this link",
    ]

    suspicious_context = [
        "claim",
        "reward",
        "prize",
        "price",
        "won",
        "winner",
        "free",
        "verify",
        "account",
        "suspended",
        "urgent",
        "password",
        "otp",
        "bank",
        "limited time",
    ]

    has_link_instruction = any(
        contains_phrase(text, phrase)
        for phrase in link_instructions
    )

    has_suspicious_context = any(
        contains_phrase(text, phrase)
        for phrase in suspicious_context
    )

    if has_link_instruction and has_suspicious_context:
        detected.append("suspicious link instruction")

    return detected


def get_risk_level(prediction, confidence, cues):
    """Assign a preliminary risk indicator."""
    if prediction == "spam":
        return "High"

    if prediction == "uncertain":
        return "Review Required"

    if cues or confidence < ABSTAIN_THRESHOLD:
        return "Review Required"

    return "Low"


def get_statistics():
    """Calculate statistics from current prediction history."""
    total = len(prediction_history)

    spam = sum(
        1 for item in prediction_history
        if item["prediction"] == "spam"
    )

    legitimate = sum(
        1 for item in prediction_history
        if item["prediction"] == "legitimate"
    )

    uncertain = sum(
        1 for item in prediction_history
        if item["prediction"] == "uncertain"
    )

    return {
        "total_checks": total,
        "spam_count": spam,
        "legitimate_count": legitimate,
        "uncertain_count": uncertain,
    }


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({
            "error": "Please enter a message."
        }), 400

    if len(message) > 10000:
        return jsonify({
            "error": (
                "Message is too long. "
                "Maximum length is 10000 characters."
            )
        }), 400

    try:
        # Step 1: Get the model prediction
        raw_prediction = model.predict([message])[0]
        model_prediction = normalize_prediction(raw_prediction)

        # Step 2: Calculate model confidence
        confidence = get_confidence(message, model_prediction)

        # Step 3: Detect suspicious wording
        cues = find_suspicious_cues(message)

        # Step 4: Apply the review rules
        if confidence < ABSTAIN_THRESHOLD or cues:
            prediction = "uncertain"
        else:
            prediction = model_prediction

        # Step 5: Calculate the risk indicator
        risk_level = get_risk_level(
            prediction,
            confidence,
            cues,
        )

        # Step 6: Create a clear review explanation
        if cues:
            review_message = (
                "Suspicious phrases detected. "
                "Please review this message carefully."
            )
        elif confidence < ABSTAIN_THRESHOLD:
            review_message = (
                "The model confidence is low. "
                "Please review this message carefully."
            )
        else:
            review_message = None

        entry = {
            "prediction": prediction,
            "model_prediction": model_prediction,
            "confidence": confidence,
            "message": message,
            "timestamp": datetime.now().strftime(
                "%d %b %Y, %I:%M %p"
            ),
            "risk_level": risk_level,
            "suspicious_cues": cues,
            "review_message": review_message,
        }

        with history_lock:
            prediction_history.insert(0, entry)

            if len(prediction_history) > MAX_HISTORY:
                prediction_history.pop()

            stats = get_statistics()

        return jsonify({
            **entry,
            "stats": stats,
        })

    except Exception:
        app.logger.exception("Prediction failed")

        return jsonify({
            "error": (
                "Unable to analyze this message. "
                "Check the Flask server terminal."
            )
        }), 500


@app.route("/history", methods=["GET"])
def history():
    with history_lock:
        items = [item.copy() for item in prediction_history]
        stats = get_statistics()

    return jsonify({
        "history": items,
        "stats": stats,
    })


@app.route("/history/clear", methods=["POST"])
def clear_history():
    with history_lock:
        prediction_history.clear()
        stats = get_statistics()

    return jsonify({
        "success": True,
        "message": "Prediction history cleared.",
        "history": [],
        "stats": stats,
    })


if __name__ == "__main__":
    app.run(debug=True)
