import os
import random
import base64
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# ---------------------------
# Configuration
# ---------------------------
ImageFolder = os.path.join(app.static_folder, "Randoms")
Labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q']

State = {
    "Remaining": Labels.copy(),
    "Current": None,
    "Correct": 0,
    "Incorrect": 0,
    "AttemptedWrong": False
}

# ---------------------------
# Helpers
# ---------------------------
def GetImageBase64(Label):
    Path = os.path.join(ImageFolder, f"{Label}.png")
    if not os.path.exists(Path):
        print(f"⚠️ Missing: {Path}")
        return ""
    with open(Path, "rb") as F:
        return base64.b64encode(F.read()).decode("utf-8")

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
@app.route("/", methods=["GET", "POST"])
def Home():
    Msg = ""
    Color = "white"
    ShowResults = False
    ShowNext = False
    SetFirstImage()

    if request.method == "POST":
        Guess = request.form.get("guess")
        if Guess == State["Current"]:
            Msg = "✅ Correct"
            Color = "lime"
            if not State["AttemptedWrong"]:
                State["Correct"] += 1
            if len(State["Remaining"]) == 1:
                ShowResults = True
            else:
                ShowNext = True
        else:
            Msg = "❌ Try Again"
            Color = "red"
            if not State["AttemptedWrong"]:
                State["Incorrect"] += 1
                State["AttemptedWrong"] = True

    ImgData = GetImageBase64(State["Current"])
    return render_template(
        "index.html",
        img_data=ImgData,
        msg=Msg,
        color=Color,
        labels=Labels,
        progress=State["Correct"],
        total=len(Labels),
        correct=State["Correct"],
        incorrect=State["Incorrect"],
        show_results=ShowResults,
        show_next=ShowNext
    )

@app.route("/Next")
def NextStep():
    NextImage()
    return redirect(url_for("Home"))

@app.route("/Reset")
def Reset():
    State["Remaining"] = Labels.copy()
    State["Current"] = None
    State["Correct"] = 0
    State["Incorrect"] = 0
    State["AttemptedWrong"] = False
    return redirect(url_for("Home"))

# ---------------------------
# New AJAX Route
# ---------------------------
@app.route("/Guess", methods=["POST"])
def Guess():
    GuessLabel = request.form.get("guess")
    if not GuessLabel:
        return jsonify({"error": "Missing guess"}), 400
    if not State["Current"]:
        SetFirstImage()

    if GuessLabel == State["Current"]:
        Msg = "✅ Correct"
        Color = "lime"
        if not State["AttemptedWrong"]:
            State["Correct"] += 1
        if len(State["Remaining"]) == 1:
            return jsonify({
                "done": True,
                "correct": State["Correct"],
                "incorrect": State["Incorrect"]
            })
        NextImage()
    else:
        Msg = "❌ Try Again"
        Color = "red"
        if not State["AttemptedWrong"]:
            State["Incorrect"] += 1
            State["AttemptedWrong"] = True

    ImgData = GetImageBase64(State["Current"])
    return jsonify({
        "img_data": ImgData,
        "msg": Msg,
        "color": Color,
        "progress": State["Correct"],
        "total": len(Labels),
        "correct": State["Correct"],
        "incorrect": State["Incorrect"]
    })

if __name__ == "__main__":
    Port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=Port, debug=True)