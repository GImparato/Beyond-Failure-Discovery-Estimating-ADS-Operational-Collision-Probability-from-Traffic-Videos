import numpy as np


def detect_odd_events(ego_trace, agents, fps):
    """
    Rileva ODD events in modo opportunistico e video-robusto.
    """
    events = []

    # --------------------------------------------------
    # STOP EVENT (permissivo)
    # --------------------------------------------------
    speeds = [e["speed"] for e in ego_trace]
    stop_time = np.sum(np.array(speeds) < 2.0) / fps
    if stop_time > 1.0:
        events.append({"type": "stop", "confidence": min(1.0, stop_time / 3.0)})

    # --------------------------------------------------
    # PEDESTRIAN NEAR EGO (DTO-based)
    # --------------------------------------------------
    for a in agents:
        if a.get("is_pedestrian") and a.get("dto_px") is not None:
            if a["dto_px"] < 100:
                events.append({
                    "type": "pedestrian_near_ego_lane",
                    "confidence": 1.0 - a["dto_px"] / 100
                })

    # --------------------------------------------------
    # CUT-IN (short trace allowed)
    # --------------------------------------------------
    for a in agents:
        trace = a.get("trace", [])
        if len(trace) >= 2:
            dx = trace[-1][0] - trace[0][0]
            if abs(dx) > 60:
                events.append({
                    "type": "cut_in",
                    "confidence": min(1.0, abs(dx) / 120)
                })

    # --------------------------------------------------
    # CROSSING VEHICLE (bearing change)
    # --------------------------------------------------
    for a in agents:
        trace = a.get("trace", [])
        if len(trace) >= 3:
            bearings = []
            for i in range(1, len(trace)):
                dx = trace[i][0] - trace[i-1][0]
                dy = trace[i][1] - trace[i-1][1]
                bearings.append(np.degrees(np.arctan2(dy, dx)))
            if max(bearings) - min(bearings) > 25:
                events.append({
                    "type": "crossing_vehicle",
                    "confidence": 0.7
                })

    # --------------------------------------------------
    # GENERIC INTERACTION
    # --------------------------------------------------
    if len(agents) > 1:
        events.append({"type": "interaction_present", "confidence": 0.5})

    # --------------------------------------------------
    # FALLBACK
    # --------------------------------------------------
    if not events:
        events.append({"type": "no_relevant_event", "confidence": 1.0})

    # Dedup per tipo (mantieni max confidence)
    unique = {}
    for e in events:
        t = e["type"]
        if t not in unique or e["confidence"] > unique[t]["confidence"]:
            unique[t] = e

    return list(unique.values())
