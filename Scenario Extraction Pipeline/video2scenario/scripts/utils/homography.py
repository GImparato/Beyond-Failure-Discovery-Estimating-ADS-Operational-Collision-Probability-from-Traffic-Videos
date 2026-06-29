import numpy as np
import cv2

def compute_homography(img_pts, world_rect_w, world_rect_h):
    # img_pts: list of 4 points (clockwise) on the ground plane
    # world points: rectangle (0,0) -> (W,0) -> (W,H) -> (0,H)
    W, H = float(world_rect_w), float(world_rect_h)
    src = np.array(img_pts, dtype=np.float32)
    dst = np.array([[0,0],[W,0],[W,H],[0,H]], dtype=np.float32)
    Hmat = cv2.getPerspectiveTransform(src, dst)
    return Hmat

def save_homography(path, H, meta=None):
    if meta is None: meta = {}
    np.savez_compressed(path, H=H, meta=meta)

def load_homography(path):
    data = np.load(path, allow_pickle=True)
    return data["H"], data.get("meta", {})
