import os
import time

import cv2
import numpy as np
from ultralytics import YOLO

IMAGE_PATH = "static/latest_frame.jpg"   # frame from capture script
CONF_THRESHOLD = 0.3                     # detection confidence threshold
NMS_IOU_THRESHOLD = 0.45                 # NMS IoU threshold

# COCO class ids for vehicles in YOLOv8
VEHICLE_CLASS_IDS = {2, 3, 5, 7}         # car, motorcycle, bus, truck

print("[YOLOv8] loading model yolov8n.pt ...")
model = YOLO("yolov8n.pt")               # will auto-download first run
print("[YOLOv8] model ready")


def count_vehicles(image):
    """
    Run YOLOv8 on the image and return NS/EW counts and annotated frame.
    """
    height, width, _ = image.shape
    mid_y = height // 2  # top = NS, bottom = EW

    # Run inference (results list, one item per image)
    results = model(
        image,
        verbose=False,
        conf=CONF_THRESHOLD,
        iou=NMS_IOU_THRESHOLD,
    )

    count_ns = 0
    count_ew = 0

    annotated = image.copy()

    for r in results:
        if r.boxes is None:
            continue

        boxes = r.boxes.xyxy.cpu().numpy().astype(int)   # [x1, y1, x2, y2]
        cls = r.boxes.cls.cpu().numpy().astype(int)      # class ids
        confs = r.boxes.conf.cpu().numpy()               # confidences

        for (x1, y1, x2, y2, c, conf) in zip(
            boxes[:, 0],
            boxes[:, 1],
            boxes[:, 2],
            boxes[:, 3],
            cls,
            confs,
        ):
            if c not in VEHICLE_CLASS_IDS:
                continue

            center_y = (y1 + y2) // 2

            if center_y < mid_y:
                count_ns += 1
                color = (0, 255, 0)      # NS = green
            else:
                count_ew += 1
                color = (0, 191, 255)    # EW = yellow

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated,
                f"veh {conf:.2f}",
                (x1, max(10, y1 - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2,
            )

    # draw split line
    cv2.line(annotated, (0, mid_y), (width, mid_y), (255, 255, 255), 1)

    return count_ns, count_ew, annotated


def main():
    while True:
        if not os.path.exists(IMAGE_PATH):
            print("No captured images yet. Waiting...")
            time.sleep(2)
            continue

        image = cv2.imread(IMAGE_PATH)
        if image is None:
            print("Failed to read image, skipping...")
            time.sleep(2)
            continue

        count_ns, count_ew, annotated = count_vehicles(image)

        print(f"NS vehicles: {count_ns} | EW vehicles: {count_ew}")

        # write counts for controller/Flask
        with open("vehicle_count_ns.txt", "w") as f:
            f.write(str(count_ns))
        with open("vehicle_count_ew.txt", "w") as f:
            f.write(str(count_ew))

        cv2.imshow("YOLOv8 Vehicle Detection (NS upper, EW lower)", annotated)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        time.sleep(1)

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
