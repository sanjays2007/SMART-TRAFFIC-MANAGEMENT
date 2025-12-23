import cv2
import os
import numpy as np
import time

# Load YOLO pre-trained model for vehicle detection
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")

# Load the COCO names file (contains class names)
with open("coco.names", "r") as f:
    classes = f.read().strip().split("\n")

last_image_used = None

while True:
    # find latest captured image
    image_files = [
        f for f in os.listdir(".")
        if f.startswith("captured_image_") and f.endswith(".jpg")
    ]
    if not image_files:
        print("No captured images yet. Waiting...")
        time.sleep(2)
        continue

    image_files.sort()
    image_path = image_files[-1]

    # skip if same image as previous loop
    if image_path == last_image_used:
        time.sleep(2)
        continue
    last_image_used = image_path

    print(f"\nUsing image: {image_path}")

    image = cv2.imread(image_path)
    if image is None:
        print("Failed to read image, skipping...")
        time.sleep(2)
        continue

    height, width, _ = image.shape

    blob = cv2.dnn.blobFromImage(
        image, 0.00392, (416, 416), (0, 0, 0), True, crop=False
    )
    net.setInput(blob)
    output_layers = net.getUnconnectedOutLayersNames()
    detections = net.forward(output_layers)

    vehicle_count = 0

    for detection in detections:
        for obj in detection:
            scores = obj[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            # car(2), motorbike(3), bus(5), truck(7)
            if confidence > 0.5 and class_id in [2, 3, 5, 7]:
                vehicle_count += 1
                center_x = int(obj[0] * width)
                center_y = int(obj[1] * height)
                w = int(obj[2] * width)
                h = int(obj[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    image,
                    "Vehicle",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )

    print(f"Vehicles detected: {vehicle_count}")

    # write count for green_time_signal.py
    with open("vehicle_count.txt", "w") as f:
        f.write(str(vehicle_count))

    # show window (updates each new image)
    cv2.imshow("Vehicle Detection", image)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    time.sleep(2)  # wait before checking for new image

cv2.destroyAllWindows()
