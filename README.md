# PhishShift - Message Risk Scanner

## Machine Learning Powered SMS Spam Detection

PhishShift is a machine learning-based web application that analyzes text messages and identifies potential spam messages and suspicious wording. It provides a prediction, model confidence, risk indicator, suspicious phrases, and prediction history to help users review messages.

**Important:** This project is an SMS spam classification baseline. It is not a validated phishing-email detection system and cannot guarantee that a message is safe.

## Features

- Analyze text messages for potential spam.
- Predict whether a message is legitimate or spam.
- Display model confidence as a percentage.
- Detect suspicious phrases using rule-based checks.
- Flag uncertain or suspicious messages for manual review.
- Display risk indicators.
- Maintain recent prediction history during the current server session.
- Display statistics for total checks, spam, legitimate messages, and messages needing review.
- Compare multiple spam detection methods.
- Generate evaluation reports and visualizations.

## Technologies Used

- Python
- Flask
- Scikit-learn
- Pandas
- Joblib
- HTML
- CSS
- JavaScript
- Matplotlib
- Seaborn

## Machine Learning Models

This project compares three approaches:

1. Rules-Based Detection
2. Logistic Regression with TF-IDF features
3. Multinomial Naive Bayes

Logistic Regression is selected as the final machine learning model based on the current evaluation results.

## Dataset

The project uses a cleaned SMS message dataset containing **5,158 messages**.

| Label | Number of Messages |
|---|---:|
| Legitimate | 4,516 |
| Spam | 642 |
| **Total** | **5,158** |

The dataset is divided into training and testing sets for the random-split evaluation.

- Training messages: 4,126
- Testing messages: 1,032

## Model Evaluation

The current random-split evaluation results are:

| Method | Accuracy | Spam Precision | Spam Recall | Spam F1-score |
|---|---:|---:|---:|---:|
| Rules-Based Detection | 89.44% | 91.30% | 16.41% | 27.81% |
| Logistic Regression | 95.83% | 100% | 66.41% | 79.81% |
| Multinomial Naive Bayes | 93.90% | 100% | 50.78% | 67.36% |

Logistic Regression achieved the highest accuracy and spam F1-score among the three evaluated methods in this random split.

These results come from a random SMS dataset split. They do not demonstrate campaign-separated generalization or validate the application for phishing-email detection.

## Grouped Evaluation

A separate normalized-message grouped split was evaluated to reduce overlap between equivalent messages in the training and testing sets.

| Metric | Result |
|---|---:|
| Training messages | 4,124 |
| Testing messages | 1,032 |
| Shared groups | 0 |
| Accuracy | 96.22% |
| Spam Precision | 98.80% |
| Spam Recall | 68.33% |
| Spam F1-score | 80.79% |

No normalized-message groups were shared between the training and testing sets. This helps reduce duplicate-message leakage. However, this evaluation does not establish generalization to unseen phishing campaigns or prove real-world phishing detection performance.

The random-split and grouped-split results are separate evaluations and should not be treated as the same test.

## Project Structure

```text
PhishShift_Message_Risk_Scanner/
|-- app.py
|-- train.py
|-- evaluate_grouped.py
|-- generate_reports.py
|-- test_false_positives.py
|-- requirements.txt
|-- README.md
|-- data/
|   |-- cleaned_messages.csv
|   |-- SMSSpamCollection
|   |-- PhishingEmailData.csv
|   |-- CEAS_08.csv
|-- models/
|   |-- phishshift_model.pkl
|-- reports/
|   |-- dataset_distribution.png
|   |-- model_comparison.png
|   |-- grouped_confusion_matrix.png
|   |-- logistic_confusion_matrix.png
|   |-- model_comparison.csv
|   |-- grouped_evaluation.csv
|   |-- grouped_test_predictions.csv
|   |-- false_positive_test_results.csv
|   |-- deduplication_proof.csv
|   |-- deduplication_summary.csv
|-- templates/
|   |-- index.html
|-- static/
    |-- style.css
    |-- script.js
```

