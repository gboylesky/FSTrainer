import os
import random
import base64
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ---------------------------
# Configuration
# ---------------------------

BaseRandomsFolder = os.path.join(app.static_folder, "Randoms")
LetterFolder = os.path.join(BaseRandomsFolder, "Letter")
NameFolder = os.path.join(BaseRandomsFolder, "Name")
NoHintFolder = os.path.join(BaseRandomsFolder, "NoHints")

Labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
          'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q']

NameMap = {
    'A': 'Unipod', 'B': 'Stair Diam', 'C': 'Mrphy Flak', 'D': 'Yuan',
    'E': 'Meeker', 'F': 'Open Accor', 'G': 'Cataccord', 'H': 'Bow',
    'J': 'Donut', 'K': 'Hook', 'L': 'Adder', 'M': 'Star',
    'N': 'Crank', 'O': 'Satellite', 'P': 'Sidebody', 'Q': 'Phalanx'
}

def _canon(s: str) -> str:
    return " ".join(s.strip().split()).lower()

ReverseNameMap = {_canon(v): k for k, v in NameMap.items()}

State = {
    "Mode": "Letter",
    "Category": "Randoms",
    "NoHint": False,
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
    """Return image base64 string based on mode and NoHint state."""
    folder = NoHintFolder if State.get("NoHint") else (
        LetterFolder if State["Mode"] == "Letter" else NameFolder
    )
    path = os.path.join(folder, f"{Label}.png")
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def NextImage():
    if State["Current"] in State["Remaining"]:
        State["Remaining"].remove(State["Current"])
    if not State["Remaining"]:
        State["Remaining"] = Labels.copy()
    State["Current"] = random.choice(State["Remaining"])
    State["AttemptedWrong"] = False

def SetFirstImage():
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

@app.route("/SetMode", methods=["POST"])
def SetMode():
    mode = request.form.get("mode", "Letter")
    if mode in ["Letter", "Name"]:
        State["Mode"] = mode
    img_data = GetImageBase64(State["Current"]) if State["Current"] else ""
    return jsonify(success=True, mode=State["Mode"], img_data=img_data)

@app.route("/SetCategory", methods=["POST"])
def SetCategory():
    category = request.form.get("category", "Randoms")
    if category in ["Randoms", "Blocks"]:
        State["Category"] = category
    return jsonify(success=True, category=State["Category"])

@app.route("/SetNoHint", methods=["POST"])
def SetNoHint():
    no_hint = request.form.get("no_hint") in ["true", "True", "1"]
    State["NoHint"] = no_hint

    folder = NoHintFolder if no_hint else (
        LetterFolder if State["Mode"] == "Letter" else NameFolder
    )
    current_label = State.get("Current")

    if current_label:
        image_path = os.path.join(folder, f"{current_label}.png")
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
        else:
            files = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
            if not files:
                return jsonify({"img_data": ""})
            fallback = random.choice(files)
            with open(os.path.join(folder, fallback), "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            State["Current"] = os.path.splitext(fallback)[0]
    else:
        SetFirstImage()
        img_data = GetImageBase64(State["Current"])

    return jsonify({"img_data": img_data})

@app.route("/Guess", methods=["POST"])
def Guess():
    guess_label = request.form.get("guess")
    if not guess_label:
        return jsonify({"error": "Missing guess"}), 400

    if not State["Current"]:
        SetFirstImage()

    if State["Mode"] == "Letter":
        guessed_letter = guess_label
    else:
        canon_guess = _canon(guess_label)
        guessed_letter = ReverseNameMap.get(canon_guess)
        if guessed_letter is None:
            for key_name, letter in ReverseNameMap.items():
                if key_name.startswith(canon_guess) or canon_guess.startswith(key_name):
                    guessed_letter = letter
                    break

    if guessed_letter == State["Current"]:
        msg = "✅ Correct"
        color = "lime"
        if not State["AttemptedWrong"]:
            State["Correct"] += 1
        State["Progress"] += 1
        if len(State["Remaining"]) == 1:
            State["Remaining"].remove(State["Current"])
            return jsonify({
                "done": True,
                "correct": State["Correct"],
                "incorrect": State["Incorrect"],
                "progress": State["Progress"],
                "total": len(Labels)
            })
        NextImage()
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
    app.run(host="0.0.0.0", port=port)