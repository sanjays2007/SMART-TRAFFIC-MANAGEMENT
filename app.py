import os
from flask import Flask, render_template, send_file, jsonify

app = Flask(__name__)

BASE_GREEN_TIME = 30
VEHICLE_MULTIPLIER = 2

def get_latest_image_path():
    files = [
        f for f in os.listdir(".")
        if f.startswith("captured_image_") and f.endswith(".jpg")
    ]
    if not files:
        return None
    files.sort()
    return files[-1]

def get_vehicle_count():
    if not os.path.exists("vehicle_count.txt"):
        return 0
    try:
        with open("vehicle_count.txt", "r") as f:
            data = f.read().strip()
            return int(data) if data else 0
    except Exception:
        return 0

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    count = get_vehicle_count()
    green_time = BASE_GREEN_TIME + VEHICLE_MULTIPLIER * count
    img_path = get_latest_image_path()
    return jsonify({
        "vehicle_count": count,
        "green_time": green_time,
        "has_image": img_path is not None
    })

@app.route("/image")
def image():
    img_path = get_latest_image_path()
    if img_path and os.path.exists(img_path):
        return send_file(img_path, mimetype="image/jpeg")
    else:
        # return a 1x1 empty image if none
        return ("", 204)

if __name__ == "__main__":
    app.run(debug=True)
