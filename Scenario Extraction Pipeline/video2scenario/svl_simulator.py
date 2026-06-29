import sys
import json
from pathlib import Path
import lgsvl

# Mappa classi YOLO → agenti SORA
CLASS_TO_AGENT = {
    "car": "Sedan",
    "truck": "Truck",
    "bus": "Bus",
    "motorcycle": "Motorcycle",
    "bicycle": "Bicycle",
    "person": "Pedestrian"
}


def load_api(sim_path: Path):
    """Aggiunge l’SDK Python del simulatore al sys.path."""
    api_folder = sim_path / "API" / "PythonAPI"
    if not api_folder.exists():
        raise FileNotFoundError(f"PythonAPI non trovata in {api_folder}")
    sys.path.append(str(api_folder))


def convert_trajectories(trajectories_file, ego_id, output_file):
    """Converte trajectories.json in tracks_world.json."""
    with open(trajectories_file, "r") as f:
        data = json.load(f)

    result = {
        "ego_id": ego_id,
        "objects": []
    }

    for obj in data:
        result["objects"].append({
            "id": obj["id"],
            "class": obj.get("class", "car"),
            "trajectory": obj["trajectory"]
        })

    with open(output_file, "w") as f:
        json.dump(result, f, indent=4)

    return output_file


def to_vector(p):
    return lgsvl.Vector(p["x"], p["y"], p["z"])


def traj_to_waypoints(traj):
    """Converte una lista di punti in DriveWaypoint."""
    wps = []
    for p in traj:
        wp = lgsvl.DriveWaypoint(
            to_vector(p),
            p.get("speed", 8),
            0
        )
        wps.append(wp)
    return wps


def run_sora_simulation(
    simulator_path,
    map_name,
    tracks_world_file,
    sim_host,
    sim_port,
    apollo_ip,
    apollo_port
):
    """Avvia una simulazione nel SORA-SVL Desktop."""
    # 1. Carica API
    load_api(Path(simulator_path))

    # 2. Importa lgsvl dopo aver aggiunto il path
    import lgsvl

    # 3. Carica tracks_world.json
    with open(tracks_world_file, "r") as f:
        data = json.load(f)

    ego_id = data["ego_id"]
    objects = data["objects"]

    # 4. Connessione al simulatore
    sim = lgsvl.Simulator(sim_host, sim_port)

    if sim.current_scene != map_name:
        print(f"[INFO] Carico mappa {map_name}")
        sim.load(map_name)
    else:
        print(f"[INFO] Mappa già caricata.")

    # 5. Spawn EGO
    ego_obj = next(o for o in objects if o["id"] == ego_id)
    traj = ego_obj["trajectory"]

    start = traj[0]
    ego_state = lgsvl.AgentState()
    ego_state.transform = lgsvl.Transform(
        to_vector(start),
        lgsvl.Vector(0, 0, 0)
    )

    ego = sim.add_agent("Lincoln2017MKZ", lgsvl.AgentType.EGO, ego_state)

    # 6. NPC
    for o in objects:
        if o["id"] == ego_id:
            continue

        cls = o.get("class", "car")
        model = CLASS_TO_AGENT.get(cls, "Sedan")

        traj = o["trajectory"]
        if len(traj) < 2:
            continue

        start = traj[0]
        st = lgsvl.AgentState()
        st.transform = lgsvl.Transform(
            to_vector(start),
            lgsvl.Vector(0, 0, 0)
        )

        npc = sim.add_agent(model, lgsvl.AgentType.NPC, st)
        npc.follow(traj_to_waypoints(traj), loop=False)

    # 7. Bridge Apollo
    if apollo_ip:
        bridge = sim.bridge_connection()
        bridge.connect(apollo_ip, apollo_port)
        print(f"[INFO] Connesso ad Apollo: {apollo_ip}:{apollo_port}")

    # 8. Avvia simulazione
    print("[INFO] Avvio simulazione...")
    sim.run(0)

