import os
from flask import Flask, render_template, send_file, jsonify
from controller import TrafficController

app = Flask(__name__)

controller = TrafficController(log_path="data/logs/cycles.csv")

def get_latest_image_path():
    files = [f for f in os.listdir(".") if f.startswith("captured_image_") and f.endswith(".jpg")]
    if not files:
        return None
    files.sort()
    return files[-1]

def read_count(path):
    if not os.path.exists(path):
        return 0
    try:
        with open(path, "r") as f:
            data = f.read().strip()
            return int(data) if data else 0
    except Exception:
        return 0

def get_vehicle_counts():
    return read_count("vehicle_count_ns.txt"), read_count("vehicle_count_ew.txt")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    count_ns, count_ew = get_vehicle_counts()
    phase, remaining, green_time, load = controller.update_phase(count_ns, count_ew)
    img_path = get_latest_image_path()
    return jsonify({
        "vehicle_count_ns": count_ns,
        "vehicle_count_ew": count_ew,
        "phase": phase,
        "remaining_time": remaining,
        "green_time": green_time,
        "load": load,
        "has_image": img_path is not None
    })

@app.route("/image")
def image():
    img_path = get_latest_image_path()
    if img_path and os.path.exists(img_path):
        return send_file(img_path, mimetype="image/jpeg")
    return ("", 204)

if __name__ == "__main__":
    app.run(debug=True)
