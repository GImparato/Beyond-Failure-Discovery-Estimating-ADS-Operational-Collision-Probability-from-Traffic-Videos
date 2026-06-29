#!/usr/bin/env python3
import argparse
import json
import lgsvl
import time
from environs import Env


# ============================================================
#   MAPPE SUPPORTATE (SVL 2021.3)
# ============================================================
MAP_IDS = {
    "BorregasAve": lgsvl.wise.DefaultAssets.map_borregasave,
    "StraightRoad": "4b4f25f0-6a9f-4ea3-a94f-5bb6fcb44c30",
    "SingleLaneRoad": "a0911a28-e9e0-4f10-8d7a-1ffa6e7ab9d4",
}

# ============================================================
#   UUID VEICOLI (quelli standard; aggiorneremo quando avrai gli LGSVL)
# ============================================================
EGO_MODELS_UUID = {
    "Jaguar2015XE": "88c8ce1f-7e54-4bf2-8baf-3a5eac2d6d34",
    "Lincoln2017MKZ": "2e966a70-4a19-44b5-a5e7-64e00a7bc5de",
    "Lexus2016RXHybrid": "fbc1df35-2100-4fa3-8b8a-5cd062b59787",
}

CANDIDATE_MODELS = ["Lincoln2017MKZ", "Jaguar2015XE", "Lexus2016RXHybrid"]


# ============================================================
#   FUNZIONE SPAWN EGO (versione robusta)
# ============================================================
def spawn_ego(sim, used_spawn, args):
    ego_state = lgsvl.AgentState()
    ego_state.transform.position = used_spawn.position
    ego_state.transform.rotation = used_spawn.rotation

    for model_name in CANDIDATE_MODELS:
        uuid = EGO_MODELS_UUID[model_name]
        print(f"[EGO] Tentativo spawn: {model_name} (UUID {uuid})")

        try:
            ego = sim.add_agent(uuid, lgsvl.AgentType.EGO, ego_state)
            print(f"[OK] EGO spawnato come {model_name}")
            return ego, model_name
        except Exception as e:
            print(f"[WARN] Fallito spawn {model_name}: {str(e)}")
            continue

    raise RuntimeError("❌ Nessun modello EGO compatibile trovato!")


# ============================================================
#   MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Esegue scenario JSON su SVL per Apollo 6")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--bridge", default="100.92.58.9")
    parser.add_argument("--port", type=int, default=9090)
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--map", default=None, help="Override mappa")
    args = parser.parse_args()

    print("\n=== AVVIO SCENARIO ===")
    print(f"Scenario: {args.scenario}")
    print(f"Apollo Bridge: {args.bridge}:{args.port}")

    # ------------------------------------------------------------
    #   CARICA LO SCENARIO JSON
    # ------------------------------------------------------------
    with open(args.scenario, "r") as f:
        data = json.load(f)

    agents = data.get("agents", [])

    # MAPPA SELEZIONATA
    map_name = args.map or data.get("map", "BorregasAve").replace(" ", "")
    if map_name not in MAP_IDS:
        print(f"[WARN] Mappa '{map_name}' sconosciuta. Uso BorregasAve.")
        map_name = "BorregasAve"

    print(f"[INFO] Mappa scenario: {map_name}")

    # ------------------------------------------------------------
    #   CONNESSIONE SIMULATORE
    # ------------------------------------------------------------
    sim = lgsvl.Simulator("127.0.0.1", 8181)

    # Carica la mappa giusta
    print(f"[INFO] Caricamento mappa '{map_name}'...")
    scene_id = MAP_IDS[map_name]

    if sim.current_scene == scene_id:
        sim.reset()
    else:
        sim.load(scene_id)

    # Spawn points
    spawns = sim.get_spawn()
    used_spawn = sim.map_point_on_lane(spawns[0].position)

    # ------------------------------------------------------------
    #   EGO
    # ------------------------------------------------------------
    ego_agent = next((a for a in agents if a["type"].upper() == "EGO"), None)
    if not ego_agent:
        raise RuntimeError("❌ Nessun agente EGO nello scenario!")

    ego, used_model = spawn_ego(sim, used_spawn, args)

    # ------------------------------------------------------------
    #   DREAMVIEW (Apollo)
    # ------------------------------------------------------------
    print("[INFO] Connessione Bridge Apollo…")
    ego.connect_bridge(args.bridge, args.port)

    print("[INFO] Setup Dreamview…")
    dv = lgsvl.dreamview.Connection(sim, ego, args.bridge)

    dv.set_hd_map(map_name)
    dv.set_vehicle(used_model)

    ego_state = ego.state
    px = ego_state.transform.position.x
    py = ego_state.transform.position.z

    dv.update_localization(ego_state.transform)

    modules = [
        "Localization", "Transform", "Perception",
        "Prediction", "Planning", "Routing", "Control"
    ]
    dv.setup_apollo(px, py, modules)

    print("[INFO] Attesa inizializzazione Apollo…")
    time.sleep(3)

    # ------------------------------------------------------------
    #   NPC
    # ------------------------------------------------------------
    npc_agents = [a for a in agents if a["type"].upper() == "NPC"]
    print(f"[INFO] Spawn NPC: {len(npc_agents)}")

    for npc_data in npc_agents:
        npc_state = lgsvl.AgentState()
        pos = lgsvl.Vector(
            npc_data["spawn"]["x"],
            npc_data["spawn"].get("z", 0.0),
            npc_data["spawn"]["y"]
        )
        npc_state.transform.position = sim.map_point_on_lane(pos).position
        npc_state.transform.rotation.y = npc_data["spawn"].get("yaw", 0.0)

        try:
            npc = sim.add_agent(npc_data["vehicleModel"], lgsvl.AgentType.NPC, npc_state)
        except Exception as e:
            print(f"[WARN] NPC {npc_data['id']} non spawnato: {e}")
            continue

    # ------------------------------------------------------------
    #   RUN SIM
    # ------------------------------------------------------------
    print("[INFO] Sync orario simulatore…")
    sim.reset_time()
    sim.set_time_of_day(time.localtime().tm_hour + time.localtime().tm_min/60)

    print(f"[INFO] RUN SIM {args.duration}s…")
    sim.run(3)

    start = time.time()
    while time.time() - start < args.duration:
        sim.run(0.5)

    print("[INFO] Simulazione conclusa.\n")


if __name__ == "__main__":
    main()
