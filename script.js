const messageInput = document.getElementById("message");
const checkBtn = document.getElementById("checkBtn");
const exampleBtn = document.getElementById("exampleBtn");
const clearBtn = document.getElementById("clearBtn");
const historyClearBtn = document.getElementById("historyClearBtn");

const resultSection = document.getElementById("result");
const predictionText = document.getElementById("prediction");
const confidenceText = document.getElementById("confidence");
const confidenceTrack = document.getElementById("confidenceTrack");
const confidenceBar = document.getElementById("confidenceBar");
const historyContainer = document.getElementById("history");

let isChecking = false;
let isClearing = false;

const exampleMessage =
    "Congratulations! You have won a free prize. Click this link to claim your reward now!";

function formatConfidence(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number.toFixed(2) : "0.00";
}

function normalizePrediction(value) {
    const prediction = String(value || "").trim().toLowerCase();

    if (["spam", "phishing", "phish", "1"].includes(prediction)) {
        return "spam";
    }

    if (["uncertain", "unknown"].includes(prediction)) {
        return "uncertain";
    }

    return "legitimate";
}

function getPredictionLabel(prediction) {
    if (prediction === "spam") return "⚠ SPAM MESSAGE";
    if (prediction === "uncertain") return "⚠ NEEDS REVIEW";
    return "✓ LEGITIMATE MESSAGE";
}

function renderStats(stats = {}) {
    const elements = {
        total: stats.total_checks,
        spam: stats.spam_count,
        legitimate: stats.legitimate_count,
        uncertain: stats.uncertain_count
    };

    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) element.textContent = Number(value ?? 0);
    });
}

function createElement(tagName, className, text) {
    const element = document.createElement(tagName);

    if (className) element.className = className;
    if (text !== undefined) element.textContent = String(text);

    return element;
}

function getOrCreateResultElement(id, className, heading) {
    let element = document.getElementById(id);

    if (!element) {
        element = createElement("div", className);
        element.id = id;

        if (heading) {
            element.appendChild(
                createElement("p", "result-subheading", heading)
            );
        }

        const resultDetails = document.getElementById("resultDetails");

        if (resultDetails) {
            resultDetails.appendChild(element);
        } else {
            resultSection.appendChild(element);
        }
    }

    return element;
}

function showResult(data) {
    resultSection.classList.remove("hidden");
    resultSection.style.display = "";

    const prediction = normalizePrediction(data.prediction);
    const confidence = Number(data.confidence) || 0;
    const safeConfidence = Math.max(0, Math.min(100, confidence));

    predictionText.textContent = getPredictionLabel(prediction);
    predictionText.className = prediction;

    confidenceText.textContent = `${formatConfidence(confidence)}%`;

    // Confidence progress bar
    if (confidenceTrack && confidenceBar) {
        confidenceBar.style.width = `${safeConfidence}%`;

        confidenceTrack.setAttribute(
            "aria-valuenow",
            String(safeConfidence)
        );

        confidenceBar.setAttribute(
            "aria-label",
            `Model confidence ${formatConfidence(confidence)} percent`
        );

        confidenceTrack.style.display = "";
    }

    // Risk level
    const risk = String(data.risk_level || "Review Required");

    const riskElement = getOrCreateResultElement(
        "riskLevel",
        "risk-level",
        "Risk Level"
    );

    riskElement.replaceChildren(
        createElement("strong", "", `Risk Level: ${risk}`)
    );

    riskElement.classList.remove(
        "high",
        "medium",
        "low",
        "uncertain"
    );

    if (prediction === "spam" || risk.toLowerCase() === "high") {
        riskElement.classList.add("high");
    } else if (
        prediction === "uncertain" ||
        risk.toLowerCase().includes("review")
    ) {
        riskElement.classList.add("uncertain");
    } else {
        riskElement.classList.add("low");
    }

    // Suspicious phrases
    const cuesElement = getOrCreateResultElement(
        "suspiciousCues",
        "suspicious-cues",
        "Suspicious Phrases"
    );

    cuesElement.replaceChildren(
        createElement("p", "result-subheading", "Suspicious Phrases")
    );

    const cues = Array.isArray(data.suspicious_cues)
        ? data.suspicious_cues
        : [];

    if (cues.length > 0) {
        cues.forEach((cue) => {
            cuesElement.appendChild(
                createElement("span", "cue-tag", cue)
            );
        });
    } else {
        cuesElement.appendChild(
            createElement(
                "p",
                "no-cues",
                "No suspicious phrases detected."
            )
        );
    }

    // Updated review warning
    const existingWarning = document.getElementById("messageWarning");

    if (existingWarning) existingWarning.remove();

    let warningText = "";

    if (cues.length > 0) {
        warningText =
            "Suspicious phrases detected. Please review this message carefully.";
    } else if (prediction === "uncertain") {
        warningText =
            "The model confidence is low. Please review this message carefully.";
    } else if (prediction === "spam") {
        warningText =
            "This message may be spam. Avoid clicking suspicious links or sharing personal information.";
    }

    if (warningText) {
        const warning = createElement(
            "p",
            "message-warning",
            warningText
        );

        warning.id = "messageWarning";
        warning.setAttribute("role", "note");

        const resultDetails = document.getElementById("resultDetails");

        if (resultDetails) {
            resultDetails.prepend(warning);
        } else {
            resultSection.appendChild(warning);
        }
    }
}

