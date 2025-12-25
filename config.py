# config.py

# Base green times (seconds)
BASE_GREEN_NS = 25      # little lower base
BASE_GREEN_EW = 25

# Per-vehicle increment
PER_VEHICLE = 3         # stronger effect: +3s per vehicle

# Bounds
MIN_GREEN = 15          # never less than 15s
MAX_GREEN = 120         # allow long greens for heavy queues

# Yellow and all-red times (seconds)
YELLOW_TIME = 3
ALL_RED_TIME = 2

# Time-of-day profiles (24-hr clock)
PEAK_MORNING = (8, 11)    # 08:00–11:59
PEAK_EVENING = (17, 20)   # 17:00–20:59

PEAK_MULTIPLIER_NS = 1.5  # NS boosts more in peak
PEAK_MULTIPLIER_EW = 1.2
NIGHT_MULTIPLIER = 0.7    # shorter greens at night
