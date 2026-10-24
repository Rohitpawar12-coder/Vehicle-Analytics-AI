from ultralytics import YOLO
import cv2
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_PATH = BASE_DIR / "sample_videos" / "bus.jpg"
OUTPUT_PATH = BASE_DIR / "sample_videos" / "detected_output.jpg"

VEHICLE_CLASSES = [2, 3, 5, 7]


def main():
    if not IMAGE_PATH.exists():
        print(f"Image not found: {IMAGE_PATH}")
        return

    image = cv2.imread(str(IMAGE_PATH))

    if image is None:
        print("Could not read the image.")
        return

    print("Loading YOLO model...")
    model = YOLO("yolo11n.pt")

    print("Detecting vehicles...")
    results = model.predict(
        source=image,
        classes=VEHICLE_CLASSES,
        conf=0.35,
        verbose=False
    )

    annotated_image = results[0].plot()
    cv2.imwrite(str(OUTPUT_PATH), annotated_image)

    print("\nDetection Results:")

    for box in results[0].boxes:
        class_id = int(box.cls[0])
        label = model.names[class_id]
        confidence = float(box.conf[0])
        print(f"{label}: {confidence:.2f}")

    print(f"\nOutput saved to: {OUTPUT_PATH}")

    cv2.imshow("Vehicle Detection", annotated_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
