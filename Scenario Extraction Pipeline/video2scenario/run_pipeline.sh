#!/usr/bin/env bash
set -e

VIDEO="$1"
if [ -z "$VIDEO" ]; then
  echo "Usage: $0 path/to/video.mp4"
  exit 1
fi

mkdir -p data outputs

python3 scripts/01_select_homography_points.py --video "$VIDEO" --rect_w 3.5 --rect_h 10.0 --out data/homography.npz

python3 scripts/02_track_yolov8.py --video "$VIDEO" --out outputs/tracks.csv --model yolov8n.pt --imgsz 960 --conf 0.25

python3 scripts/03_build_trajectories.py --video "$VIDEO" --tracks outputs/tracks.csv --homography data/homography.npz --out outputs/trajectories.json

python3 scripts/04_export_openx.py --trajectories outputs/trajectories.json --out outputs/scenario.xosc --title "video2scenario"

python3 scripts/05_export_svl.py --trajectories outputs/trajectories.json --out outputs/scenario_svl.json --title "video2scenario" --map "BorregasAve" --time-of-day noon