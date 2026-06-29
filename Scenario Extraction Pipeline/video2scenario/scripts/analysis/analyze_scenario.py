import json
import cv2

from scripts.analysis.naming import generate_scenario_id
from scripts.analysis.csv_writer import append_row
from scripts.analysis.odd.odd_analyzer import OddAnalyzer
from scripts.analysis.traffic.traffic_density import TrafficDensityEstimator
from scripts.analysis.environment.environment_classifier import EnvironmentClassifier
from scripts.analysis.collision.collision_analyzer import CollisionAnalyzer
from scripts.analysis.risk.probability_of_collision import ProbabilityOfCollisionEstimator


def analyze_scenario_from_json(
    scenario_json_path,
    source_video,
    csv_path="results/scenario_metrics.csv"
):
    # ------------------------------------------------------------------
    # LOAD SCENARIO JSON (output pipeline video → scenario)
    # ------------------------------------------------------------------
    with open(scenario_json_path) as f:
        data = json.load(f)

    agents = data.get("agents", [])

    # Ego motion è atteso come dizionario strutturato.
    # Qui NON lo calcoliamo: lo consumiamo soltanto.
    ego_motion = data.get("ego_motion", {})

    # ------------------------------------------------------------------
    # SAFETY METRICS DERIVED FROM VIDEO (TTC / DTO)
    # ------------------------------------------------------------------
    dto_vals = []
    ttc_vals = []
    collision_agents = []
    pedestrian_count = 0

    for a in agents:
        # Conteggio pedoni
        if a.get("is_pedestrian"):
            pedestrian_count += 1

        # DTO (pixel-based)
        if a.get("dto_px") is not None:
            dto_vals.append(a["dto_px"])

        # TTC (secondi)
        if a.get("ttc_seconds") is not None:
            ttc_vals.append(a["ttc_seconds"])

        # Collision flag
        if a.get("has_collision"):
            collision_agents.append(a["id"])

    dto_min = min(dto_vals) if dto_vals else None
    ttc_min = min(ttc_vals) if ttc_vals else None
    ttc_mean = sum(ttc_vals) / len(ttc_vals) if ttc_vals else None

    # ------------------------------------------------------------------
    # EGO MOTION (dinamica ego)
    # ------------------------------------------------------------------
    ego_avg_speed = ego_motion.get("ego_avg_speed_px_s")
    ego_max_speed = ego_motion.get("ego_max_speed_px_s")
    ego_trace = ego_motion.get("ego_trace", [])

    # ------------------------------------------------------------------
    # COLLISION (scenario-level)
    # ------------------------------------------------------------------
    collision_occurred = 1 if collision_agents else 0

    # ------------------------------------------------------------------
    # COLLISION ANALYSIS (type & time)
    # ------------------------------------------------------------------
    collision_time = None
    collision_type = None

    if collision_occurred:
        collision_analyzer = CollisionAnalyzer()
        collision_info = collision_analyzer.analyze(
            ego_trace=ego_trace,
            agents=agents
        )
        collision_time = collision_info["collision_time"]
        collision_type = collision_info["collision_type"]


    # ------------------------------------------------------------------
    # ODD ANALYSIS (MAIN CATEGORY + EVENTS)
    # ------------------------------------------------------------------
    odd_analyzer = OddAnalyzer(fps=30)

    odd_main_category = odd_analyzer.classify_main_category(ego_trace)

    # ODD events (STEP D)
    odd_events = odd_analyzer.detect_events(
        ego_trace=ego_trace,
        agents=agents
    )

    # ------------------------------------------------------------------
    # TRAFFIC DENSITY (STEP E)
    # ------------------------------------------------------------------
    traffic_estimator = TrafficDensityEstimator()
    traffic_info = traffic_estimator.estimate(agents)

    traffic_density = traffic_info["traffic_density"]
    traffic_density_value = traffic_info["traffic_density_value"]
    avg_num_vehicles = traffic_info["avg_num_vehicles"]

    # ------------------------------------------------------------------
    # PROBABILITY OF COLLISION (PC)
    #------------------------------------------------------------------
    pc_estimator = ProbabilityOfCollisionEstimator()

    pc_value = pc_estimator.estimate(
        ttc_min=ttc_min,
        dto_min=dto_min,
        traffic_density=traffic_density,
        odd_events=odd_events
    )

    # ------------------------------------------------------------------
    # ENVIRONMENT PERCEPTION (visual, video-based)
    # ------------------------------------------------------------------
    frames = []

    cap = cv2.VideoCapture(source_video)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
    cap.release()

    env_classifier = EnvironmentClassifier()
    env = env_classifier.classify(frames)

    # ------------------------------------------------------------------
    # SCENARIO ID
    # ------------------------------------------------------------------
    scenario_id = generate_scenario_id(
        video_path=source_video,
        odd_category=odd_main_category,
        odd_subcategory=None,
        weather_type=None,
        has_pedestrians=pedestrian_count > 0
    )

    # ------------------------------------------------------------------
    # CSV ROW (FINAL, COERENTE, TESI-SAFE)
    # ------------------------------------------------------------------
    row = {
        # --------------------------------------------------
        # Scenario identifiers
        # --------------------------------------------------
        "scenario_id": scenario_id,
        "source_video": source_video,
        "scenario_file": scenario_json_path,

        # --------------------------------------------------
        # ODD
        # --------------------------------------------------
        "odd_main_category": odd_main_category,
        "odd_events": ",".join(e["type"] for e in odd_events),
        "num_odd_events": len(odd_events),

        # --------------------------------------------------
        # Ego motion
        # --------------------------------------------------
        "ego_avg_speed": ego_avg_speed,
        "ego_max_speed": ego_max_speed,

        # --------------------------------------------------
        # Safety metrics
        # --------------------------------------------------
        "ttc_min": ttc_min,
        "ttc_mean": ttc_mean,
        "dto_min_vehicle": dto_min,
        "dto_min_pedestrian": None,

        # --------------------------------------------------
        # Collision & agents
        # --------------------------------------------------
        "collision_occurred": collision_occurred,
        "num_collision_agents": len(collision_agents),
        "num_pedestrians": pedestrian_count,

        # --------------------------------------------------
        # Collision details
        #--------------------------------------------------
        "collision_time": collision_time,
        "collision_type": collision_type,

        # --------------------------------------------------
        # Traffic density
        # --------------------------------------------------
        "traffic_density": traffic_density,
        "traffic_density_value": traffic_density_value,
        "avg_num_vehicles": avg_num_vehicles,

        # --------------------------------------------------
        # Collision risk
        # --------------------------------------------------
        "probability_of_collision": pc_value,
        "risk_ttc": pc_estimator._risk_from_ttc(ttc_min),
        "risk_dto": pc_estimator._risk_from_dto(dto_min),



        # --------------------------------------------------
        # Environment (perceived, video-based)
        # --------------------------------------------------
        "illumination": env["illumination"],
        "visibility": env["visibility"],
        "precipitation_visible": env["precipitation_visible"],
    }

    append_row(csv_path, row)
    return scenario_id
