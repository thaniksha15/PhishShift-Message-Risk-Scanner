
from pathlib import Path
import re

import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "cleaned_messages.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_PATH = MODEL_DIR / "phishshift_model.pkl"
REPORT_DIR = BASE_DIR / "reports"


# Simple rules-based baseline.
# These rules are only heuristic indicators, not proof of phishing.
SUSPICIOUS_PATTERNS = [
    r"\bclaim your (?:prize|reward|cash)\b",
    r"\byou have won\b",
    r"\byou.ve won\b",
    r"\bcongratulations\b",
    r"\bfree entry\b",
    r"\bselected (?:as )?(?:a )?winner\b",
    r"\bcall now\b",
    r"\bverify your account\b",
    r"\baccount suspended\b",
    r"\bconfirm your password\b",
    r"\bbank details\b",
    r"\bclick (?:here|this link)\b",
    r"\blimited time offer\b",
    r"\bcash reward\b",
    r"\bclaim now\b",
    r"\bprize\b",
    r"\bwon a prize\b",
]


def rules_based_predict(message):
    """Return spam if any configured suspicious pattern matches."""
    text = str(message).lower()

    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, text):
            return "spam"

    return "legitimate"


def calculate_metrics(y_true, y_pred):
    return {
        "Accuracy": round(accuracy_score(y_true, y_pred), 4),
        "Spam Precision": round(
            precision_score(
                y_true, y_pred, pos_label="spam", zero_division=0
            ),
            4,
        ),
        "Spam Recall": round(
            recall_score(
                y_true, y_pred, pos_label="spam", zero_division=0
            ),
            4,
        ),
        "Spam F1-score": round(
            f1_score(
                y_true, y_pred, pos_label="spam", zero_division=0
            ),
            4,
        ),
    }


def evaluate_method(name, y_test, predictions):
    metrics = calculate_metrics(y_test, predictions)

    print("\n" + "=" * 55)
    print("Method:", name)

    for metric, value in metrics.items():
        print(f"{metric}: {value}")

    print("\nConfusion Matrix")
    print("Rows = actual, columns = predicted")
    print("Label order: legitimate, spam")
    print(
        confusion_matrix(
            y_test,
            predictions,
            labels=["legitimate", "spam"],
        )
    )

    print("\nClassification Report")
    print(
        classification_report(
            y_test,
            predictions,
            labels=["legitimate", "spam"],
            zero_division=0,
        )
    )

    return {"Method": name, **metrics}


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    data = pd.read_csv(DATA_PATH)

    required_columns = {"message", "label"}
    if not required_columns.issubset(data.columns):
        raise ValueError(
            "Dataset must contain 'message' and 'label' columns."
        )

    # Clean the dataset.
    data = data.dropna(subset=["message", "label"]).copy()
    data["message"] = data["message"].astype(str).str.strip()
    data["label"] = (
        data["label"].astype(str).str.strip().str.lower()
    )

    data = data[
        (data["message"] != "")
        & data["label"].isin(["ham", "spam"])
    ].copy()

    data = data.drop_duplicates(
        subset=["label", "message"]
    ).copy()

    # Remove messages that have conflicting labels.
    conflicting = (
        data.groupby("message")["label"].nunique()
    )
    conflicting_messages = conflicting[conflicting > 1].index
    data = data[~data["message"].isin(conflicting_messages)].copy()

    data["label"] = data["label"].map({
        "ham": "legitimate",
        "spam": "spam",
    })

    print("DATASET AUDIT")
    print("Total messages:", len(data))
    print("\nLabel distribution:")
    print(data["label"].value_counts().to_string())

    # Fixed random split for reproducibility.
    # This is a random split, not campaign-separated testing.
    X_train, X_test, y_train, y_test = train_test_split(
        data["message"],
        data["label"],
        test_size=0.20,
        random_state=42,
        stratify=data["label"],
    )

    print("\nTraining messages:", len(X_train))
    print("Testing messages:", len(X_test))

    results = []
    trained_models = {}

    # Method 1: Rules-based baseline.
    rules_predictions = X_test.apply(rules_based_predict)
    results.append(
        evaluate_method(
            "Rules-Based Detection",
            y_test,
            rules_predictions,
        )
    )

    # Methods 2 and 3: Machine learning models.
    classifiers = {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Multinomial Naive Bayes": MultinomialNB(),
    }

    for name, classifier in classifiers.items():
        model = Pipeline([
            (
                "tfidf",
                TfidfVectorizer(ngram_range=(1, 2)),
            ),
            ("classifier", classifier),
        ])

        model.fit(X_train, y_train)
        predictions = model.predict(X_test)

        results.append(
            evaluate_method(name, y_test, predictions)
        )

        trained_models[name] = model

    # Compare the methods.
    comparison = pd.DataFrame(results)

    print("\n" + "=" * 55)
    print("MODEL COMPARISON")
    print(comparison.to_string(index=False))

    # Select the best ML model using spam F1-score.
    # Rules-based detection is evaluated separately.
    ml_results = comparison[
        comparison["Method"].isin(trained_models.keys())
    ]
    best_name = ml_results.sort_values(
        by="Spam F1-score",
        ascending=False,
    ).iloc[0]["Method"]

    best_model = trained_models[best_name]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Save the complete TF-IDF + classifier pipeline.
    joblib.dump(best_model, MODEL_PATH)

    # Save comparison results for the project report.
    comparison_path = REPORT_DIR / "model_comparison.csv"
    comparison.to_csv(comparison_path, index=False)

    print("\nSelected ML model:", best_name)
    print("Saved model to:", MODEL_PATH)
    print("Saved comparison report to:", comparison_path)
    print("\nIMPORTANT:")
    print(
        "This evaluation uses a random SMS dataset split. "
        "It is not campaign-separated testing."
    )
    print(
        "This project is an SMS spam classification baseline, "
        "not a validated phishing-email detection system."
    )


if __name__ == "__main__":
    main()
