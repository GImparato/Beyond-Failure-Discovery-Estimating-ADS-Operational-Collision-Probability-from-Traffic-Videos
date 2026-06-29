import argparse, os
import cv2, numpy as np
from collections import defaultdict
from scipy.signal import savgol_filter
from utils.io_utils import write_json
from utils.homography import load_homography
from utils.geometry import bbox_bottom_center, apply_homography

# ============================================================
# STEP 1 — EGO SPEED (pixel-based)
# ============================================================

def estimate_ego_speed_from_video(video_path, detections_by_frame):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    ret, prev = cap.read()
    if not ret:
        cap.release()
        return None

    prev_gray = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
    speeds = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )

        mag = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)

        mask = np.ones(mag.shape, dtype=bool)
        for (x1, y1, x2, y2) in detections_by_frame.get(frame_idx, []):
            mask[int(y1):int(y2), int(x1):int(x2)] = False

        bg_mag = mag[mask]
        if bg_mag.size > 0:
            speeds.append(bg_mag.mean())

        prev_gray = gray
        frame_idx += 1

    cap.release()

    if not speeds:
        return None

    return {
        "ego_avg_speed_px_frame": float(np.mean(speeds)),
        "ego_max_speed_px_frame": float(np.max(speeds)),
        "ego_avg_speed_px_s": float(np.mean(speeds) * fps),
        "ego_max_speed_px_s": float(np.max(speeds) * fps),
    }

# ============================================================
# STEP 2 — DTO per agente (pixel)
# ============================================================

def compute_agent_dto(centers_px, frames, ego_point_px):
    min_d, min_f = float("inf"), None
    for (x, y), f in zip(centers_px, frames):
        d = np.hypot(x - ego_point_px[0], y - ego_point_px[1])
        if d < min_d:
            min_d, min_f = d, f
    return (float(min_d), int(min_f)) if min_f is not None else (None, None)

# ============================================================
# STEP 3 — TTC per agente (frame + secondi)
# ============================================================

def compute_agent_ttc(frames, dto_frame, fps):
    if dto_frame is None:
        return None, None
    ttc_f = max(0, dto_frame - frames[0])
    return int(ttc_f), float(ttc_f / fps)

# ============================================================
# STEP 4 — Pedestrians veri
# ============================================================

def is_pedestrian(class_name):
    return (class_name or "").lower() in ["person", "pedestrian"]

# ============================================================
# STEP 5 — Collisioni visive
# ============================================================

def detect_collision(frames, bboxes, dto_frame, W, H):
    if dto_frame is None:
        return False, None

    roi_x1, roi_x2 = 0.4 * W, 0.6 * W
    roi_y1, roi_y2 = 0.6 * H, 0.9 * H

    areas = []
    for f, (x1, y1, x2, y2) in zip(frames, bboxes):
        cx, cy = (x1+x2)/2, (y1+y2)/2
        area = (x2-x1)*(y2-y1)
        areas.append(area)

        if roi_x1 <= cx <= roi_x2 and roi_y1 <= cy <= roi_y2 and f >= dto_frame:
            growth = area / max(1.0, np.mean(areas[:3]))
            if growth > 1.5:
                return True, int(f)

    return False, None

# ============================================================

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--tracks", required=True)
    ap.add_argument("--homography", required=True)
    ap.add_argument("--out", default="outputs/trajectories.json")
    ap.add_argument("--savgol_window", type=int, default=9)
    ap.add_argument("--savgol_poly", type=int, default=2)
    ap.add_argument("--min_len", type=int, default=3)
    return ap.parse_args()

def read_tracks_csv(path):
    import csv
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def smooth(arr, win, poly):
    arr = np.asarray(arr, dtype=np.float32)
    if win < 3 or len(arr) < 3:
        return arr
    if win % 2 == 0:
        win += 1
    win = min(win, len(arr) - (1 - len(arr) % 2))
    if win < 3:
        return arr
    return savgol_filter(arr, win, min(poly, 3))

def main():
    args = parse_args()

    cap = cv2.VideoCapture(args.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    ego_point_px = (W / 2.0, H * 0.9)

    Hmat, meta = load_homography(args.homography)
    rows = read_tracks_csv(args.tracks)

    tracks = defaultdict(list)
    detections_by_frame = defaultdict(list)

    for r in rows:
        fid = int(float(r["frame"]))
        tid = int(float(r["track_id"]))
        cname = r["class"]
        x1, y1, x2, y2 = map(float, (r["x1"], r["y1"], r["x2"], r["y2"]))
        tracks[tid].append((fid, cname, x1, y1, x2, y2))
        detections_by_frame[fid].append((x1, y1, x2, y2))

    ego_motion = estimate_ego_speed_from_video(args.video, detections_by_frame)

    agents = []
    collision_ids = set()
    pedestrian_ids = set()

    for tid, dets in tracks.items():
        dets.sort(key=lambda z: z[0])
        if len(dets) < args.min_len:
            continue

        frames = [d[0] for d in dets]
        classes = [d[1] for d in dets]
        centers_px = [bbox_bottom_center(d[2], d[3], d[4], d[5]) for d in dets]
        bboxes = [(d[2], d[3], d[4], d[5]) for d in dets]

        cname_mode = max(set(classes), key=classes.count)

        if is_pedestrian(cname_mode):
            pedestrian_ids.add(tid)

        dto_px, dto_frame = compute_agent_dto(centers_px, frames, ego_point_px)
        ttc_frame, ttc_seconds = compute_agent_ttc(frames, dto_frame, fps)
        has_col, col_frame = detect_collision(frames, bboxes, dto_frame, W, H)

        if has_col:
            collision_ids.add(tid)

        img_xy = np.array(centers_px, dtype=np.float32)
        world_xy = apply_homography(Hmat, img_xy)
        t = np.array(frames) / fps

        x = smooth(world_xy[:, 0], args.savgol_window, args.savgol_poly)
        y = smooth(world_xy[:, 1], args.savgol_window, args.savgol_poly)

        traj = [{"t": float(t[i]), "x": float(x[i]), "y": float(y[i])} for i in range(len(t))]

        agents.append({
            "id": int(tid),
            "class": cname_mode,
            "is_pedestrian": is_pedestrian(cname_mode),
            "dto_px": dto_px,
            "dto_frame": dto_frame,
            "ttc_frame": ttc_frame,
            "ttc_seconds": ttc_seconds,
            "has_collision": has_col,
            "collision_frame": col_frame,
            "trajectory": traj
        })

    out = {
        "video": args.video,
        "fps": float(fps),
        "ego_motion": ego_motion,
        "ego_point_px": {"x": ego_point_px[0], "y": ego_point_px[1]},
        "has_collision": len(collision_ids) > 0,
        "collision_agents": list(collision_ids),
        "has_pedestrians": len(pedestrian_ids) > 0,
        "num_pedestrians": len(pedestrian_ids),
        "homography_meta": meta.item() if hasattr(meta, "item") else meta,
        "agents": agents
    }

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    write_json(out, args.out)

    print(f"[OK] Trajectories written to {args.out}")

if __name__ == "__main__":
    main()
