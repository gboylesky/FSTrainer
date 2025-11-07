import os
import random
import base64
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session  # pip install Flask-Session

# ---------------------------
# App Setup
# ---------------------------
app = Flask(__name__)
app.secret_key = "supersecretkey"  # required for session encryption
app.config["SESSION_TYPE"] = "filesystem"  # store session data per user
app.config["SESSION_PERMANENT"] = False
Session(app)

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

# ---------------------------
# Helpers
# ---------------------------
def get_state():
    """Get or initialize per-session state."""
    if "state" not in session:
        session["state"] = {
            "Mode": "Letter",
            "Category": "Randoms",
            "NoHint": False,
            "TestMode": False,
            "Remaining": Labels.copy(),
            "Current": None,
            "Correct": 0,
            "Incorrect": 0,
            "Progress": 0,
            "AttemptedWrong": False
        }
    return session["state"]

def save_state(state):
    """Persist modified state to session."""
    session["state"] = state
    session.modified = True

def GetImageBase64(label, state):
    """Return image base64 string based on mode and NoHint state."""
    folder = NoHintFolder if state.get("NoHint") else (
        LetterFolder if state["Mode"] == "Letter" else NameFolder
    )
    path = os.path.join(folder, f"{label}.png")
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def NextImage(state):
    if state["Current"] in state["Remaining"]:
        state["Remaining"].remove(state["Current"])
    if not state["Remaining"]:
        state["Remaining"] = Labels.copy()
    state["Current"] = random.choice(state["Remaining"])
    state["AttemptedWrong"] = False

def SetFirstImage(state):
    if not state["Current"]:
        state["Current"] = random.choice(state["Remaining"])
        state["AttemptedWrong"] = False

# ---------------------------
# Routes
# ---------------------------

@app.route("/", methods=["GET"])
def Home():
    state = get_state()
    state["NoHint"] = False
    SetFirstImage(state)
    img_data = GetImageBase64(state["Current"], state)
    save_state(state)
    return render_template(
        "index.html",
        img_data=img_data,
        msg="",
        color="white",
        labels=Labels,
        progress=state["Progress"],
        total=len(Labels),
        correct=state["Correct"],
        incorrect=state["Incorrect"],
        show_results=False,
        show_next=False
    )

@app.route("/SetMode", methods=["POST"])
def SetMode():
    state = get_state()
    mode = request.form.get("mode", "Letter")
    if mode in ["Letter", "Name"]:
        state["Mode"] = mode
    img_data = GetImageBase64(state["Current"], state) if state["Current"] else ""
    save_state(state)
    return jsonify(success=True, mode=state["Mode"], img_data=img_data)

@app.route("/SetCategory", methods=["POST"])
def SetCategory():
    state = get_state()
    category = request.form.get("category", "Randoms")
    if category in ["Randoms", "Blocks"]:
        state["Category"] = category
    save_state(state)
    return jsonify(success=True, category=state["Category"])

@app.route("/SetTestMode", methods=["POST"])
def SetTestMode():
    state = get_state()
    test_mode = request.form.get("test_mode") in ["true", "True", "1"]
    state["TestMode"] = test_mode
    save_state(state)
    return jsonify(success=True, test_mode=test_mode)

@app.route("/SetNoHint", methods=["POST"])
def SetNoHint():
    state = get_state()
    no_hint = request.form.get("no_hint") in ["true", "True", "1"]
    state["NoHint"] = no_hint

    folder = NoHintFolder if no_hint else (
        LetterFolder if state["Mode"] == "Letter" else NameFolder
    )
    current_label = state.get("Current")

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
            state["Current"] = os.path.splitext(fallback)[0]
    else:
        SetFirstImage(state)
        img_data = GetImageBase64(state["Current"], state)

    save_state(state)
    return jsonify({"img_data": img_data})

@app.route("/Guess", methods=["POST"])
def Guess():
    state = get_state()
    guess_label = request.form.get("guess")
    if not guess_label:
        return jsonify({"error": "Missing guess"}), 400

    if not state["Current"]:
        SetFirstImage(state)

    if state["Mode"] == "Letter":
        guessed_letter = guess_label
    else:
        canon_guess = _canon(guess_label)
        guessed_letter = ReverseNameMap.get(canon_guess)
        if guessed_letter is None:
            for key_name, letter in ReverseNameMap.items():
                if key_name.startswith(canon_guess) or canon_guess.startswith(key_name):
                    guessed_letter = letter
                    break

    if guessed_letter == state["Current"]:
        msg = "✅ Correct"
        color = "lime"
        if not state["AttemptedWrong"]:
            state["Correct"] += 1
        state["Progress"] += 1
        if len(state["Remaining"]) == 1:
            state["Remaining"].remove(state["Current"])
            save_state(state)
            img_data = GetImageBase64(state["Current"], state)
            return jsonify({
                "done": True,
                "img_data": img_data,
                "msg": "✅ All Complete!",
                "color": "lime",
                "correct": state["Correct"],
                "incorrect": state["Incorrect"],
                "progress": state["Progress"],
                "total": len(Labels)
    })

        NextImage(state)
    else:
        msg = "❌ Try Again"
        color = "red"
        if not state["AttemptedWrong"]:
            state["Incorrect"] += 1
            state["AttemptedWrong"] = True

    img_data = GetImageBase64(state["Current"], state)
    save_state(state)
    return jsonify({
        "img_data": img_data,
        "msg": msg,
        "color": color,
        "progress": state["Progress"],
        "total": len(Labels),
        "correct": state["Correct"],
        "incorrect": state["Incorrect"]
    })

@app.route("/Reset", methods=["POST"])
def Reset():
    state = {
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
    SetFirstImage(state)
    img_data = GetImageBase64(state["Current"], state)
    if not img_data:
        # fallback to 'A.png' if something is missing
        img_data = GetImageBase64("A", state)
        state["Current"] = "A"
    save_state(state)
    return jsonify({
        "img_data": img_data,
        "progress": state["Progress"],
        "total": len(Labels),
        "correct": state["Correct"],
        "incorrect": state["Incorrect"]
    })

# ---------------------------
# Entry Point
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)