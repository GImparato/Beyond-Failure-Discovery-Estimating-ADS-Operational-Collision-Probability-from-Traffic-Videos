# scripts/analysis/risk/probability_of_collision.py
class ProbabilityOfCollisionEstimator:
    """
    Stima una collision probability normalizzata [0,1]
    come risk score composito.
    """

    def __init__(
        self,
        ttc_th=5.0,
        dto_th=50.0,
        w_ttc=0.4,
        w_dto=0.3,
        w_traffic=0.2,
        w_events=0.1
    ):
        self.ttc_th = ttc_th
        self.dto_th = dto_th

        self.w_ttc = w_ttc
        self.w_dto = w_dto
        self.w_traffic = w_traffic
        self.w_events = w_events

    def _risk_from_ttc(self, ttc):
        if ttc is None:
            return 0.0
        return max(0.0, min(1.0, (self.ttc_th - ttc) / self.ttc_th))

    def _risk_from_dto(self, dto):
        if dto is None:
            return 0.0
        return max(0.0, min(1.0, (self.dto_th - dto) / self.dto_th))

    def _risk_from_traffic(self, traffic_density):
        return {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8
        }.get(traffic_density, 0.2)

    def _risk_from_events(self, odd_events):
        if not odd_events:
            return 0.0

        critical_events = {
            "cut_in",
            "crossing_vehicle",
            "pedestrian_near_ego_lane",
            "stop"
        }

        score = 0.0
        for e in odd_events:
            if e["type"] in critical_events:
                score += 0.25

        return min(1.0, score)

    def estimate(
        self,
        ttc_min,
        dto_min,
        traffic_density,
        odd_events
    ):
        r_ttc = self._risk_from_ttc(ttc_min)
        r_dto = self._risk_from_dto(dto_min)
        r_traffic = self._risk_from_traffic(traffic_density)
        r_events = self._risk_from_events(odd_events)

        pc = (
            self.w_ttc * r_ttc +
            self.w_dto * r_dto +
            self.w_traffic * r_traffic +
            self.w_events * r_events
        )

        return max(0.0, min(1.0, pc))


# The probability of collision is computed as a normalized composite risk score in [0,1],
# combining temporal risk (TTC), spatial risk (DTO), traffic context, and semantic ODD events.
# Each component is individually normalized using physically motivated thresholds and
# weighted according to its relevance in safety assessment.

