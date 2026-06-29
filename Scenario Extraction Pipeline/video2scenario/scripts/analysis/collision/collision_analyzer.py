# scripts/analysis/collision/collision_analyzer.py
import numpy as np


class CollisionAnalyzer:
    """
    Deriva collision time e collision type
    da ego_trace e agent traces.
    """

    def __init__(self, collision_dist_px=20):
        self.collision_dist = collision_dist_px

    def analyze(self, ego_trace, agents):
        """
        ego_trace: lista di dict con chiave 'pos' e 't'
        agents: lista di agenti con 'trace' e 'is_pedestrian'
        """

        collision_times = []
        collision_types = []

        # Prepara ego positions
        ego_pos = [e["pos"] for e in ego_trace]
        ego_times = [e["t"] for e in ego_trace]

        for a in agents:
            if not a.get("has_collision"):
                continue

            trace = a.get("trace", [])
            if not trace:
                continue

            is_ped = a.get("is_pedestrian", False)

            for i in range(min(len(trace), len(ego_pos))):
                p_agent = np.array(trace[i])
                p_ego = np.array(ego_pos[i])

                dist = np.linalg.norm(p_agent - p_ego)

                if dist <= self.collision_dist:
                    collision_times.append(ego_times[i])
                    collision_types.append(
                        "pedestrian" if is_ped else "vehicle_vehicle"
                    )
                    break

        if not collision_times:
            return {
                "collision_time": None,
                "collision_type": None
            }

        # collision time = primo evento
        idx = int(np.argmin(collision_times))

        return {
            "collision_time": collision_times[idx],
            "collision_type": collision_types[idx]
        }
