import numpy as np


def detect_odd_events(ego_trace, agents, fps):
    """
    Detects ODD events from video data in a permissive and robust manner.

    - Multiple ODD events may occur within the same scenario.
    - Each event is represented by a type and a confidence score.
    - Directional attributes (e.g., left/right cut-in) are inferred when applicable.
    - If no relevant interaction is detected, a fallback 'none' event is returned.
    """
    events = []

    # --------------------------------------------------
    # STOP EVENT (ego stationary for a significant time)
    # --------------------------------------------------
    speeds = [e["speed"] for e in ego_trace if "speed" in e]
    if speeds:
        stop_time = np.sum(np.array(speeds) < 2.0) / fps
        if stop_time > 1.0:
            events.append({
                "type": "stop",
                "confidence": min(1.0, stop_time / 3.0)
            })

    # --------------------------------------------------
    # PEDESTRIAN NEAR EGO LANE (DTO-based)
    # --------------------------------------------------
    for a in agents:
        if a.get("is_pedestrian") and a.get("dto_px") is not None:
            if a["dto_px"] < 100:
                events.append({
                    "type": "pedestrian_near_ego_lane",
                    "confidence": max(0.0, 1.0 - a["dto_px"] / 100.0)
                })

    # --------------------------------------------------
    # CUT-IN EVENT (with direction)
    # --------------------------------------------------
    for a in agents:
        trace = a.get("trace", [])
        if len(trace) >= 2:
            dx = trace[-1][0] - trace[0][0]
            if abs(dx) > 60:
                direction = "left" if dx < 0 else "right"
                events.append({
                    "type": "cut_in",
                    "direction": direction,
                    "confidence": min(1.0, abs(dx) / 120.0)
                })

    # --------------------------------------------------
    # CROSSING VEHICLE (bearing variation)
    # --------------------------------------------------
    for a in agents:
        trace = a.get("trace", [])
        if len(trace) >= 3:
            bearings = []
            for i in range(1, len(trace)):
                dx = trace[i][0] - trace[i - 1][0]
                dy = trace[i][1] - trace[i - 1][1]
                bearings.append(np.degrees(np.arctan2(dy, dx)))

            if bearings and (max(bearings) - min(bearings)) > 25:
                events.append({
                    "type": "crossing_vehicle",
                    "confidence": 0.7
                })

    # --------------------------------------------------
    # GENERIC INTERACTION (contextual)
    # --------------------------------------------------
    if len(agents) > 1:
        events.append({
            "type": "interaction_present",
            "confidence": 0.5
        })

    # --------------------------------------------------
    # FALLBACK: no relevant event detected
    # --------------------------------------------------
    if not events:
        events.append({
            "type": "none",
            "confidence": 1.0
        })

    # --------------------------------------------------
    # DEDUPLICATION BY EVENT TYPE (keep max confidence)
    # --------------------------------------------------
    unique_events = {}
    for e in events:
        event_key = e["type"]
        if event_key not in unique_events or e["confidence"] > unique_events[event_key]["confidence"]:
            unique_events[event_key] = e

    return list(unique_events.values())
