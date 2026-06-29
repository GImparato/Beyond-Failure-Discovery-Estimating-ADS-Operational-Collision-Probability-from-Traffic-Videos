# scripts/analysis/ego/ego_motion.py
import numpy as np
from collections import deque

class EgoMotionEstimator:
    """
    Stima map-less dell'ego motion a partire dal moto relativo degli agenti.
    STEP A: yaw stimato usando SOLO agenti lontani e stabili.
    """

    def __init__(self, fps, ema_alpha=0.3, min_agents=3,
                 min_distance_px=150):
        self.fps = fps
        self.ema_alpha = ema_alpha
        self.min_agents = min_agents
        self.min_distance_px = min_distance_px

        self._vel_ema = np.array([0.0, 0.0])
        self._yaw_ema = 0.0

        self.ego_trace = []

    def update(self, agents_prev, agents_curr, t):
        common_ids = set(agents_prev.keys()) & set(agents_curr.keys())

        rel_vels = []

        for aid in common_ids:
            a_prev = agents_prev[aid]
            a_curr = agents_curr[aid]

            p0 = np.array(a_prev["pos"])
            p1 = np.array(a_curr["pos"])

            # --------------------------------------------
            # STEP A — filtro agenti lontani
            # --------------------------------------------
            # Usiamo solo agenti abbastanza lontani
            # (riduce rumore da sorpassi / lane change)
            dist = np.linalg.norm(p0)
            if dist < self.min_distance_px:
                continue

            rel_vels.append((p1 - p0) * self.fps)

        # Se non abbiamo abbastanza agenti affidabili
        if len(rel_vels) < self.min_agents:
            self._append_state(t, self._vel_ema, self._yaw_ema)
            return

        world_vel = np.mean(rel_vels, axis=0)
        ego_vel = -world_vel

        # EMA smoothing
        self._vel_ema = (
            self.ema_alpha * ego_vel + (1 - self.ema_alpha) * self._vel_ema
        )

        yaw = np.degrees(np.arctan2(self._vel_ema[1], self._vel_ema[0]))
        self._yaw_ema = (
            self.ema_alpha * yaw + (1 - self.ema_alpha) * self._yaw_ema
        )

        self._append_state(t, self._vel_ema, self._yaw_ema)

    def _append_state(self, t, vel, yaw):
        speed = float(np.linalg.norm(vel))
        self.ego_trace.append({
            "t": t,
            "vel": (float(vel[0]), float(vel[1])),
            "speed": speed,
            "yaw": float(yaw),
        })

    def get_trace(self):
        return self.ego_trace