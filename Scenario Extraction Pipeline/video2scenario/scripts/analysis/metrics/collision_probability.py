def collision_probability(safe_distance, current_distance):
    if current_distance >= safe_distance:
        return 0.0
    return max(0.0, (safe_distance - current_distance) / safe_distance)


def compute_pc(distances, ego_speed, decel=6.0):
    probs = []

    for d in distances:
        safe_dist = (ego_speed ** 2) / (2 * decel) + 5.0
        probs.append(collision_probability(safe_dist, d))

    if not probs:
        return 0.0, 0.0

    return max(probs), sum(probs) / len(probs)
