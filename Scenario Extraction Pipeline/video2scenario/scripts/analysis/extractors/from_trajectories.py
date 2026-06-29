import json

def load_trajectories(path):
    with open(path, "r") as f:
        return json.load(f)
