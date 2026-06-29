import numpy as np
from scripts.analysis.odd.odd_events import detect_odd_events


class OddAnalyzer:
    """
    ODD Analyzer basato su fusione di segnali ego-based + eventi opportunistici.
    """

    def __init__(self, fps):
        self.fps = fps

    # --------------------------------------------------
    # MAIN CATEGORY (multi-signal)
    # --------------------------------------------------
    def classify_main_category(self, ego_trace):
        if ego_trace is None or len(ego_trace) < self.fps:
            return "on_road_following"

        yaws = np.array([e["yaw"] for e in ego_trace])
        speeds = np.array([e["speed"] for e in ego_trace])
        xs = np.array([e["pos"][0] for e in ego_trace])

        yaw_total = np.sum(np.abs(np.diff(yaws)))
        yaw_mean = np.mean(np.abs(np.diff(yaws)))
        lateral_disp = xs.max() - xs.min()

        stop_duration = np.sum(speeds < 2.0) / self.fps
        speed_drop = np.max(speeds) - np.min(speeds)

        # -----------------------------
        # Decision logic
        # -----------------------------
        if stop_duration > 2.0 and speed_drop > 5:
            return "stop_and_go"

        if yaw_total > 80 and lateral_disp > 60:
            return "intersection_maneuver"

        if yaw_total > 35:
            return "turn_maneuver"

        if lateral_disp > 80 and yaw_mean < 5:
            return "lane_change"

        return "on_road_following"

    # --------------------------------------------------
    # EVENTS
    # --------------------------------------------------
    def detect_events(self, ego_trace, agents):
        return detect_odd_events(ego_trace, agents, self.fps)
