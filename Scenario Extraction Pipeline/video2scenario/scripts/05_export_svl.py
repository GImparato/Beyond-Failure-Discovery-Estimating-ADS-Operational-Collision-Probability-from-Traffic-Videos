#!/usr/bin/env python3
import argparse, os, json, math, time
from utils.io_utils import read_json  # tua utility esistente

CLASS_TO_SVL = {
    "car": "Sedan",
    "truck": "Truck",
    "bus": "Bus",
    "motorcycle": "Motorcycle",
    "bicycle": "Bicycle",
    "person": "Pedestrian",
    "pedestrian": "Pedestrian",
}

SORA_SENSORS = [
    "Main Camera", "Depth Camera", "Lidar", "Radar", "GPS", "IMU", "CAN-Bus"
]

def to_deg(rad): return rad * 180.0 / math.pi

def heading_deg(p_prev, p_next):
    dx, dy = p_next["x"] - p_prev["x"], p_next["y"] - p_prev["y"]
    return 0.0 if (dx == 0 and dy == 0) else to_deg(math.atan2(dy, dx))

def speed_mps(p_prev, p_next):
    dt = max(1e-6, p_next["t"] - p_prev["t"])
    return math.hypot(p_next["x"] - p_prev["x"], p_next["y"] - p_prev["y"]) / dt

def normalize_class(cname):
    cname = (cname or "car").lower()
    return CLASS_TO_SVL.get(cname, "Sedan")

def build_agent(agent):
    traj = agent.get("trajectory", [])
    if not traj:
        return None
    traj = sorted(traj, key=lambda p: p.get("t", 0.0))

    # deduplica per tempo
    dedup, last_t = [], None
    for p in traj:
        t = float(p["t"])
        if last_t is None or t > last_t:
            dedup.append({"t": t, "x": float(p["x"]), "y": float(p["y"])})
            last_t = t
    traj = dedup

    wps = []
    for i, p in enumerate(traj):
        if i < len(traj) - 1:
            yaw, spd = heading_deg(p, traj[i + 1]), speed_mps(p, traj[i + 1])
        else:
            yaw = wps[-1]["yaw"] if wps else 0.0
            spd = wps[-1]["speed"] if wps else 0.0
        wps.append({
            "t": round(p["t"], 3),
            "x": round(p["x"], 3),
            "y": round(p["y"], 3),
            "z": 0.0,
            "yaw": round(yaw, 3),
            "speed": round(spd, 3)
        })

    spawn = {"x": wps[0]["x"], "y": wps[0]["y"], "z": 0.0, "yaw": wps[0]["yaw"]}

    return {
        "id": str(agent.get("id", "")),
        "name": f"agent_{agent.get('id')}",
        "type": "NPC",
        "vehicleModel": normalize_class(agent.get("class")),
        "spawn": spawn,
        "behavior": {
            "controller": "FollowWaypoints",
            "waypoints": wps,
            "loop": False
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Export scenario JSON compatibile con LGSVL 2021.3 / Sora-SVL")
    parser.add_argument("--trajectories", required=True, help="Percorso a outputs/trajectories.json")
    ts_default = time.strftime("%Y%m%d_%H%M%S")
    parser.add_argument("--out", default=f"outputs/scenario_svl_{ts_default}.json")
    parser.add_argument("--title", default="video2scenario")
    parser.add_argument("--map", default="BorregasAve")
    parser.add_argument("--time-of-day", default="noon",
                        choices=["dawn","morning","noon","afternoon","dusk","night"])
    args = parser.parse_args()

    data = read_json(args.trajectories)
    agents = data.get("agents", [])

    svl_agents = []
    for ag in agents:
        a = build_agent(ag)
        if a:
            svl_agents.append(a)

    # === Aggiungi EGO ===
    ego_vehicle = {
        "id": "ego",
        "name": "EgoVehicle",
        "type": "EGO",
        "vehicleModel": "Lincoln2017MKZ (Apollo 5.0)",
        "spawn": {"x": 0.0, "y": 0.0, "z": 0.0, "yaw": 90.0},
        "sensors": SORA_SENSORS
    }
    svl_agents.insert(0, ego_vehicle)

    scenario = {
        "schema": "svlsimulator/api/v1",
        "name": args.title,
        "map": args.map,
        "timeOfDay": args.time_of_day,
        "weather": {"rain": 0, "fog": 0, "wetness": 0, "cloudiness": 0},
        "agents": svl_agents
    }

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(scenario, f, ensure_ascii=False, indent=2)

    print(f"[OK] Scenario Sora-SVL scritto in {args.out} (EGO + {len(svl_agents)-1} NPC)")

if __name__ == "__main__":
    main()
