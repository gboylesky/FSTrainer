import os
import random
import base64
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ---------------------------
# Configuration
# ---------------------------
IMAGE_FOLDER = os.path.join(app.static_folder, "Randoms")
LABELS = ['A','B','C','D','E','F','G','H','J','K','L','M','N','O','P','Q']

state = {
    "remaining": LABELS.copy(),
    "current": None,
    "correct": 0,
    "incorrect": 0,
    "attempted_wrong": False
}


# ---------------------------
# Helpers
# ---------------------------
def get_image_base64(label):
    path = os.path.join(IMAGE_FOLDER, f"{label}.png")
    if not os.path.exists(path):
        print(f"⚠️ Missing: {path}")
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def next_image():
    """Advance to the next random image."""
    if state["current"] in state["remaining"]:
        state["remaining"].remove(state["current"])
    if not state["remaining"]:
        state["remaining"] = LABELS.copy()
    state["current"] = random.choice(state["remaining"])
    state["attempted_wrong"] = False


def set_first_image():
    """Pick the first image if none set."""
    if not state["current"]:
        state["current"] = random.choice(state["remaining"])
        state["attempted_wrong"] = False


# ---------------------------
# Routes
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    msg = ""
    color = "white"
    show_results = False
    show_next = False

    set_first_image()

    if request.method == "POST":
        guess = request.form.get("guess")

        if guess == state["current"]:
            msg = "✅ Correct"
            color = "lime"
            if not state["attempted_wrong"]:
                state["correct"] += 1

            # Finished?
            if len(state["remaining"]) == 1:
                show_results = True
            else:
                show_next = True

        else:
            msg = "❌ Try Again"
            color = "red"
            if not state["attempted_wrong"]:
                state["incorrect"] += 1
                state["attempted_wrong"] = True

    img_data = get_image_base64(state["current"])
    return render_template(
        "index.html",
        img_data=img_data,
        msg=msg,
        color=color,
        labels=LABELS,
        progress=state["correct"],
        total=len(LABELS),
        correct=state["correct"],
        incorrect=state["incorrect"],
        show_results=show_results,
        show_next=show_next
    )


@app.route("/next")
def next_step():
    next_image()
    return redirect(url_for("home"))


@app.route("/reset")
def reset():
    state["remaining"] = LABELS.copy()
    state["current"] = None
    state["correct"] = 0
    state["incorrect"] = 0
    state["attempted_wrong"] = False
    return redirect(url_for("home"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)