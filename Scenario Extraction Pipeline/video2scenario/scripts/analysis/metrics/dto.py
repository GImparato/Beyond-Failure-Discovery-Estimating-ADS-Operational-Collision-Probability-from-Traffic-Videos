import math

def min_distance(ego_states, actor_states):
    dists = []
    for e, a in zip(ego_states, actor_states):
        d = math.hypot(a["x"] - e["x"], a["y"] - e["y"])
        dists.append(d)
    return min(dists) if dists else float("inf")

def compute_min_distance(ego_wp, npc_wps):
    distances = []
    for npc_wp in npc_wps:
        for e, n in zip(ego_wp, npc_wp):
            d = math.hypot(n["x"] - e["x"], n["y"] - e["y"])
            distances.append(d)

    return min(distances) if distances else float("inf")
