import cv2
from collections import Counter

class ColorClassifier:
    def classify(self, crop):
        if crop is None or crop.size == 0:
            return "Unknown"

        h, w = crop.shape[:2]
        crop = crop[int(h * 0.15):max(int(h * 0.85), 1),
                    int(w * 0.15):max(int(w * 0.85), 1)]

        if crop.size == 0:
            return "Unknown"

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        pixels = hsv.reshape(-1, 3)
        pixels = pixels[pixels[:, 2] > 35]

        if len(pixels) == 0:
            return "Black"

        hue = pixels[:, 0]
        sat = pixels[:, 1]
        val = pixels[:, 2]

        if val.mean() < 65:
            return "Black"
        if sat.mean() < 35:
            return "White" if val.mean() > 190 else ("Grey" if val.mean() > 100 else "Black")

        h_mean = float(hue.mean())
        if h_mean < 10 or h_mean >= 170:
            return "Red"
        if h_mean < 22:
            return "Orange"
        if h_mean < 35:
            return "Yellow"
        if h_mean < 85:
            return "Green"
        if h_mean < 130:
            return "Blue"
        return "Purple"
