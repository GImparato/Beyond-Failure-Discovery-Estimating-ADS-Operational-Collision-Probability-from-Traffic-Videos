# scripts/analysis/environment/environment_classifier.py
import cv2
import numpy as np


class EnvironmentClassifier:
    """
    Stima condizioni ambientali percepite da video monoculare.
    NON stima meteo reale, ma solo cue visive osservabili.
    """

    def classify(self, frames):
        """
        frames: lista di frame RGB (np.array BGR OpenCV)

        Ritorna:
            illumination: day | dusk_dawn | night
            visibility: good | moderate | poor
            precipitation_visible: True | False
        """

        if not frames:
            return {
                "illumination": None,
                "visibility": None,
                "precipitation_visible": None
            }

        # --------------------------------------------------
        # ILLUMINATION (global luminance)
        # --------------------------------------------------
        gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
        mean_luminance = float(np.mean(gray))

        if mean_luminance < 60:
            illumination = "night"
        elif mean_luminance < 120:
            illumination = "dusk_dawn"
        else:
            illumination = "day"

        # --------------------------------------------------
        # VISIBILITY (contrast-based)
        # --------------------------------------------------
        contrast = float(np.std(gray))

        if contrast < 25:
            visibility = "poor"
        elif contrast < 50:
            visibility = "moderate"
        else:
            visibility = "good"

        # --------------------------------------------------
        # PRECIPITATION (visual heuristic)
        # --------------------------------------------------
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(np.mean(edges > 0))

        precipitation_visible = edge_density > 0.12

        return {
            "illumination": illumination,
            "visibility": visibility,
            "precipitation_visible": precipitation_visible
        }
