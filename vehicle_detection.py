import cv2
import os
import numpy as np
import time

# Load YOLO pre-trained model for vehicle detection
net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")

# Load the COCO names file (contains class names)
with open("coco.names", "r") as f:
    classes = f.read().strip().split("\n")

def get_latest_image_path():
    files = [
        f for f in os.listdir(".")
        if f.startswith("captured_image_") and f.endswith(".jpg")
    ]
    if not files:
        return None
    files.sort()
    return files[-1]

last_image_used = None

while True:
    image_path = get_latest_image_path()
    if image_path is None:
        print("No captured images yet. Waiting...")
        time.sleep(2)
        continue

    if image_path == last_image_used:
        time.sleep(1)
        continue
    last_image_used = image_path

    print(f"\nUsing image: {image_path}")
    image = cv2.imread(image_path)
    if image is None:
        print("Failed to read image, skipping...")
        time.sleep(2)
        continue

    height, width, _ = image.shape
    mid_y = height // 2  # top = NS, bottom = EW

    blob = cv2.dnn.blobFromImage(
        image, 0.00392, (416, 416), (0, 0, 0), True, crop=False
    )
    net.setInput(blob)
    output_layers = net.getUnconnectedOutLayersNames()
    detections = net.forward(output_layers)

    count_ns = 0
    count_ew = 0

    for detection in detections:
        for obj in detection:
            scores = obj[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            # class_id 2=car, 3=motorbike, 5=bus, 7=truck
            if confidence > 0.5 and class_id in [2, 3, 5, 7]:
                center_x = int(obj[0] * width)
                center_y = int(obj[1] * height)
                w = int(obj[2] * width)
                h = int(obj[3] * height)

                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                # region split
                if center_y < mid_y:
                    count_ns += 1
                    color = (0, 255, 0)  # NS
                else:
                    count_ew += 1
                    color = (0, 191, 255)  # EW

                cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
                cv2.putText(image, "Vehicle", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    print(f"NS vehicles: {count_ns} | EW vehicles: {count_ew}")

    # write counts for controller/Flask
    with open("vehicle_count_ns.txt", "w") as f:
        f.write(str(count_ns))
    with open("vehicle_count_ew.txt", "w") as f:
        f.write(str(count_ew))

    # draw split line
    cv2.line(image, (0, mid_y), (width, mid_y), (255, 255, 255), 1)
    cv2.imshow("Vehicle Detection (NS upper, EW lower)", image)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    time.sleep(1)

cv2.destroyAllWindows()
