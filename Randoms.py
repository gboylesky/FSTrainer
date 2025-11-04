import os
import random
import base64
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ---------------------------
# Configuration
# ---------------------------
BaseRandomsFolder = os.path.join(app.static_folder, "Randoms")
LetterFolder = os.path.join(BaseRandomsFolder, "Letter")
NameFolder = os.path.join(BaseRandomsFolder, "Name")

# ✅ Added: No Hint folder (absolute Windows path)
NoHintFolder = r"C:\Users\GB\Desktop\FS Trainer Web\static\Randoms\NoHints"

Labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
          'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q']

# Mapping for formation names
NameMap = {
    'A': 'Unipod', 'B': 'Stair Diam', 'C': 'Mrphy Flak', 'D': 'Yuan',
    'E': 'Meeker', 'F': 'Open Accor', 'G': 'Cataccord', 'H': 'Bow',
    'J': 'Donut', 'K': 'Hook', 'L': 'Adder', 'M': 'Star',
    'N': 'Crank', 'O': 'Satellite', 'P': 'Sidebody', 'Q': 'Phalanx'
}

def _canon(s: str) -> str:
    """Lowercase + trim whitespace for robust matching."""
    return " ".join(s.strip().split()).lower()

ReverseNameMap = {_canon(v): k for k, v in NameMap.items()}

State = {
    "Mode": "Letter",           # Current mode (Letter/Name)
    "Category": "Randoms",      # Active category (Randoms/Blocks)
    "NoHint": False,            # ✅ New: whether No Hint mode is on
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
    """Return image base64 string from the folder based on current mode and No Hint."""
    # ✅ Use NoHints folder if enabled
    if State.get("NoHint", False):
        folder = NoHintFolder
    else:
        folder = LetterFolder if State["Mode"] == "Letter" else NameFolder

    path = os.path.join(folder, f"{Label}.png")
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


@app.route("/SetMode", methods=["POST"])
def SetMode():
    """Switch between Letter and Name modes and return current image for the new mode."""
    mode = request.form.get("mode", "Letter")
    if mode in ["Letter", "Name"]:
        State["Mode"] = mode
        print(f"🔁 Mode switched to: {mode}")
    img_data = GetImageBase64(State["Current"]) if State["Current"] else ""
    return jsonify(success=True, mode=State["Mode"], img_data=img_data)


@app.route("/SetCategory", methods=["POST"])
def SetCategory():
    """Switch between Randoms and Blocks categories."""
    category = request.form.get("category", "Randoms")
    if category in ["Randoms", "Blocks"]:
        State["Category"] = category
        print(f"📁 Category switched to: {category}")
    return jsonify(success=True, category=State["Category"])


# ✅ NEW: Handle "No Hint" toggle
@app.route("/SetNoHint", methods=["POST"])
def SetNoHint():
    """Enable or disable No Hint mode and return an updated image."""
    no_hint = request.form.get("no_hint") in ["true", "True", "1"]
    State["NoHint"] = no_hint
    print(f"🧩 No Hint mode set to: {no_hint}")

    # Refresh the current image from the appropriate folder
    img_data = GetImageBase64(State["Current"]) if State["Current"] else ""
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
            done_progress = State["Progress"]
            return jsonify({
                "done": True,
                "correct": State["Correct"],
                "incorrect": State["Incorrect"],
                "progress": done_progress,
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