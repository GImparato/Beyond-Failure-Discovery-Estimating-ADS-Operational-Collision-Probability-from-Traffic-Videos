import math

def compute_ttc(ego_states, actor_states):
    ttc_values = []

    for e, a in zip(ego_states, actor_states):
        dx = a["x"] - e["x"]
        dy = a["y"] - e["y"]
        dvx = e["vx"] - a["vx"]
        dvy = e["vy"] - a["vy"]

        closing_speed = dx * dvx + dy * dvy
        if closing_speed <= 0:
            continue

        dist_sq = dx**2 + dy**2
        ttc = dist_sq / closing_speed
        if ttc > 0:
            ttc_values.append(ttc)

    if not ttc_values:
        return float("inf"), float("inf")

    return min(ttc_values), sum(ttc_values) / len(ttc_values)

def compute_ttc_from_waypoints(ego_wp, npc_wps):
    ttc_values = []

    for npc_wp in npc_wps:
        for e, n in zip(ego_wp, npc_wp):
            dx = n["x"] - e["x"]
            dy = n["y"] - e["y"]

            ev = e.get("speed", 5.0)
            nv = n.get("speed", 5.0)

            rel_speed = ev - nv
            if rel_speed <= 0:
                continue

            dist = math.hypot(dx, dy)
            ttc = dist / rel_speed
            if ttc > 0:
                ttc_values.append(ttc)

    if not ttc_values:
        return float("inf"), float("inf")

    return min(ttc_values), sum(ttc_values) / len(ttc_values)
