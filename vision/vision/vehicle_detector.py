from pathlib import Path
import cv2
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent
IMAGE_PATH = BASE_DIR / "sample_videos" / "bus.jpg"
OUTPUT_PATH = BASE_DIR / "sample_videos" / "detected_output.jpg"
VEHICLE_CLASSES = [2, 3, 5, 7]

def main():
    if not IMAGE_PATH.exists():
        print(f"Image not found: {IMAGE_PATH}")
        print("Put a test image at sample_videos\\bus.jpg or use the dashboard to upload a video.")
        return
    image = cv2.imread(str(IMAGE_PATH))
    if image is None:
        print("Could not read the image.")
        return
    model = YOLO("yolo11n.pt")
    result = model.predict(image, classes=VEHICLE_CLASSES, conf=0.35, verbose=False)[0]
    cv2.imwrite(str(OUTPUT_PATH), result.plot())
    print("Detections:")
    for box in result.boxes:
        cls_id = int(box.cls[0].item())
        print(f"{model.names[cls_id]}: {float(box.conf[0].item()):.2f}")
    print(f"Output saved to: {OUTPUT_PATH}")
    cv2.imshow("Vehicle Detection", result.plot())
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
