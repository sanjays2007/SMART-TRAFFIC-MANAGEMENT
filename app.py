import os
import time
import csv
from datetime import datetime

from flask import Flask, jsonify, render_template, send_file

app = Flask(__name__)

# ------------------------------------------------------------------
# SIMPLE CONTROLLER STATE (you can later wire this to controller.py)
# ------------------------------------------------------------------
controller_state = {
    "current_phase": "EW",      # "NS" or "EW"
    "phase_start_time": time.time(),
    "green_time": 30,           # seconds for current green
    "vehicle_ns": 0,
    "vehicle_ew": 0,
}

def compute_remaining_time():
    elapsed = time.time() - controller_state["phase_start_time"]
    remaining = controller_state["green_time"] - elapsed
    return max(0, int(remaining))

# ------------------------------------------------------------------
# CSV LOGGING HELPER  data/logs/cycles.csv
# ------------------------------------------------------------------
def log_cycle(phase, ns_count, ew_count, green_time):
    os.makedirs("data/logs", exist_ok=True)
    csv_path = "data/logs/cycles.csv"
    file_exists = os.path.exists(csv_path)

    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "phase",
                "vehicle_count_ns",
                "vehicle_count_ew",
                "green_time",
            ],
        )
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "phase": phase,
                "vehicle_count_ns": ns_count,
                "vehicle_count_ew": ew_count,
                "green_time": green_time,
            }
        )

# ------------------------------------------------------------------
# INDEX
# ------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# ------------------------------------------------------------------
# STATUS  (used by dashboard JS)
# ------------------------------------------------------------------
@app.route("/status")
def status():
    """
    JS expects:
      phase            -> "NS" or "EW"
      remaining_time   -> number
      green_time       -> number
      vehicle_ns       -> number
      vehicle_ew       -> number
    """
    # TODO: replace this block with real values from your detection/controller
    # Example demo logic: alternate every 30 seconds
    remaining = compute_remaining_time()
    if remaining == 0:
        controller_state["current_phase"] = (
            "NS" if controller_state["current_phase"] == "EW" else "EW"
        )
        controller_state["phase_start_time"] = time.time()
        controller_state["green_time"] = 30
        remaining = compute_remaining_time()

        # log one cycle when phase switches
        log_cycle(
            controller_state["current_phase"],
            controller_state["vehicle_ns"],
            controller_state["vehicle_ew"],
            controller_state["green_time"],
        )

    # here you can update vehicle_ns / vehicle_ew from txt or shared memory
    if os.path.exists("vehicle_count_ns.txt"):
        try:
            with open("vehicle_count_ns.txt") as f:
                controller_state["vehicle_ns"] = int(f.read().strip() or 0)
        except ValueError:
            controller_state["vehicle_ns"] = 0

    if os.path.exists("vehicle_count_ew.txt"):
        try:
            with open("vehicle_count_ew.txt") as f:
                controller_state["vehicle_ew"] = int(f.read().strip() or 0)
        except ValueError:
            controller_state["vehicle_ew"] = 0

    has_image = os.path.exists("static/latest_frame.jpg")

    return jsonify(
        {
            "phase": controller_state["current_phase"],
            "remaining_time": remaining,
            "green_time": controller_state["green_time"],
            "vehicle_ns": controller_state["vehicle_ns"],
            "vehicle_ew": controller_state["vehicle_ew"],
            "has_image": has_image,
        }
    )

# ------------------------------------------------------------------
# HISTORY  (last 10 rows of cycles.csv)
# ------------------------------------------------------------------
@app.route("/history")
def history():
    csv_path = "data/logs/cycles.csv"
    if not os.path.exists(csv_path):
        return jsonify([])

    cycles = []
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        for row in rows[-10:]:
            cycles.append(
                {
                    "timestamp": row["timestamp"],
                    "phase": row["phase"],
                    "vehicle_ns": row["vehicle_count_ns"],
                    "vehicle_ew": row["vehicle_count_ew"],
                    "green_time": row["green_time"],
                }
            )

    return jsonify(cycles)

# ------------------------------------------------------------------
# IMAGE  (served to <img id="trafficImage"> when has_image = true)
# ------------------------------------------------------------------
@app.route("/image")
def image():
    """
    Expects your capture script to keep writing a frame to:
      static/latest_frame.jpg
    """
    img_path = "static/latest_frame.jpg"
    if os.path.exists(img_path):
        return send_file(img_path, mimetype="image/jpeg")
    return ("", 404)

# ------------------------------------------------------------------
if __name__ == "__main__":
    # debug=True for development
    app.run(host="0.0.0.0", port=5000, debug=True)
