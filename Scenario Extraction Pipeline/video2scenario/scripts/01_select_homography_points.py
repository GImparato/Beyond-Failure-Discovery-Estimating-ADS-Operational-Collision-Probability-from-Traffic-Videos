import argparse, cv2, os
import numpy as np
from utils.homography import compute_homography, save_homography

def parse_args():
    ap = argparse.ArgumentParser(description="Seleziona 4 punti (rettangolo) per omografia")
    ap.add_argument("--video", required=True)
    ap.add_argument("--rect_w", type=float, required=True, help="larghezza rettangolo reale (m)")
    ap.add_argument("--rect_h", type=float, required=True, help="altezza rettangolo reale (m)")
    ap.add_argument("--out", default="data/homography.npz")
    return ap.parse_args()

def main():
    args = parse_args()
    cap = cv2.VideoCapture(args.video)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("Impossibile leggere il primo frame dal video")

    clone = frame.copy()
    pts = []

    def on_mouse(event, x, y, flags, param):
        nonlocal pts, frame
        if event == cv2.EVENT_LBUTTONDOWN:
            pts.append((x, y))

    cv2.namedWindow("Seleziona 4 punti (ordine orario)")
    cv2.setMouseCallback("Seleziona 4 punti (ordine orario)", on_mouse)

    while True:
        vis = clone.copy()
        for i, p in enumerate(pts):
            cv2.circle(vis, p, 5, (0,255,0), -1)
            cv2.putText(vis, str(i+1), (p[0]+6, p[1]-6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        cv2.imshow("Seleziona 4 punti (ordine orario)", vis)
        key = cv2.waitKey(20) & 0xFF
        if key == 27:  # ESC
            break
        if len(pts) == 4:
            break
    cv2.destroyAllWindows()

    if len(pts) != 4:
        raise RuntimeError("Selezione annullata o incompleta. Servono 4 punti.")

    H = compute_homography(pts, args.rect_w, args.rect_h)
    meta = {"video": args.video, "rect_w": args.rect_w, "rect_h": args.rect_h, "points": pts}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    save_homography(args.out, H, meta=meta)
    print(f"[OK] Omografia salvata in {args.out}")

if __name__ == "__main__":
    main()
