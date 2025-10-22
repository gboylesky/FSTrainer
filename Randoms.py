from flask import Flask, render_template, request, redirect, url_for
from PIL import Image
import os, random, base64
from io import BytesIO

app = Flask(__name__)

# ---------------- Settings ----------------
ImageFolder = r"C:\Users\GB\Desktop\FS Trainer Web\Randoms"
Labels = ['A','B','C','D','E','F','G','H','J','K','L','M','N','O','P','Q']
MaxImageWidth = 500
MaxImageHeight = 300

# ---------------- Load Images ----------------
images = {}
if os.path.isdir(ImageFolder):
    for f in sorted(os.listdir(ImageFolder)):
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            lbl = os.path.splitext(f)[0].upper()
            try:
                img = Image.open(os.path.join(ImageFolder, f))
                img.thumbnail((MaxImageWidth, MaxImageHeight))
                buf = BytesIO()
                img.save(buf, format="PNG")
                images[lbl] = base64.b64encode(buf.getvalue()).decode("utf-8")
            except Exception as e:
                print(f"Skipping {f}: {e}")

# ---------------- State ----------------
state = {
    "remaining": list(images.keys()),
    "current": None,
    "correct": 0,
    "incorrect": 0,
    "index": 0,
    "bad": False
}

def next_image():
    """Advance to the next random image."""
    if not state["remaining"]:
        state["remaining"] = list(images.keys())
    state["bad"] = False
    state["current"] = random.choice(state["remaining"])
    state["remaining"].remove(state["current"])

# ---------------- Routes ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    if state["current"] is None:
        next_image()

    msg, color = None, None
    show_next = False
    show_results = False  # NEW FLAG to handle end-of-sequence modal

    if request.method == "POST":
        guess = request.form.get("guess")
        if guess == state["current"]:
            state["index"] += 1
            if not state["bad"]:
                state["correct"] += 1
            msg, color = "✅ Correct!", "lime"

            # If finished all images, trigger results instead of next image
            if state["index"] >= len(images):
                show_results = True
            else:
                show_next = True
        else:
            state["incorrect"] += 1
            state["bad"] = True
            msg, color = "❌ Try Again", "red"

    img_data = images[state["current"]]
    progress = state["index"]
    total = len(images)

    return render_template(
        "index.html",
        img_data=img_data,
        labels=Labels,
        msg=msg,
        color=color,
        correct=state["correct"],
        incorrect=state["incorrect"],
        progress=progress,
        total=total,
        show_next=show_next,
        show_results=show_results,
    )

@app.route("/next")
def next_step():
    # Only advance if not finished
    if state["index"] < len(images):
        next_image()
    return redirect(url_for("home"))

@app.route("/reset")
def reset():
    """Reset all progress and start again."""
    state.update({
        "remaining": list(images.keys()),
        "current": None,
        "correct": 0,
        "incorrect": 0,
        "index": 0,
        "bad": False
    })
    next_image()
    return redirect(url_for("home"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)