*Note: This structure lists the main project files and report outputs. Check the actual folders before submission, because generated files may change.*

## Installation and Setup

### 1. Install Python

Install a compatible Python version and ensure Python is available in the terminal.

### 2. Open the Project Folder

Open the `PhishShift_Message_Risk_Scanner` project folder in VS Code.

### 3. Create and Activate a Virtual Environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Train the Model

```powershell
python train.py
```

This trains and compares the models and saves the selected model in the `models` folder.

### 6. Run the Application

```powershell
python app.py
```

### 7. Open the Application

Open this address in your browser:

`http://127.0.0.1:5000`

## How to Use

1. Open the PhishShift web application in your browser.
2. Enter a text message in the input area.
3. Click **Check Message**.
4. Review the prediction and confidence score.
5. Check the risk indicator and suspicious phrases.
6. Review recent analyses in the prediction history.
7. Use the result as guidance for manual review, not as a guarantee of message safety.

## Evaluation Reports

The `reports` folder contains evaluation outputs and visualizations, including:

- `dataset_distribution.png` - displays the dataset label distribution.
- `model_comparison.png` - compares the evaluated detection methods.
- `logistic_confusion_matrix.png` - displays the Logistic Regression confusion matrix.
- `grouped_confusion_matrix.png` - displays the grouped evaluation confusion matrix.
- `model_comparison.csv` - stores model comparison metrics.
- `grouped_evaluation.csv` - stores grouped evaluation metrics.
- `grouped_test_predictions.csv` - stores grouped test predictions.
- `false_positive_test_results.csv` - stores results from the manual test messages.
- `deduplication_proof.csv` and `deduplication_summary.csv` - store duplicate-check evidence.

These reports can be used to explain the project's dataset, evaluation process, and results during a project presentation.

## False-Positive Test

A small manually written test set of 12 messages was used to check how the application handles legitimate and spam-like messages.

The latest test run reported:

- Total test messages: 12
- Legitimate messages: 8
- Spam messages: 4
- Exact-match correct predictions: 9
- Messages requiring review: 3
- False positives: 0
- Spam predicted as legitimate by the model: 1

This is a small smoke test, not a representative benchmark. The result does not establish a real-world false-positive rate or guarantee that the application will identify all spam messages correctly.

## Limitations

- The model is trained and evaluated using SMS spam data.
- Accuracy on a test split does not guarantee performance on new messages.
- Spam recall is 66.41% in the reported random-split evaluation, so some spam messages may be missed.
- Suspicious phrase detection may flag legitimate messages for review.
- Model confidence is not a guarantee of message safety.
- Grouped evaluation reduces overlap between normalized message groups but is not campaign-separated testing.
- Prediction history is stored in memory and is cleared when the server restarts.
- The application does not verify URLs or guarantee phishing detection.
- The manual false-positive test uses only 12 messages and cannot establish real-world performance.

## Future Improvements

- Evaluate on a larger and more diverse collection of labeled messages.
- Add independently verified phishing-message datasets.
- Improve spam recall while monitoring false positives.
- Conduct campaign-separated evaluation using reliable campaign identifiers.
- Add persistent prediction history if required.
- Improve explainability and security testing.
- Evaluate the application on unseen messages from different sources.

## Conclusion

PhishShift demonstrates how machine learning and rule-based checks can work together in a web application to analyze SMS messages. It compares Rules-Based Detection, Logistic Regression with TF-IDF features, and Multinomial Naive Bayes. Logistic Regression achieved the best accuracy and spam F1-score in the reported random-split comparison. The application provides predictions and highlights suspicious wording to support manual review.

The grouped evaluation provides an additional assessment with no normalized-message groups shared between training and testing. However, further testing is needed before making claims about performance on real-world phishing messages.

**Disclaimer:** PhishShift is an educational project and should not be used as the only method for deciding whether a message is safe.