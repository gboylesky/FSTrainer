import os
import random
import base64
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ---------------------------
# Configuration
# ---------------------------
ImageFolder = os.path.join(app.static_folder, "Randoms", "Letter")

Labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
          'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q']

State = {
    "Remaining": Labels.copy(),
    "Current": None,
    "Correct": 0,
    "Incorrect": 0,
    "Progress": 0,
    "AttemptedWrong": False
}

# ---------------------------
# Helpers
# ---------------------------
def GetImageBase64(Label):
    path = os.path.join(ImageFolder, f"{Label}.png")
    if not os.path.exists(path):
        print(f"⚠️ Missing: {path}")
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def NextImage():
    """Move to the next random image and clear AttemptedWrong flag."""
    if State["Current"] in State["Remaining"]:
        State["Remaining"].remove(State["Current"])
    if not State["Remaining"]:
        State["Remaining"] = Labels.copy()
    State["Current"] = random.choice(State["Remaining"])
    State["AttemptedWrong"] = False


def SetFirstImage():
    """Pick a starting image if none currently selected."""
    if not State["Current"]:
        State["Current"] = random.choice(State["Remaining"])
        State["AttemptedWrong"] = False


# ---------------------------
# Routes
# ---------------------------
@app.route("/", methods=["GET"])
def Home():
    SetFirstImage()
    img_data = GetImageBase64(State["Current"])
    return render_template(
        "index.html",
        img_data=img_data,
        msg="",
        color="white",
        labels=Labels,
        progress=State["Progress"],
        total=len(Labels),
        correct=State["Correct"],
        incorrect=State["Incorrect"],
        show_results=False,
        show_next=False
    )


@app.route("/Guess", methods=["POST"])
def Guess():
    guess_label = request.form.get("guess")
    if not guess_label:
        return jsonify({"error": "Missing guess"}), 400

    if not State["Current"]:
        SetFirstImage()

    # ---------------- Correct Guess ----------------
    if guess_label == State["Current"]:
        msg = "✅ Correct"
        color = "lime"

        # Only increment Correct and Progress once per formation
        if not State["AttemptedWrong"]:
            State["Correct"] += 1
        State["Progress"] += 1

        # Check if finished all
        if len(State["Remaining"]) == 1:
            State["Remaining"].remove(State["Current"])
            done_progress = State["Progress"]
            return jsonify({
                "done": True,
                "correct": State["Correct"],
                "incorrect": State["Incorrect"],
                "progress": done_progress,
                "total": len(Labels)
            })

        NextImage()

    # ---------------- Incorrect Guess ----------------
    else:
        msg = "❌ Try Again"
        color = "red"
        if not State["AttemptedWrong"]:
            State["Incorrect"] += 1
            State["AttemptedWrong"] = True

    img_data = GetImageBase64(State["Current"])
    return jsonify({
        "img_data": img_data,
        "msg": msg,
        "color": color,
        "progress": State["Progress"],
        "total": len(Labels),
        "correct": State["Correct"],
        "incorrect": State["Incorrect"]
    })


@app.route("/Reset", methods=["POST"])
def Reset():
    """Reset all counters and reload a fresh random image."""
    State["Remaining"] = Labels.copy()
    State["Current"] = None
    State["Correct"] = 0
    State["Incorrect"] = 0
    State["Progress"] = 0
    State["AttemptedWrong"] = False

    SetFirstImage()
    img_data = GetImageBase64(State["Current"])

    return jsonify({
        "img_data": img_data,
        "progress": State["Progress"],
        "total": len(Labels),
        "correct": State["Correct"],
        "incorrect": State["Incorrect"]
    })


# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)