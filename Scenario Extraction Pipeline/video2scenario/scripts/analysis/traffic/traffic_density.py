# scripts/analysis/traffic/traffic_density.py
import numpy as np


class TrafficDensityEstimator:
    """
    Stima la densità di traffico usando il numero medio
    di veicoli presenti nel tempo (ID persistenti).
    """

    def __init__(self, low_th=3, high_th=7):
        self.low_th = low_th
        self.high_th = high_th

    def estimate(self, agents):
        """
        agents: lista di agenti con ID persistenti.
                Ogni agente deve avere una traccia temporale (trace).
        """

        if not agents:
            return {
                "traffic_density": "low",
                "traffic_density_value": 0.0,
                "avg_num_vehicles": 0.0
            }

        # Seleziona solo veicoli
        vehicles = [
            a for a in agents
            if a.get("class") in ["car", "truck", "bus", "motorcycle"]
        ]

        if not vehicles:
            return {
                "traffic_density": "low",
                "traffic_density_value": 0.0,
                "avg_num_vehicles": 0.0
            }

        # Numero massimo di frame osservati
        max_len = max(len(a.get("trace", [])) for a in vehicles)

        if max_len == 0:
            return {
                "traffic_density": "low",
                "traffic_density_value": 0.0,
                "avg_num_vehicles": 0.0
            }

        # Conta veicoli presenti a ogni frame
        counts = []
        for i in range(max_len):
            c = 0
            for v in vehicles:
                if i < len(v.get("trace", [])):
                    c += 1
            counts.append(c)

        avg_num_vehicles = float(np.mean(counts))

        # Classificazione discreta
        if avg_num_vehicles < self.low_th:
            density = "low"
        elif avg_num_vehicles < self.high_th:
            density = "medium"
        else:
            density = "high"

        return {
            "traffic_density": density,
            "traffic_density_value": avg_num_vehicles,
            "avg_num_vehicles": avg_num_vehicles
        }
