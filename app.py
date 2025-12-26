import os
import time
import csv
from datetime import datetime

from flask import Flask, jsonify, render_template, send_file

from controller import TrafficController   # NEW: use your smart controller

app = Flask(__name__)

# -------------------------------------------------------
# SMART CONTROLLER INSTANCE
# -------------------------------------------------------
controller = TrafficController()  # uses config.py + internal CSV logging


# -------------------------------------------------------
# EXTRA CSV LOGGING (OPTIONAL, can be removed if you only want controller.log)
# -------------------------------------------------------
def log_cycle_simple(phase, ns_count, ew_count, green_time):
    """
    Kept only if you still want app.py-side logging; otherwise not used.
    History widget already reads the controller's CSV.
    """
    os.makedirs("data/logs", exist_ok=True)
    csv_path = "data/logs/cycles_app.csv"
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


# -------------------------------------------------------
# INDEX
# -------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -------------------------------------------------------
# STATUS (used by dashboard JS)
# -------------------------------------------------------
@app.route("/status")
def status():
    """
    Frontend expects:
      phase           -> "NS", "EW", "YELLOW", "ALL_RED"
      remaining_time  -> number
      green_time      -> number
      vehicle_ns      -> number
      vehicle_ew      -> number
      has_image       -> bool
    """

    # Read current counts from YOLO output text files
    count_ns = 0
    count_ew = 0

    if os.path.exists("vehicle_count_ns.txt"):
        try:
            with open("vehicle_count_ns.txt") as f:
                count_ns = int(f.read().strip() or 0)
        except ValueError:
            count_ns = 0

    if os.path.exists("vehicle_count_ew.txt"):
        try:
            with open("vehicle_count_ew.txt") as f:
                count_ew = int(f.read().strip() or 0)
        except ValueError:
            count_ew = 0

    # Ask smart controller for phase + timings + load
    ui_phase, remaining, green_time, load = controller.update_phase(count_ns, count_ew)

    has_image = os.path.exists("static/latest_frame.jpg")

    return jsonify(
        {
            "phase": ui_phase,
            "remaining_time": remaining,
            "green_time": green_time,
            "vehicle_ns": count_ns,
            "vehicle_ew": count_ew,
            "has_image": has_image,
            # Optional: expose load if you later show it in UI
            # "load": load
        }
    )


# -------------------------------------------------------
# HISTORY (last 10 rows of controller CSV)
# -------------------------------------------------------
@app.route("/history")
def history():
    # controller already writes to data/logs/cycles.csv
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


# -------------------------------------------------------
# IMAGE (served to <img id="trafficImage"> when has_image = true)
# -------------------------------------------------------
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


# -------------------------------------------------------
if __name__ == "__main__":
    # debug=True for development
    app.run(host="0.0.0.0", port=5000, debug=True)
