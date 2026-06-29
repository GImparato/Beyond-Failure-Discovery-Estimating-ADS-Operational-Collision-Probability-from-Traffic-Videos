import numpy as np

def to_homogeneous(points_xy):
    points_xy = np.asarray(points_xy, dtype=np.float32)
    if points_xy.ndim == 1:
        points_xy = points_xy[None, :]
    ones = np.ones((points_xy.shape[0], 1), dtype=np.float32)
    return np.concatenate([points_xy, ones], axis=1)

def apply_homography(H, points_xy):
    pts_h = to_homogeneous(points_xy) @ H.T
    pts = (pts_h[:, :2] / pts_h[:, 2:3]).astype(np.float32)
    return pts

def bbox_bottom_center(x1, y1, x2, y2):
    return ( (x1 + x2) / 2.0, y2 )