function hideResult() {
    resultSection.classList.add("hidden");
    resultSection.style.display = "none";
}

function renderHistory(items = []) {
    historyContainer.replaceChildren();

    if (!Array.isArray(items) || items.length === 0) {
        historyContainer.appendChild(
            createElement(
                "p",
                "empty",
                "Your checked messages will appear here."
            )
        );
        return;
    }

    items.forEach((item) => {
        const card = createElement("div", "history-item");
        const prediction = normalizePrediction(item.prediction);

        card.appendChild(
            createElement(
                "div",
                `tag ${prediction}`,
                getPredictionLabel(prediction)
            )
        );

        card.appendChild(
            createElement(
                "div",
                "history-confidence",
                `Confidence: ${formatConfidence(item.confidence)}%`
            )
        );

        card.appendChild(
            createElement(
                "p",
                "history-message",
                item.message || "No message available."
            )
        );

        if (
            Array.isArray(item.suspicious_cues) &&
            item.suspicious_cues.length > 0
        ) {
            card.appendChild(
                createElement(
                    "p",
                    "history-cues",
                    "Suspicious phrases: " +
                    item.suspicious_cues.join(", ")
                )
            );
        }

        if (item.timestamp) {
            card.appendChild(
                createElement("small", "history-time", item.timestamp)
            );
        }

        historyContainer.appendChild(card);
    });
}

async function loadHistory() {
    try {
        const response = await fetch("/history", {
            method: "GET",
            headers: { Accept: "application/json" },
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`History request failed: ${response.status}`);
        }

        const data = await response.json();

        renderHistory(data.history || []);
        renderStats(data.stats || {});
    } catch (error) {
        console.error("History loading error:", error);
    }
}

async function checkMessage() {
    if (isChecking) return;

    const message = messageInput.value.trim();

    if (!message) {
        alert("Please enter a message to check.");
        messageInput.focus();
        return;
    }

    isChecking = true;
    checkBtn.disabled = true;
    checkBtn.textContent = "Checking...";

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json"
            },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Prediction failed.");
        }

        showResult(data);

        if (data.stats) renderStats(data.stats);

        await loadHistory();
    } catch (error) {
        console.error("Prediction error:", error);
        alert(error.message || "Unable to analyze the message.");
    } finally {
        isChecking = false;
        checkBtn.disabled = false;
        checkBtn.textContent = "Check Message";
    }
}

function clearMessage() {
    messageInput.value = "";
    hideResult();
    messageInput.focus();
}

async function clearHistory() {
    if (isClearing) return;

    isClearing = true;
    historyClearBtn.disabled = true;
    historyClearBtn.textContent = "Clearing...";

    try {
        const response = await fetch("/history/clear", {
            method: "POST",
            headers: { Accept: "application/json" }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Unable to clear history.");
        }

        renderHistory(data.history || []);

        renderStats(data.stats || {
            total_checks: 0,
            spam_count: 0,
            legitimate_count: 0,
            uncertain_count: 0
        });
    } catch (error) {
        console.error("Clear history error:", error);
        alert(error.message || "Unable to clear history.");
    } finally {
        isClearing = false;
        historyClearBtn.disabled = false;
        historyClearBtn.textContent = "Clear History";
    }
}

// Button events
checkBtn.addEventListener("click", checkMessage);

exampleBtn.addEventListener("click", () => {
    messageInput.value = exampleMessage;
    messageInput.focus();
});

clearBtn.addEventListener("click", clearMessage);
historyClearBtn.addEventListener("click", clearHistory);

// Enter submits; Shift + Enter adds a new line
messageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        checkMessage();
    }
});

// Load history when the page opens
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadHistory, {
        once: true
    });
} else {
    loadHistory();
}
