import json, csv, os, sys, math
from ruamel.yaml import YAML

yaml = YAML()

def read_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.load(f)

def write_yaml(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)

def read_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def write_csv(rows, header, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)
